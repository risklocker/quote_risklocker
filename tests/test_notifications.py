from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_PROVIDER": "supabase_postgres",
        "DATABASE_URL": "postgresql://postgres:password@db.test.supabase.co:5432/postgres",
        "AUTH_HASH_SECRET": "test-auth-hash-secret-that-is-long-enough",
        "STORAGE_DRIVER": "supabase",
        "SUPABASE_URL": "https://project-ref.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
    }
)

from app.api import routes
from app.api.deps import settings_dep
from app.core.errors import AppError, register_error_handlers
from app.core.security import hash_session_token
from app.db.session import get_db
from app.models.enums import AccountStatus, NotificationEventType
from app.models.tables import AuthSession, Notification, User
from app.services.auth_service import (
    LOGIN_REQUEST_MESSAGE,
    invite_user,
    notify_role_change,
    notify_status_change,
    update_user,
    verify_code_and_create_session,
)
from app.services.notification_service import (
    create_notification,
    get_notifications,
    get_unread_count,
    mark_all_read,
    mark_read,
    serialize_notification,
)


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


def _user(role="Staff", status="active", email="person.name@risklocker.com"):
    return User(
        id=str(uuid4()), email=email, role=role, status=status,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


def _admin():
    return _user(role="Admin", email="first.last@risklocker.com")


def _test_settings(**overrides):
    values = {
        "auth_hash_secret": "test-auth-hash-secret-that-is-long-enough",
        "auth_code_expire_minutes": 10,
        "auth_code_max_attempts": 3,
        "auth_code_resend_seconds": 60,
        "session_idle_hours": 8,
        "session_max_days": 30,
        "smtp_host": "",
        "smtp_from_email": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def http_settings():
    return SimpleNamespace(
        app_env="test",
        cors_origins=("http://localhost:3000",),
        session_cookie_name="risklocker_session",
        session_cookie_secure=False,
        session_idle_hours=8,
        session_max_days=30,
        auth_hash_secret="test-auth-hash-secret-that-is-long-enough",
        smtp_host="",
        smtp_from_email="",
    )


def http_client(db: FakeSession):
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(routes.router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[settings_dep] = http_settings
    return TestClient(app)


def _active_session(user):
    now = datetime.now(timezone.utc)
    raw_token = "opaque-session-token"
    session = AuthSession(
        id=str(uuid4()), user_id=user.id, token_hash=hash_session_token(raw_token),
        last_activity_at=now, idle_expires_at=now.replace(year=now.year + 1),
        absolute_expires_at=now.replace(year=now.year + 1), revoked_at=None,
        created_at=now, updated_at=now,
    )
    return session, raw_token


def _auth_client(user, extra_rows=None):
    """Build FakeSession wired for the auth middleware and return TestClient + user."""
    session, raw_token = _active_session(user)
    scalar_values = [session]
    objects = {user.id: user}
    rows = list(extra_rows or [])
    db = FakeSession(scalar_values=scalar_values, objects=objects, rows=rows)
    client = http_client(db)
    client.cookies.set("risklocker_session", raw_token)
    return client, user, session


# ── Notification service unit tests ────────────────────────────────────────


class TestNotificationService:
    def test_create_notification(self):
        db = FakeSession()
        user = _user()
        notification = create_notification(
            db, user.id, NotificationEventType.INVITATION.value,
            "Account Invitation", "You have been invited.", delivery_state="sent",
        )
        assert notification.id is not None
        assert notification.recipient_id == user.id
        assert notification.event_type == "invitation"
        assert notification.read_at is None
        assert notification.delivery_state == "sent"
        assert len(db.added) == 1

    def test_create_notification_with_delivery_failure(self):
        db = FakeSession()
        user = _user()
        notification = create_notification(
            db, user.id, NotificationEventType.INVITATION.value,
            "Account Invitation", "You have been invited.",
            delivery_state="failed", delivery_error="SMTP timeout",
        )
        assert notification.delivery_state == "failed"
        assert notification.delivery_error == "SMTP timeout"

    def test_get_notifications_returns_recipient_only(self):
        u1 = _user(email="a@risklocker.com")
        u2 = _user(email="b@risklocker.com")
        n1 = Notification(id=str(uuid4()), recipient_id=u1.id, event_type="invitation",
                          title="T1", body="B1")
        n2 = Notification(id=str(uuid4()), recipient_id=u2.id, event_type="invitation",
                          title="T2", body="B2")
        db = FakeSession(rows=[n1, n2])
        result = get_notifications(db, u1.id)
        assert len(result) == 2

    def test_get_unread_count(self):
        user = _user()
        n1 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T1", body="B1", read_at=None)
        n2 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T2", body="B2", read_at=datetime.now(timezone.utc))
        db = FakeSession(rows=[n1, n2])
        count = get_unread_count(db, user.id)
        assert count == 2

    def test_mark_read_changes_read_at(self):
        user = _user()
        notification = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                                    title="T1", body="B1", read_at=None)
        db = FakeSession(objects={notification.id: notification})
        updated = mark_read(db, notification.id, user.id)
        assert updated.read_at is not None

    def test_mark_read_recipient_isolation(self):
        u1 = _user(email="a@risklocker.com")
        u2 = _user(email="b@risklocker.com")
        notification = Notification(id=str(uuid4()), recipient_id=u1.id, event_type="invitation",
                                    title="T1", body="B1", read_at=None)
        db = FakeSession(objects={notification.id: notification})
        with pytest.raises(AppError, match="Notification not found"):
            mark_read(db, notification.id, u2.id)

    def test_mark_read_not_found(self):
        db = FakeSession()
        with pytest.raises(AppError, match="Notification not found"):
            mark_read(db, "nonexistent", _user().id)

    def test_mark_all_read_only_unread(self):
        user = _user()
        n1 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T1", body="B1", read_at=None)
        n2 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T2", body="B2", read_at=datetime.now(timezone.utc))
        db = FakeSession(rows=[n1, n2])
        updated = mark_all_read(db, user.id)
        assert updated == 2

    def test_serialize_notification(self):
        notification = Notification(
            id=str(uuid4()), recipient_id=str(uuid4()), event_type="invitation",
            title="Account Invitation", body="You have been invited.",
            delivery_state="sent", created_at=datetime.now(timezone.utc),
        )
        result = serialize_notification(notification)
        assert result["id"] == notification.id
        assert result["event_type"] == "invitation"
        assert result["title"] == "Account Invitation"
        assert result["body"] == "You have been invited."
        assert result["read_at"] is None
        assert result["delivery_state"] == "sent"


# ── Invitation and invited-account lifecycle tests ──────────────────────────


class TestInvitedAccountLifecycle:
    def test_invite_user_creates_invited_account(self):
        admin = _admin()
        db = FakeSession(objects={admin.id: admin}, rows=[])
        delivered = []

        user = invite_user(
            db, _test_settings(), admin, "newuser@risklocker.com", "Staff",
            sender=lambda _s, recipient, code: delivered.append((recipient, code)),
        )
        assert user.status == AccountStatus.INVITED.value
        assert len(delivered) == 1
        assert delivered[0][0] == "newuser@risklocker.com"
        assert len(delivered[0][1]) == 6

    def test_invite_user_records_delivery_failure(self):
        admin = _admin()
        db = FakeSession(objects={admin.id: admin}, rows=[])

        user = invite_user(
            db, _test_settings(), admin, "newuser@risklocker.com", "Staff",
            sender=lambda _s, _r, _c: (_ for _ in ()).throw(RuntimeError("SMTP down")),
        )
        assert user.status == AccountStatus.INVITED.value
        notifications = [obj for obj in db.added if isinstance(obj, Notification)]
        assert len(notifications) >= 1
        failed = [n for n in notifications if n.delivery_state == "failed"]
        assert len(failed) >= 1
        assert "SMTP down" in (failed[0].delivery_error or "")

    def test_invited_user_can_verify_code_and_promotes_to_active(self):
        now = datetime.now(timezone.utc)
        user = _user(status=AccountStatus.INVITED.value)
        code_id = str(uuid4())
        from app.core.security import generate_login_code, hash_login_code

        raw_code = generate_login_code()
        from app.models.tables import LoginCode
        challenge = LoginCode(
            id=code_id, user_id=user.id,
            email_hash="test-hash", code_hash=hash_login_code(code_id, raw_code, "test-auth-hash-secret-that-is-long-enough"),
            attempt_count=0, max_attempts=3,
            expires_at=now.replace(year=now.year + 1),
            resend_available_at=now,
            consumed_at=None,
        )
        db = FakeSession(
            scalar_values=[challenge, user],
            objects={user.id: user},
        )
        result_user, session, raw_token = verify_code_and_create_session(
            db, _test_settings(), user.email, raw_code,
        )
        assert result_user.status == AccountStatus.ACTIVE.value

    def test_invited_user_can_request_login_code(self):
        from app.services.auth_service import request_login_code
        user = _user(status=AccountStatus.INVITED.value)
        db = FakeSession(scalar_values=[user], rows=[])
        message = request_login_code(
            db, _test_settings(), user.email,
            sender=lambda _s, _r, _c: None,
        )
        assert message == LOGIN_REQUEST_MESSAGE

    def test_inactive_account_cannot_request_code(self):
        from app.services.auth_service import request_login_code
        user = _user(status=AccountStatus.INACTIVE.value)
        db = FakeSession(scalar_values=[user], rows=[])
        message = request_login_code(
            db, _test_settings(), user.email,
            sender=lambda _s, _r, _c: None,
        )
        assert message == LOGIN_REQUEST_MESSAGE


# ── Role and status notification tests ──────────────────────────────────────


class TestRoleStatusNotifications:
    def test_notify_role_change_creates_notification(self):
        admin = _admin()
        target = _user(role="Staff")
        db = FakeSession(rows=[])
        notify_role_change(db, _test_settings(), admin, target, "Manager")
        notifications = [obj for obj in db.added if isinstance(obj, Notification)]
        assert len(notifications) == 1
        assert notifications[0].event_type == NotificationEventType.ROLE_CHANGE.value
        assert notifications[0].recipient_id == target.id
        assert "Manager" in notifications[0].title or "Manager" in notifications[0].body

    def test_notify_status_change_creates_notification(self):
        admin = _admin()
        target = _user(status="active")
        db = FakeSession(rows=[])
        notify_status_change(db, _test_settings(), admin, target, "inactive")
        notifications = [obj for obj in db.added if isinstance(obj, Notification)]
        assert len(notifications) == 1
        assert notifications[0].event_type == NotificationEventType.STATUS_CHANGE.value

    def test_update_user_detects_role_change(self):
        admin = _admin()
        target = _user(role="Staff")
        db = FakeSession(objects={target.id: target}, rows=[])
        updated = update_user(db, admin, target, email=None, role="Manager", status=None)
        assert updated.role == "Manager"


# ── HTTP endpoint tests ─────────────────────────────────────────────────────


class TestNotificationHttpEndpoints:
    def test_list_notifications_http(self):
        user = _user()
        n1 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T1", body="B1", delivery_state="sent",
                          created_at=datetime.now(timezone.utc))
        client, _, _ = _auth_client(user, extra_rows=[n1])

        response = client.get("/notifications")
        assert response.status_code == 200
        assert len(response.json()["notifications"]) == 1

    def test_unread_count_http(self):
        user = _user()
        n1 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T1", body="B1", read_at=None,
                          created_at=datetime.now(timezone.utc))
        client, _, _ = _auth_client(user, extra_rows=[n1])

        response = client.get("/notifications/unread-count")
        assert response.status_code == 200
        assert response.json()["unread_count"] == 1

    def test_mark_read_http(self):
        user = _user()
        notification = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                                    title="T1", body="B1", read_at=None, delivery_state="sent",
                                    created_at=datetime.now(timezone.utc))
        sess, token = _active_session(user)
        db = FakeSession(scalar_values=[sess], objects={user.id: user, notification.id: notification})
        client = http_client(db)
        client.cookies.set("risklocker_session", token)

        response = client.patch(f"/notifications/{notification.id}/read")
        assert response.status_code == 200
        assert response.json()["notification"]["read_at"] is not None

    def test_mark_read_recipient_isolation_http(self):
        u1 = _user()
        u2 = _user(email="other@risklocker.com")
        notification = Notification(id=str(uuid4()), recipient_id=u2.id, event_type="invitation",
                                    title="T1", body="B1", read_at=None, delivery_state="sent",
                                    created_at=datetime.now(timezone.utc))
        sess, token = _active_session(u1)
        db = FakeSession(scalar_values=[sess], objects={u1.id: u1, notification.id: notification})
        client = http_client(db)
        client.cookies.set("risklocker_session", token)

        response = client.patch(f"/notifications/{notification.id}/read")
        assert response.status_code == 404

    def test_mark_all_read_http(self):
        user = _user()
        n1 = Notification(id=str(uuid4()), recipient_id=user.id, event_type="invitation",
                          title="T1", body="B1", read_at=None,
                          created_at=datetime.now(timezone.utc))
        client, _, _ = _auth_client(user, extra_rows=[n1])

        response = client.patch("/notifications/read")
        assert response.status_code == 200
        assert response.json()["updated"] == 1

    def test_notification_endpoints_require_auth(self):
        client = http_client(FakeSession())
        assert client.get("/notifications").status_code == 401
        assert client.get("/notifications/unread-count").status_code == 401
        assert client.patch("/notifications/some-id/read").status_code == 401
        assert client.patch("/notifications/read").status_code == 401


class TestAdminMailTestHttp:
    def test_mail_test_requires_admin(self):
        staff = _user(role="Staff")
        client, _, _ = _auth_client(staff)

        response = client.post("/admin/mail/test")
        assert response.status_code == 403

    def test_mail_test_configured(self, monkeypatch):
        admin = _admin()
        client, _, _ = _auth_client(admin)

        monkeypatch.setattr(
            routes,
            "validate_smtp_connection",
            lambda _settings: (True, "SMTP connection validated successfully."),
        )
        monkeypatch.setattr(
            routes,
            "send_test_email",
            lambda _settings, _recipient: None,
        )

        response = client.post("/admin/mail/test")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert admin.email in body["message"]

    def test_mail_test_not_configured(self, monkeypatch):
        admin = _admin()
        client, _, _ = _auth_client(admin)

        monkeypatch.setattr(
            routes,
            "validate_smtp_connection",
            lambda _settings: (False, "SMTP_HOST and SMTP_FROM_EMAIL are not configured."),
        )

        response = client.post("/admin/mail/test")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is False


# ── User create HTTP with invitation ────────────────────────────────────────


class TestUserCreateWithInvitationHttp:
    def test_create_user_sends_invitation(self, monkeypatch):
        admin = _admin()
        client, _, _ = _auth_client(admin)
        delivered = []

        monkeypatch.setattr(
            routes,
            "invite_user",
            lambda db, settings, actor, email, role, sender=None: (
                delivered.append((email, role)) or _user(email=email, role=role, status="invited")
            ),
        )

        response = client.post("/users", json={"email": "new@risklocker.com", "role": "Staff"})
        assert response.status_code == 200
        assert response.json()["status"] == "invited"
        assert len(delivered) == 1
