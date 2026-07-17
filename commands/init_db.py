"""Seed default settings into an already-migrated Supabase/Postgres database."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.cli import init_db


if __name__ == "__main__":
    init_db()
