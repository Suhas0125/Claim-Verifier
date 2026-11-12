from src.rules import check
from src.rules import polarity_check

EV = ["Net profit for FY2025 was Rs 110 crore.",
      "The board approved a dividend of Rs 4 per share on 15 May 2025."]


def test_wrong_number_fails():
    assert check("Net profit was Rs 130 crore", EV)["status"] == "fail"


def test_correct_number_passes():
    assert check("Net profit was Rs 110 crore", EV)["status"] == "pass"


def test_wrong_date_fails():
    assert check("Dividend approved on 15 June 2025", EV)["status"] == "fail"


def test_correct_date_passes():
    assert check("Dividend approved on 15 May 2025", EV)["status"] == "pass"


def test_no_numbers_is_na():
    assert check("The auditor issued a qualified opinion", EV)["status"] == "n/a"


def test_comma_numbers_normalized():
    assert check("Revenue was Rs 1,250 crore", ["Revenue of Rs 1250 crore"])["status"] == "pass"

def test_polarity_flags_opposite():
    r = polarity_check("The auditor issued a qualified opinion",
                       "The auditor's report carried an unqualified opinion.")
    assert r["status"] == "fail"

def test_unit_mismatch_fails():
    r = check("The market will reach $135.3 million", ["The market will reach $135.3 billion by 2025."])
    assert r["status"] == "fail"