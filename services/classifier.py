from __future__ import annotations

import re


def classify_text(text: str, categories: dict) -> str:
    scores: dict[str, int] = {}
    for category, config in categories.items():
        score = 0
        for keyword in config.get("keywords", []):
            pattern = rf"(?<![\w]){re.escape(keyword)}(?![\w])"
            score += len(re.findall(pattern, text, flags=re.IGNORECASE))
        scores[category] = score
    best_category, best_score = max(scores.items(), key=lambda item: item[1]) if scores else ("Other", 0)
    return best_category if best_score > 0 else "Other"
