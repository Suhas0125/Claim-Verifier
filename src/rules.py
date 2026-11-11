"""Deterministic checks: numbers and dates in a claim must appear in the evidence."""
import re

MONTHS = ("January|February|March|April|May|June|July|August|"
          "September|October|November|December")
DATE_RE = re.compile(rf"(\d{{1,2}})\s+({MONTHS})\s+(\d{{4}})", re.I)
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def extract_dates(text: str) -> set[tuple]:
    return {(int(d), m.lower(), int(y)) for d, m, y in DATE_RE.findall(text)}


def extract_numbers(text: str) -> set[str]:
    text = DATE_RE.sub(" ", text)  # dates are checked separately
    return {n.replace(",", "").rstrip(".") for n in NUM_RE.findall(text) if n.strip(",")}


def check(claim: str, evidence_texts: list[str]) -> dict:
    """Return {'status': 'pass' | 'fail' | 'n/a', 'reason': str}."""
    evidence = " ".join(evidence_texts)
    c_dates, c_nums = extract_dates(claim), extract_numbers(claim)
    if not c_dates and not c_nums:
        return {"status": "n/a", "reason": "no numbers or dates in claim"}

    bad_dates = c_dates - extract_dates(evidence)
    bad_nums = c_nums - extract_numbers(evidence)
    if bad_dates or bad_nums:
        parts = []
        if bad_dates:
            parts.append("dates not in evidence: " +
                         ", ".join(f"{d} {m.title()} {y}" for d, m, y in sorted(bad_dates)))
        if bad_nums:
            parts.append("numbers not in evidence: " + ", ".join(sorted(bad_nums)))
        return {"status": "fail", "reason": "; ".join(parts)}
    return {"status": "pass", "reason": "all numbers and dates found in evidence"}