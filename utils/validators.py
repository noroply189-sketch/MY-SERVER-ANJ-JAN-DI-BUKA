from __future__ import annotations

import mimetypes
from pathlib import Path

from utils.security import SAFE_FILE_EXTENSIONS


def validate_file_size(file_path: str | Path, max_mb: int) -> bool:
    path = Path(file_path)
    if not path.exists() or path.stat().st_size <= 0:
        return False
    return (path.stat().st_size / (1024 * 1024)) <= max_mb


def validate_extension(file_name: str, allowed: set[str] | None = None) -> bool:
    ext = Path(file_name).suffix.lower().lstrip(".")
    allowed_exts = allowed or SAFE_FILE_EXTENSIONS
    return ext in {item.lower() for item in allowed_exts}


def validate_mime_type(file_path: str | Path, expected: set[str] | None = None) -> bool:
    guessed, _ = mimetypes.guess_type(str(file_path))
    if not guessed:
        return False
    if expected is None:
        return True
    return guessed in expected


def file_summary(file_path: str | Path) -> dict[str, object]:
    path = Path(file_path)
    if not path.exists():
        return {"exists": False}
    return {
        "exists": True,
        "name": path.name,
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 4),
    }
