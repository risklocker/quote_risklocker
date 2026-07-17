"""Small operational CLI helpers."""

from __future__ import annotations

import argparse

from sqlalchemy import select

from app.db.init_db import seed_defaults
from app.db.session import SessionLocal
from app.models.enums import AccountStatus, Role
from app.models.tables import User
from app.services.auth_service import normalize_employee_email


def init_db() -> None:
    with SessionLocal() as db:
        seed_defaults(db)


def create_admin(email: str) -> None:
    init_db()
    with SessionLocal() as db:
        normalized_email = normalize_employee_email(email)
        user = db.scalar(select(User).where(User.email == normalized_email))
        action = "Updated"
        if user:
            user.role = Role.ADMIN.value
            user.status = AccountStatus.ACTIVE.value
        else:
            action = "Created"
            user = User(email=normalized_email, role=Role.ADMIN.value, status=AccountStatus.ACTIVE.value)
            db.add(user)
        db.commit()
        print(f"{action} Admin account: {normalized_email}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    admin = sub.add_parser("create-admin")
    admin.add_argument("email")
    args = parser.parse_args()
    if args.command == "init-db":
        init_db()
    elif args.command == "create-admin":
        create_admin(args.email)


if __name__ == "__main__":
    main()
