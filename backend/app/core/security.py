"""Cryptographic helpers for passwordless login codes and opaque sessions."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_login_code() -> str:
    """Return a fixed-width code suitable for delivery through the SMTP relay."""
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_session_token() -> str:
    """Return an opaque high-entropy token; only its hash is persisted."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def keyed_hash(value: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_login_code(challenge_id: str, code: str, secret: str) -> str:
    return keyed_hash(f"login-code:{challenge_id}:{code}", secret)


def verify_login_code_hash(challenge_id: str, code: str, stored_hash: str, secret: str) -> bool:
    expected = hash_login_code(challenge_id, code, secret)
    return hmac.compare_digest(expected, stored_hash)
