"""Database engine/session helpers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


def _sqlalchemy_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


engine = create_engine(_sqlalchemy_url(settings.database_url), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def verify_database_connection() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except SQLAlchemyError as exc:
        message = str(exc).lower()
        if "password authentication failed" in message:
            raise RuntimeError(
                "Supabase/Postgres database connection failed: password authentication failed for DATABASE_URL. "
                "Use the Supabase database password, not the anon or service-role API key."
            ) from None
        raise RuntimeError(
            "Supabase/Postgres database connection failed. Check DATABASE_URL, network access, and Supabase database status."
        ) from None


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
