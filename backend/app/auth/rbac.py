"""Role checks for API operations."""

from __future__ import annotations

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import Role
from app.models.tables import User


def require_role(user: User, *roles: Role) -> None:
    if user.role not in {role.value for role in roles}:
        raise AppError("You do not have permission to do this.", status.HTTP_403_FORBIDDEN)


def can_view_owner(user: User, owner_id: str) -> bool:
    return user.role in {Role.ADMIN.value, Role.MANAGER.value} or user.id == owner_id


def can_view_owner_record(db: Session, actor: User, owner_id: str) -> bool:
    if actor.role == Role.ADMIN.value:
        return True
    if actor.id == owner_id:
        return True
    if actor.role == Role.MANAGER.value:
        owner = db.get(User, owner_id)
        return bool(owner and owner.role == Role.STAFF.value)
    return False


def can_manage_target(actor: User, target_role: str) -> bool:
    if actor.role == Role.ADMIN.value:
        return True
    if actor.role == Role.MANAGER.value:
        return target_role == Role.STAFF.value
    return False
