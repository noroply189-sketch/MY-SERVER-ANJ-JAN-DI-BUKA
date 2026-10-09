from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterable


SAFE_FILE_EXTENSIONS = {
    "txt", "md", "rtf", "odt", "json", "xml", "yaml", "yml", "sql", "py", "js", "ts",
    "html", "css", "log", "csv", "zip", "pdf", "docx", "xlsx", "pptx", "png", "jpg",
    "jpeg", "webp", "gif"
}


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(name).name)
    sanitized = sanitized.strip("._ ") or "downloaded_file"
    return sanitized


def ensure_safe_path(base_dir: str | Path, candidate: str | Path) -> Path:
    base = Path(base_dir).resolve()
    target = (base / candidate).resolve()
    if base not in target.parents and target != base:
        raise ValueError("Refusing to access a path outside the designated storage directory.")
    return target


def cleanup_temp_files(root_dir: str | Path, max_age_minutes: int = 30) -> int:
    root = Path(root_dir)
    if not root.exists():
        return 0

    removed = 0
    now = os.path.getmtime
    cutoff = __import__("time").time() - (max_age_minutes * 60)

    for path in root.rglob("*"):
        if path.is_file() and now(path) < cutoff:
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
    return removed


def is_archive_safe(path: str | Path) -> bool:
    file_path = Path(path)
    if not file_path.exists():
        return False
    try:
        with zipfile.ZipFile(file_path) as archive:
            infos = archive.infolist()
            if not infos:
                return False
            total = sum(info.file_size for info in infos)
            if total > 200 * 1024 * 1024:
                return False
            for info in infos:
                if info.is_dir():
                    continue
                if info.filename.startswith("/") or ".." in Path(info.filename).parts:
                    return False
                if info.file_size > 50 * 1024 * 1024:
                    return False
            return True
    except Exception:
        return False


def safe_temp_dir(prefix: str = "agent_") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def redact_sensitive_text(value: str, keep_last: int = 4) -> str:
    if len(value) <= keep_last:
        return "***"
    return f"{'*' * max(3, len(value) - keep_last)}{value[-keep_last:]}"


def safe_string(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).replace("\x00", "")[:2000]


import zipfile
