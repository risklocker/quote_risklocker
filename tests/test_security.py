from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.errors import AppError
from app.core.security import hash_login_code, hash_session_token, verify_login_code_hash
from app.models.tables import AuthSession, LoginCode, User
from app.services.auth_service import (
    LOGIN_REQUEST_MESSAGE,
    authenticate_session,
    create_session,
    create_user,
    normalize_employee_email,
    request_login_code,
    revoke_session,
    update_user,
    verify_code_and_create_session,
)


def settings(**overrides):
    values = {
        "auth_hash_secret": "test-auth-hash-secret-that-is-long-enough",
        "auth_code_expire_minutes": 10,
        "auth_code_max_attempts": 3,
        "auth_code_resend_seconds": 60,
        "session_idle_hours": 8,
        "session_max_days": 30,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ScalarRows:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeSession:
    def __init__(self, scalar_values=None, objects=None, rows=None):
        self.scalar_values = list(scalar_values or [])
        self.objects = objects or {}
        self.rows = list(rows or [])
        self.added = []
        self.commits = 0

    def scalar(self, _statement):
        return self.scalar_values.pop(0) if self.scalar_values else None

    def scalars(self, _statement):
        return ScalarRows(self.rows)

    def get(self, _model, object_id):
        return self.objects.get(object_id)

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = str(uuid4())
        if hasattr(value, "created_at") and getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)
        self.added.append(value)

    def flush(self):
        return None

    def commit(self):
        self.commits += 1

    def refresh(self, _value):
        return None


@pytest.mark.parametrize(
    ("source", "expected"),
    [(" Person.Name@Risklocker.com ", "person.name@risklocker.com"), ("person+test@risklocker.com", "person+test@risklocker.com")],
)
def test_employee_email_domain_is_normalized_and_allowed(source, expected):
    assert normalize_employee_email(source) == expected


@pytest.mark.parametrize(
    "email",
    [
        "person@example.com", "person@sub.risklocker.com", "person@risklocker.com.evil", "admin@risklocker.com",
        "team@risklocker.com", "person name@risklocker.com", "person!name@risklocker.com",
    ],
)
def test_external_and_shared_addresses_are_rejected(email):
    with pytest.raises(AppError):
        normalize_employee_email(email)


def test_login_code_hash_round_trip_does_not_store_plain_code():
    digest = hash_login_code("challenge-1", "123456", settings().auth_hash_secret)
    assert "123456" not in digest
    assert verify_login_code_hash("challenge-1", "123456", digest, settings().auth_hash_secret)
    assert not verify_login_code_hash("challenge-1", "654321", digest, settings().auth_hash_secret)


def test_request_response_is_non_enumerating_for_unknown_domain():
    db = FakeSession()
    assert request_login_code(db, settings(), "outsider@example.com") == LOGIN_REQUEST_MESSAGE
    assert not db.added


def test_employee_domain_policy_is_enforced_on_account_create_and_update():
    now = datetime.now(timezone.utc)
    admin = User(id=str(uuid4()), email="owner.name@risklocker.com", role="Admin", status="active", created_at=now, updated_at=now)
    create_db = FakeSession(scalar_values=[None])
    created = create_user(create_db, admin, "new.person@risklocker.com", "Staff")
    assert created.email == "new.person@risklocker.com"

    with pytest.raises(AppError, match="Only named Risklocker"):
        create_user(FakeSession(), admin, "new.person@example.com", "Staff")
    with pytest.raises(AppError, match="Only named Risklocker"):
        update_user(FakeSession(), admin, created, email="team@risklocker.com", role=None, status=None)


def test_request_code_sends_through_injected_relay_and_throttles_resend():
    user = User(id=str(uuid4()), email="person.name@risklocker.com", role="Staff", status="active")
    delivered = []
    first_db = FakeSession(scalar_values=[user, None])

    request_login_code(first_db, settings(), user.email, sender=lambda _settings, recipient, code: delivered.append((recipient, code)))

    challenge = next(item for item in first_db.added if isinstance(item, LoginCode))
    assert delivered[0][0] == user.email
    assert len(delivered[0][1]) == 6
    assert challenge.code_hash != delivered[0][1]

    throttled_db = FakeSession(scalar_values=[user, challenge])
    request_login_code(throttled_db, settings(), user.email, sender=lambda *_args: pytest.fail("resend should be throttled"))
    assert any(getattr(item, "action", "") == "auth.code.throttled" for item in throttled_db.added)


def test_code_expiry_and_attempt_limit_are_enforced():
    now = datetime.now(timezone.utc)
    user = User(id=str(uuid4()), email="person.name@risklocker.com", role="Staff", status="active")
    expired = LoginCode(
        id=str(uuid4()), user_id=user.id, email_hash="hash", code_hash="hash", attempt_count=0, max_attempts=3,
        expires_at=now - timedelta(seconds=1), resend_available_at=now, consumed_at=None,
    )
    db = FakeSession(scalar_values=[expired], objects={user.id: user})
    with pytest.raises(AppError, match="invalid or has expired"):
        verify_code_and_create_session(db, settings(), user.email, "123456")
    assert expired.consumed_at is not None

    challenge = LoginCode(
        id=str(uuid4()), user_id=user.id,
        email_hash="hash", code_hash=hash_login_code("challenge", "123456", settings().auth_hash_secret),
        attempt_count=2, max_attempts=3, expires_at=now + timedelta(minutes=5), resend_available_at=now, consumed_at=None,
    )
    challenge.id = "challenge"
    db = FakeSession(scalar_values=[challenge], objects={user.id: user})
    with pytest.raises(AppError):
        verify_code_and_create_session(db, settings(), user.email, "000000")
    assert challenge.attempt_count == 3
    assert challenge.consumed_at is not None


def test_valid_code_creates_one_time_server_session():
    user = User(id=str(uuid4()), email="person.name@risklocker.com", role="Staff", status="active")
    now = datetime.now(timezone.utc)
    challenge = LoginCode(
        id="challenge", user_id=user.id, email_hash="unused",
        code_hash=hash_login_code("challenge", "123456", settings().auth_hash_secret),
        attempt_count=0, max_attempts=3, expires_at=now + timedelta(minutes=5), resend_available_at=now, consumed_at=None,
    )
    db = FakeSession(scalar_values=[challenge], objects={user.id: user})
    authenticated_user, session, raw_token = verify_code_and_create_session(db, settings(), user.email, "123456")
    assert authenticated_user is user
    assert challenge.consumed_at is not None
    assert session.token_hash == hash_session_token(raw_token)
    assert raw_token not in session.token_hash


def test_eight_hour_window_rolls_on_activity_and_then_expires():
    user = User(id=str(uuid4()), email="person.name@risklocker.com", role="Staff", status="active")
    issued = datetime.now(timezone.utc)
    create_db = FakeSession()
    session, raw_token = create_session(create_db, settings(), user, now=issued)
    active_at = issued + timedelta(hours=7)
    auth_db = FakeSession(scalar_values=[session], objects={user.id: user})
    authenticate_session(auth_db, settings(), raw_token, now=active_at)
    assert session.last_activity_at == active_at
    assert session.idle_expires_at == active_at + timedelta(hours=8)

    expired_db = FakeSession(scalar_values=[session], objects={user.id: user})
    with pytest.raises(AppError, match="expired"):
        authenticate_session(expired_db, settings(), raw_token, now=session.idle_expires_at + timedelta(seconds=1))
    assert session.revoked_at is not None


def test_session_has_hard_thirty_day_limit_and_revocation_is_immediate():
    user = User(id=str(uuid4()), email="person.name@risklocker.com", role="Staff", status="active")
    issued = datetime.now(timezone.utc)
    db = FakeSession()
    session, raw_token = create_session(db, settings(), user, now=issued)
    session.idle_expires_at = session.absolute_expires_at
    expired_db = FakeSession(scalar_values=[session], objects={user.id: user})
    with pytest.raises(AppError, match="expired"):
        authenticate_session(expired_db, settings(), raw_token, now=issued + timedelta(days=30, seconds=1))

    session.revoked_at = None
    revoke_session(db, session, user.id)
    revoked_db = FakeSession(scalar_values=[session], objects={user.id: user})
    with pytest.raises(AppError, match="log in again"):
        authenticate_session(revoked_db, settings(), raw_token, now=issued + timedelta(hours=1))


def test_disabled_account_cannot_use_existing_session():
    user = User(id=str(uuid4()), email="person.name@risklocker.com", role="Staff", status="inactive")
    issued = datetime.now(timezone.utc)
    db = FakeSession()
    session, raw_token = create_session(db, settings(), user, now=issued)
    auth_db = FakeSession(scalar_values=[session], objects={user.id: user})
    with pytest.raises(AppError, match="not active"):
        authenticate_session(auth_db, settings(), raw_token, now=issued + timedelta(minutes=1))
    assert session.revoked_at is not None


def test_frontend_does_not_store_authentication_tokens_in_browser_storage():
    api_source = (ROOT / "frontend" / "src" / "lib" / "api.ts").read_text(encoding="utf-8")
    login_source = (ROOT / "frontend" / "src" / "app" / "login" / "page.tsx").read_text(encoding="utf-8")
    combined = api_source + login_source
    assert "risklocker_token" not in combined
    assert "Authorization" not in combined
    assert "Bearer " not in combined
    assert "localStorage" not in combined
    assert "sessionStorage" not in combined
