"""Typed request bodies for authentication and employee-account mutations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginCodeRequest(StrictRequest):
    email: str = Field(min_length=3, max_length=255)


class LoginCodeVerify(StrictRequest):
    email: str = Field(min_length=3, max_length=255)
    code: str = Field(pattern=r"^\d{6}$")


class UserCreateRequest(StrictRequest):
    email: str = Field(min_length=3, max_length=255)
    role: str = "Staff"


class UserUpdateRequest(StrictRequest):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: str | None = None
    status: str | None = None
