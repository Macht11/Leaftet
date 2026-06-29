from __future__ import annotations

import re


def detect_brands(text: str, brands: list[str]) -> list[str]:
    found: list[str] = []
    for brand in brands:
        pattern = rf"(?<![\w]){re.escape(brand)}(?![\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(brand)
    return found
