from services.classifier import classify_text


CATEGORIES = {
    "MX": {"keywords": ["smartphone", "galaxy", "iphone"]},
    "VD": {"keywords": ["TV", "OLED", "4K"]},
    "DA": {"keywords": ["lave-linge", "réfrigérateur"]},
}


def test_classifies_mx_text():
    assert classify_text("Samsung Galaxy smartphone", CATEGORIES) == "MX"


def test_classifies_vd_text():
    assert classify_text("TV OLED 4K", CATEGORIES) == "VD"


def test_returns_other_without_keywords():
    assert classify_text("weekly grocery offers", CATEGORIES) == "Other"
