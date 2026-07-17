"""Passwordless authentication, revocable sessions, and employee accounts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.rbac import can_manage_target
from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import (
    generate_login_code,
    generate_session_token,
    hash_login_code,
    hash_session_token,
    keyed_hash,
    verify_login_code_hash,
)
from app.models.enums import AccountStatus, NotificationEventType, Role
from app.models.tables import AuditEvent, AuthSession, LoginCode, User
from app.services.email_service import (
    send_invitation_email,
    send_login_code,
    send_role_notification,
    send_status_notification,
)
from app.services.notification_service import create_notification


LOGIN_REQUEST_MESSAGE = "If the account can sign in, a confirmation code has been sent."
LOGIN_ERROR_MESSAGE = "The confirmation code is invalid or has expired."
SHARED_EMAIL_LOCAL_PARTS = frozenset(
    {
        "accounts", "admin", "billing", "claims", "contact", "finance", "hello", "help", "hr", "info",
        "inbox", "marketing", "notifications", "noreply", "no-reply", "operations", "quotes", "sales",
        "support", "team",
    }
)

_SIGNABLE_STATUSES = frozenset({AccountStatus.ACTIVE.value, AccountStatus.INVITED.value})


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_employee_email(email: str) -> str:
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise AppError("Enter a valid named employee email address.")
    local_part, domain = normalized.split("@", 1)
    if (
        domain != "risklocker.com"
        or not re.fullmatch(r"[a-z0-9][a-z0-9._%+\-]*", local_part)
        or local_part in SHARED_EMAIL_LOCAL_PARTS
    ):
        raise AppError("Only named Risklocker employee email addresses are allowed.")
    if any(character.isspace() for character in normalized):
        raise AppError("Enter a valid named employee email address.")
    return normalized


def _audit(db: Session, action: str, user_id: str | None, entity_id: str | None = None, details: dict | None = None) -> None:
    db.add(AuditEvent(actor_id=user_id, action=action, entity_type="authentication", entity_id=entity_id, details=details or {}))


def _email_hash(email: str, settings: Settings) -> str:
    return keyed_hash(f"login-email:{email}", settings.auth_hash_secret)


def request_login_code(
    db: Session,
    settings: Settings,
    email: str,
    sender: Callable[[Settings, str, str], None] = send_login_code,
) -> str:
    try:
        normalized = normalize_employee_email(email)
    except AppError:
        return LOGIN_REQUEST_MESSAGE

    user = db.scalar(select(User).where(User.email == normalized))
    if not user or user.status not in _SIGNABLE_STATUSES:
        return LOGIN_REQUEST_MESSAGE

    now = utcnow()
    email_hash = _email_hash(normalized, settings)
    latest = db.scalar(
        select(LoginCode).where(LoginCode.email_hash == email_hash).order_by(LoginCode.created_at.desc()).with_for_update()
    )
    if latest and latest.consumed_at is None and latest.resend_available_at > now:
        _audit(db, "auth.code.throttled", user.id, user.id)
        db.commit()
        return LOGIN_REQUEST_MESSAGE

    if latest and latest.consumed_at is None:
        latest.consumed_at = now

    code = generate_login_code()
    challenge = LoginCode(
        user_id=user.id,
        email_hash=email_hash,
        code_hash="pending",
        max_attempts=settings.auth_code_max_attempts,
        expires_at=now + timedelta(minutes=settings.auth_code_expire_minutes),
        resend_available_at=now + timedelta(seconds=settings.auth_code_resend_seconds),
    )
    db.add(challenge)
    db.flush()
    challenge.code_hash = hash_login_code(challenge.id, code, settings.auth_hash_secret)
    try:
        sender(settings, normalized, code)
    except Exception:
        challenge.consumed_at = now
        _audit(db, "auth.code.delivery_failed", user.id, user.id)
        db.commit()
        return LOGIN_REQUEST_MESSAGE
    _audit(db, "auth.code.sent", user.id, user.id, {"expires_at": challenge.expires_at.isoformat()})
    db.commit()
    return LOGIN_REQUEST_MESSAGE


def create_session(
    db: Session,
    settings: Settings,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
    now: datetime | None = None,
) -> tuple[AuthSession, str]:
    issued_at = now or utcnow()
    raw_token = generate_session_token()
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        last_activity_at=issued_at,
        idle_expires_at=issued_at + timedelta(hours=settings.session_idle_hours),
        absolute_expires_at=issued_at + timedelta(days=settings.session_max_days),
        user_agent=(user_agent or "")[:500] or None,
        ip_address=(ip_address or "")[:64] or None,
    )
    db.add(session)
    db.flush()
    return session, raw_token


def verify_code_and_create_session(
    db: Session,
    settings: Settings,
    email: str,
    code: str,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[User, AuthSession, str]:
    try:
        normalized = normalize_employee_email(email)
    except AppError:
        raise AppError(LOGIN_ERROR_MESSAGE, 401) from None
    email_hash = _email_hash(normalized, settings)
    challenge = db.scalar(
        select(LoginCode).where(LoginCode.email_hash == email_hash).order_by(LoginCode.created_at.desc()).with_for_update()
    )
    now = utcnow()
    if not challenge or challenge.consumed_at is not None:
        raise AppError(LOGIN_ERROR_MESSAGE, 401)
    if challenge.expires_at <= now or challenge.attempt_count >= challenge.max_attempts:
        challenge.consumed_at = now
        _audit(db, "auth.code.expired", challenge.user_id, challenge.user_id)
        db.commit()
        raise AppError(LOGIN_ERROR_MESSAGE, 401)
    if not verify_login_code_hash(challenge.id, code, challenge.code_hash, settings.auth_hash_secret):
        challenge.attempt_count += 1
        if challenge.attempt_count >= challenge.max_attempts:
            challenge.consumed_at = now
        _audit(db, "auth.code.rejected", challenge.user_id, challenge.user_id, {"attempt": challenge.attempt_count})
        db.commit()
        raise AppError(LOGIN_ERROR_MESSAGE, 401)

    user = db.get(User, challenge.user_id)
    if not user or user.email != normalized or user.status not in _SIGNABLE_STATUSES:
        challenge.consumed_at = now
        db.commit()
        raise AppError(LOGIN_ERROR_MESSAGE, 401)
    challenge.consumed_at = now
    was_invited = user.status == AccountStatus.INVITED.value
    if was_invited:
        user.status = AccountStatus.ACTIVE.value
    session, raw_token = create_session(
        db, settings, user, user_agent=user_agent, ip_address=ip_address, now=now
    )
    _audit(db, "auth.session.created", user.id, session.id, {"promoted_from_invited": was_invited})
    db.commit()
    db.refresh(session)
    return user, session, raw_token


def authenticate_session(
    db: Session,
    settings: Settings,
    raw_token: str,
    *,
    now: datetime | None = None,
    touch: bool = True,
) -> tuple[User, AuthSession]:
    checked_at = now or utcnow()
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_session_token(raw_token)))
    if not session or session.revoked_at is not None:
        raise AppError("Please log in again.", 401)
    if session.idle_expires_at <= checked_at or session.absolute_expires_at <= checked_at:
        session.revoked_at = checked_at
        _audit(db, "auth.session.expired", session.user_id, session.id)
        db.commit()
        raise AppError("Your session has expired. Please log in again.", 401)
    user = db.get(User, session.user_id)
    if not user or user.status not in _SIGNABLE_STATUSES:
        session.revoked_at = checked_at
        db.commit()
        raise AppError("Your account is not active. Please contact an Admin.", 401)
    try:
        normalized = normalize_employee_email(user.email)
    except AppError:
        session.revoked_at = checked_at
        db.commit()
        raise AppError("Please log in again.", 401) from None
    if normalized != user.email:
        session.revoked_at = checked_at
        db.commit()
        raise AppError("Please log in again.", 401)
    if touch:
        session.last_activity_at = checked_at
        session.idle_expires_at = min(
            checked_at + timedelta(hours=settings.session_idle_hours), session.absolute_expires_at
        )
        db.commit()
    return user, session


def revoke_session(db: Session, session: AuthSession, actor_id: str | None) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        session.revoked_by = actor_id
        _audit(db, "auth.session.revoked", actor_id, session.id, {"user_id": session.user_id})
        db.commit()


def revoke_user_sessions(db: Session, user_id: str, actor_id: str | None) -> int:
    sessions = list(
        db.scalars(select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))).all()
    )
    now = utcnow()
    for session in sessions:
        session.revoked_at = now
        session.revoked_by = actor_id
    _audit(db, "auth.sessions.revoked", actor_id, user_id, {"user_id": user_id, "count": len(sessions)})
    db.commit()
    return len(sessions)


def create_user(db: Session, actor: User, email: str, role: str) -> User:
    normalized = normalize_employee_email(email)
    if role not in {Role.STAFF.value, Role.MANAGER.value, Role.ADMIN.value}:
        raise AppError("Choose a valid role.")
    if not can_manage_target(actor, role):
        raise AppError("You do not have permission to manage this role.", 403)
    if db.scalar(select(User).where(User.email == normalized)):
        raise AppError("A user with this email already exists.")
    user = User(email=normalized, role=role, status=AccountStatus.INVITED.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def invite_user(
    db: Session,
    settings: Settings,
    actor: User,
    email: str,
    role: str,
    sender: Callable[[Settings, str, str], None] = send_invitation_email,
) -> User:
    user = create_user(db, actor, email, role)
    now = utcnow()
    code = generate_login_code()
    email_hash = _email_hash(user.email, settings)
    challenge = LoginCode(
        user_id=user.id,
        email_hash=email_hash,
        code_hash="pending",
        max_attempts=settings.auth_code_max_attempts,
        expires_at=now + timedelta(minutes=settings.auth_code_expire_minutes),
        resend_available_at=now + timedelta(seconds=settings.auth_code_resend_seconds),
    )
    db.add(challenge)
    db.flush()
    challenge.code_hash = hash_login_code(challenge.id, code, settings.auth_hash_secret)
    delivery_state = "sent"
    delivery_error = None
    try:
        sender(settings, user.email, code)
    except Exception as exc:
        delivery_state = "failed"
        delivery_error = str(exc)
        challenge.consumed_at = now
    _audit(db, "auth.invitation.sent" if delivery_state == "sent" else "auth.invitation.failed", actor.id, user.id)
    create_notification(
        db,
        recipient_id=user.id,
        event_type=NotificationEventType.INVITATION.value,
        title="Account Invitation",
        body=f"Your Risklocker account has been created with the {role} role. Check your email for your sign-in code.",
        delivery_state=delivery_state,
        delivery_error=delivery_error,
    )
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, actor: User, target: User, *, email: str | None, role: str | None, status: str | None) -> User:
    if actor.role == Role.MANAGER.value and target.role != Role.STAFF.value:
        raise AppError("Managers can manage Staff only.", 403)
    email_changed = False
    role_changed = False
    status_changed = False
    if email is not None:
        normalized = normalize_employee_email(email)
        duplicate = db.scalar(select(User).where(User.email == normalized, User.id != target.id))
        if duplicate:
            raise AppError("A user with this email already exists.")
        email_changed = normalized != target.email
        target.email = normalized
    if role is not None:
        if role not in {item.value for item in Role} or not can_manage_target(actor, role):
            raise AppError("You do not have permission to manage this role.", 403)
        role_changed = role != target.role
        target.role = role
    if status is not None:
        if status not in {AccountStatus.ACTIVE.value, AccountStatus.INACTIVE.value}:
            raise AppError("Choose a valid account status.")
        status_changed = status != target.status
        target.status = status
    db.commit()
    db.refresh(target)
    if status == AccountStatus.INACTIVE.value or email_changed:
        revoke_user_sessions(db, target.id, actor.id)
    return target


def notify_role_change(db: Session, settings: Settings, actor: User, target: User, new_role: str) -> None:
    try:
        send_role_notification(settings, target.email, new_role)
        delivery_state = "sent"
        delivery_error = None
    except Exception as exc:
        delivery_state = "failed"
        delivery_error = str(exc)
    create_notification(
        db,
        recipient_id=target.id,
        event_type=NotificationEventType.ROLE_CHANGE.value,
        title="Role Updated",
        body=f"Your account role has been changed to {new_role}.",
        delivery_state=delivery_state,
        delivery_error=delivery_error,
    )


def notify_status_change(db: Session, settings: Settings, actor: User, target: User, new_status: str) -> None:
    try:
        send_status_notification(settings, target.email, new_status)
        delivery_state = "sent"
        delivery_error = None
    except Exception as exc:
        delivery_state = "failed"
        delivery_error = str(exc)
    create_notification(
        db,
        recipient_id=target.id,
        event_type=NotificationEventType.STATUS_CHANGE.value,
        title="Account Status Changed",
        body=f"Your account is now {new_status}." if new_status == "active" else "Your account has been deactivated.",
        delivery_state=delivery_state,
        delivery_error=delivery_error,
    )


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
    }
