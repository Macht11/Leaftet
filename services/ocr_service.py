from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image


def ocr_image(image_path: Path, languages: str = "fra+eng") -> str:
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang=languages)
    except Exception as exc:  # keep retailer failures from killing scans
        return f"OCR unavailable for {image_path.name}: {exc}"
