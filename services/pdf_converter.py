from __future__ import annotations

from pathlib import Path

import fitz


def pdf_to_images(pdf_path: Path, output_dir: Path, zoom: float = 2.0) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    images: list[Path] = []
    matrix = fitz.Matrix(zoom, zoom)
    for index, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = output_dir / f"{pdf_path.stem}_page_{index:03d}.png"
        pixmap.save(image_path)
        images.append(image_path)
    return images
