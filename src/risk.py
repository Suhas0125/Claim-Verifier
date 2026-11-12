"""Risk score: how urgently should a human look at this claim? (0 to 1)"""
import re

SENSITIVE = ("regulator", "circular", "act ", "complian", "penalty", "audit",
             "opinion", "breach", "dividend", "borrowing", "terminate", "liability", "complaint")


def materiality(claim: str) -> float:
    c, m = claim.lower(), 0.0
    if re.search(r"\d", c):
        m += 0.10                      # contains figures or dates
    if any(w in c for w in SENSITIVE):
        m += 0.10                      # legal, regulatory or financial wording
    return m


def risk_score(result: dict) -> float:
    base = {"Contradicted": 0.80, "Unsupported": 0.60, "Partial": 0.45}.get(
        result["status"], 0.30 * (1 - result["confidence"]))
    return round(min(1.0, (base or 0.0) + materiality(result["claim"])), 3)