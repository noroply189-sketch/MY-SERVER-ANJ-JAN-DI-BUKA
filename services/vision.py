from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None


async def ocr_image(image_path: str | Path) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed.")
    try:
        return pytesseract.image_to_string(Image.open(path), config="--psm 6")
    except Exception as exc:
        raise RuntimeError(f"OCR failed: {exc}") from exc


async def describe_image(image_path: str | Path) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    with Image.open(path) as img:
        width, height = img.size
    return f"Image dimensions: {width}x{height}, format: {path.suffix.lower() or 'unknown'}"


async def read_image_question(image_path: str | Path) -> str:
    text = await ocr_image(image_path)
    return text.strip() or "No text was detected in the image."


__all__ = ["ocr_image", "describe_image", "read_image_question"]
