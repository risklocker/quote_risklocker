"""Upload validation helpers kept free of web/database dependencies for testing."""

from __future__ import annotations

from pathlib import Path


ALLOWED_UPLOADS = {
    ".pdf": {"application/pdf"},
}


def display_filename(filename: str | None) -> str:
    name = Path(filename or "quotation").name
    cleaned = "".join(ch if ch.isalnum() or ch in {".", "-", "_", " "} else "_" for ch in name).strip()
    return cleaned[:180] or "quotation"


def validate_upload_bytes(filename: str | None, content_type: str | None, data: bytes, max_bytes: int = 1024 * 1024) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOADS:
        raise ValueError("Upload a PDF file.")
    if not data:
        raise ValueError("The selected PDF is empty.")
    if len(data) > max_bytes:
        size_mb = max_bytes / (1024 * 1024)
        raise ValueError(f"Each PDF must be {size_mb:g}MB or smaller.")

    normalized_type = (content_type or "").split(";")[0].lower()
    if normalized_type and normalized_type not in ALLOWED_UPLOADS[suffix]:
        raise ValueError("File type does not match the selected file.")

    if suffix == ".pdf" and not data.startswith(b"%PDF"):
        raise ValueError("File type does not match the selected file.")
    return suffix
