import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.errors import AppError
from app.models.enums import StorageStatus
from app.services.pdf_content import load_pdf_bytes, parse_byte_range
from app.services.storage_retention import purge_expired_pdfs


class ScalarResult:
    def __init__(self, records):
        self.records = records

    def all(self):
        return self.records


def stored_record(record_id: str, *, archived: bool = False):
    return SimpleNamespace(
        id=record_id,
        storage_path=f"source/2026/07/batch/{record_id}.pdf",
        storage_provider="supabase",
        storage_status=StorageStatus.AVAILABLE.value,
        storage_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        storage_deleted_at=None,
        archive_status=StorageStatus.ARCHIVED.value if archived else None,
        archive_item_id="archive-item" if archived else None,
        extracted_history="retained",
    )


def test_byte_ranges_support_browser_pdf_loading():
    assert parse_byte_range(None, 100) is None
    assert parse_byte_range("bytes=0-9", 100) == (0, 9)
    assert parse_byte_range("bytes=90-", 100) == (90, 99)
    assert parse_byte_range("bytes=-10", 100) == (90, 99)
    with pytest.raises(AppError) as error:
        parse_byte_range("bytes=200-300", 100)
    assert error.value.status_code == 416


def test_expired_source_keeps_database_history_but_content_is_unavailable():
    record = stored_record("expired-source")
    with pytest.raises(AppError, match="PDF Expired") as error:
        load_pdf_bytes(record, SimpleNamespace())
    assert error.value.status_code == 410
    assert record.extracted_history == "retained"


def test_retention_deletes_objects_and_preserves_records():
    source = stored_record("source")
    generated = stored_record("generated", archived=True)
    db = MagicMock()
    db.scalars.side_effect = [ScalarResult([source]), ScalarResult([generated])]
    storage = MagicMock()

    result = purge_expired_pdfs(db, storage)

    assert result == {"processed": 2, "deleted": 2, "failures": []}
    assert storage.delete_pdf.call_count == 2
    assert source.storage_status == StorageStatus.EXPIRED.value
    assert generated.storage_status == StorageStatus.ARCHIVED.value
    assert source.extracted_history == "retained"
    db.commit.assert_called_once()
