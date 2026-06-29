from services.brand_detector import detect_brands


def test_detects_known_brands_case_insensitively():
    assert detect_brands("samsung and LG offers", ["Samsung", "LG", "Sony"]) == ["Samsung", "LG"]


def test_does_not_match_inside_words():
    assert detect_brands("This is not lgear", ["LG"]) == []
