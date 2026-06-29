from __future__ import annotations

from pathlib import Path

DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
DOWNLOAD_DIR = DATA_DIR / "downloads"
PAGE_IMAGE_DIR = DATA_DIR / "pages"


def ensure_directories() -> None:
    for path in (DATA_DIR, OUTPUT_DIR, DOWNLOAD_DIR, PAGE_IMAGE_DIR):
        path.mkdir(parents=True, exist_ok=True)
