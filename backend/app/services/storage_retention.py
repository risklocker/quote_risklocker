"""Rolling PDF retention without deleting quotation database history."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.enums import StorageStatus
from app.models.tables import GeneratedPdfVersion, UploadedFile
from app.storage.supabase import StorageError, SupabaseStorage


def purge_expired_pdfs(db: Session, storage: SupabaseStorage, *, limit: int = 200) -> dict:
    now = datetime.now(timezone.utc)
    predicate = and_(
        UploadedFile.storage_provider == "supabase",
        UploadedFile.storage_expires_at.is_not(None),
        UploadedFile.storage_expires_at <= now,
        UploadedFile.storage_status.in_([StorageStatus.AVAILABLE.value, StorageStatus.ARCHIVE_PENDING.value, StorageStatus.ARCHIVE_FAILED.value]),
    )
    uploads = list(db.scalars(select(UploadedFile).where(predicate).limit(limit)).all())
    remaining = max(0, limit - len(uploads))
    version_predicate = and_(
        GeneratedPdfVersion.storage_provider == "supabase",
        GeneratedPdfVersion.storage_expires_at.is_not(None),
        GeneratedPdfVersion.storage_expires_at <= now,
        GeneratedPdfVersion.storage_status.in_([StorageStatus.AVAILABLE.value, StorageStatus.ARCHIVE_PENDING.value, StorageStatus.ARCHIVE_FAILED.value]),
    )
    versions = list(db.scalars(select(GeneratedPdfVersion).where(version_predicate).limit(remaining)).all())

    deleted = 0
    failures: list[dict] = []
    for kind, record in [("source", item) for item in uploads] + [("generated", item) for item in versions]:
        try:
            storage.delete_pdf(record.storage_path)
            record.storage_deleted_at = now
            record.storage_status = StorageStatus.ARCHIVED.value if record.archive_status == StorageStatus.ARCHIVED.value else StorageStatus.EXPIRED.value
            deleted += 1
        except StorageError as exc:
            failures.append({"type": kind, "id": record.id, "message": str(exc)})
    db.commit()
    return {"processed": len(uploads) + len(versions), "deleted": deleted, "failures": failures}
