"""Safe access to local template assets."""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
from pathlib import Path
from typing import Any


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}


def asset_root() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "template_assets"


def _asset_id(path: Path) -> str:
    return hashlib.sha1(path.name.encode("utf-8")).hexdigest()[:16]


def _label(path: Path) -> str:
    name = path.stem.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", name).strip().title()


def list_template_assets() -> list[dict[str, Any]]:
    root = asset_root()
    if not root.exists():
        return []
    assets: list[dict[str, Any]] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        asset_id = _asset_id(path)
        assets.append(
            {
                "id": asset_id,
                "label": _label(path),
                "filename": path.name,
                "extension": path.suffix.lower(),
                "url": f"/template-assets/{asset_id}",
                "size_bytes": path.stat().st_size,
            }
        )
    return assets


def resolve_template_asset(asset_id: str) -> Path:
    root = asset_root()
    if not re.fullmatch(r"[a-f0-9]{16}", asset_id):
        raise FileNotFoundError(asset_id)
    for path in root.iterdir() if root.exists() else []:
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS and _asset_id(path) == asset_id:
            resolved = path.resolve()
            if root.resolve() not in resolved.parents:
                raise FileNotFoundError(asset_id)
            return resolved
    raise FileNotFoundError(asset_id)


def asset_data_uri(asset_id: str | None) -> str:
    if not asset_id:
        return ""
    try:
        path = resolve_template_asset(asset_id)
    except FileNotFoundError:
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def find_asset_by_hint(hints: list[str]) -> str:
    assets = list_template_assets()
    lowered = [(asset["id"], asset["filename"].lower(), asset["label"].lower()) for asset in assets]
    for hint in hints:
        token = hint.lower()
        for asset_id, filename, label in lowered:
            if token in filename or token in label:
                return asset_id
    return ""
