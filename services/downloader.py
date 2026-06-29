from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


def hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_filename(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned[:140] or "catalogue"


def download_file(url: str, output_dir: Path, stem: str) -> tuple[Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    content = response.content
    suffix = Path(urlparse(url).path).suffix or ".bin"
    digest = hash_bytes(content)
    path = output_dir / f"{safe_filename(stem)}_{digest[:10]}{suffix}"
    path.write_bytes(content)
    return path, digest
