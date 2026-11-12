"""Deterministic checks: numbers and dates in a claim must appear in the evidence."""
import re

MONTHS = ("January|February|March|April|May|June|July|August|"
          "September|October|November|December")
DATE_RE = re.compile(rf"(\d{{1,2}})\s+({MONTHS})\s+(\d{{4}})", re.I)
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def extract_dates(text: str) -> set[tuple]:
    return {(int(d), m.lower(), int(y)) for d, m, y in DATE_RE.findall(text)}


def _floats(text: str) -> set[float]:
    text = DATE_RE.sub(" ", text)
    out = set()
    for n in NUM_RE.findall(text):
        try:
            out.add(float(n.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return out


UNIT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|trillion|crore|lakh)s?\b", re.I)


def _unit_pairs(text: str) -> set[tuple]:
    out = set()
    for n, u in UNIT_RE.findall(text):
        try:
            out.add((float(n.replace(",", "")), u.lower()))
        except ValueError:
            pass
    return out


def check(claim: str, evidence_texts: list[str]) -> dict:
    """Numbers, dates and units in the claim must match the evidence texts."""
    evidence = " ".join(evidence_texts)
    c_dates, c_nums = extract_dates(claim), _floats(claim)
    if not c_dates and not c_nums:
        return {"status": "n/a", "reason": "no numbers or dates in claim"}

    e_nums = _floats(evidence)
    e_nums |= {x / 1000 for x in e_nums} | {x * 1000 for x in e_nums}
    bad_dates = c_dates - extract_dates(evidence)
    bad_nums = {n for n in c_nums if not any(abs(n - e) < 1e-9 for e in e_nums)}
    c_u, e_u = _unit_pairs(claim), _unit_pairs(evidence)
    bad_units = {(n, u) for n, u in c_u
                 if (n, u) not in e_u and any(en == n for en, _ in e_u)}

    if bad_dates or bad_nums or bad_units:
        parts = []
        if bad_dates:
            parts.append("dates not in evidence: " +
                         ", ".join(f"{d} {m.title()} {y}" for d, m, y in sorted(bad_dates)))
        if bad_nums:
            parts.append("numbers not in evidence: " +
                         ", ".join(f"{n:g}" for n in sorted(bad_nums)))
        if bad_units:
            parts.append("unit differs from source: " +
                         ", ".join(f"{n:g} {u}" for n, u in sorted(bad_units)))
        return {"status": "fail", "reason": "; ".join(parts)}
    return {"status": "pass", "reason": "all numbers, dates and units found in evidence"}


POLARITY = [("qualified", "unqualified"), ("increase", "decrease"),
            ("increased", "decreased"), ("approved", "rejected"),
            ("profit", "loss"), ("complies", "violates")]


def polarity_check(claim: str, evidence: str) -> dict:
    """Flag claims that use the opposite word of a pair found in the evidence."""
    c = set(re.findall(r"[a-z]+", claim.lower()))
    e = set(re.findall(r"[a-z]+", evidence.lower()))
    for a, b in POLARITY:
        for x, y in ((a, b), (b, a)):
            if x in c and y in e and x not in e:
                return {"status": "fail", "reason": f"claim says '{x}', evidence says '{y}'"}
    return {"status": "pass", "reason": ""}