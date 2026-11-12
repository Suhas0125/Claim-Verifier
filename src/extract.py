"""Split a draft memo into atomic claims. Handles bullets, headers, abbreviations."""
import re

HEADER = re.compile(r"^(MEMORANDUM|TO:|FROM:|DATE:|SUBJECT:|CC:)")
ABBR = re.compile(r"\b(U\.S\.|U\.K\.|Inc\.|Ltd\.|Corp\.|Co\.|No\.|vs\.|e\.g\.|i\.e\.)")


def _protect(s):
    return ABBR.sub(lambda m: m.group().replace(".", "§"), s)


def extract_claims(text: str) -> list[dict]:
    claims = []
    for line in text.splitlines():
        line = re.sub(r"^[\s•\-\*●]+", "", line).strip()
        if not line or HEADER.match(line):
            continue
        if not re.search(r"[.!?]$", line) and len(line.split()) <= 8:
            continue  # short line without a period = heading
        for sent in re.split(r"(?<=[.!?])\s+", _protect(line)):
            for part in re.split(r",\s+and\s+|;\s+", sent):
                part = part.replace("§", ".").strip().rstrip(".:")
                part = re.sub(r"^[A-Z][\w&()/\- ]{2,40}:\s+", "", part)  # drop "Label:" prefix
                part = part.strip()
                if len(part.split()) >= 3:
                    claims.append(part)
    return [{"id": i + 1, "text": c} for i, c in enumerate(claims)]