from __future__ import annotations

from collections import Counter
from pathlib import Path

import plotly.express as px


def save_brand_chart(brand_counts: dict[str, int], output_path: Path) -> Path | None:
    if not brand_counts:
        return None
    fig = px.bar(x=list(brand_counts.keys()), y=list(brand_counts.values()), labels={"x": "Brand", "y": "Appearances"})
    try:
        fig.write_image(output_path)
        return output_path
    except Exception:
        return None


def count_brands(rows: list[dict]) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        for brand in row.get("brands", []):
            counter[brand] += 1
    return counter
