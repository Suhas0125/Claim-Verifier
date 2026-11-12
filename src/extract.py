"""Split a draft memo into atomic claims. Handles bullets, headers, abbreviations."""
import re

HEADER = re.compile(r"^(MEMORANDUM|TO:|FROM:|DATE:|SUBJECT:|CC:)")
ABBR = re.compile(r"\b(U\.S\.|U\.K\.|Inc\.|Ltd\.|Corp\.|Co\.|No\.|vs\.|e\.g\.|i\.e\.)")


def _protect(s):
    return ABBR.sub(lambda m: m.group().replace(".", "§"), s)


def _join_wrapped(text: str) -> str:
    """Re-join sentences that a PDF copy-paste broke across lines."""
    out = []
    for line in _join_wrapped(text).splitlines():
        s = line.strip()
        if not s:
            out.append("")
            continue
        prev = out[-1] if out else ""
        FUNC = {"a", "an", "the", "of", "to", "and", "or", "in", "at", "by", "for", "with", "from", "is", "are"}
        if (prev and not re.search(r"[.!?:]$", prev) and not re.match(r"^[•\-\*●\d]", s)
                and (s[0].islower() or prev.endswith(",")
                     or prev.split()[-1].lower() in FUNC)):
            out[-1] = prev + " " + s
        else:
            out.append(s)
    return "\n".join(out)


def extract_claims(text: str) -> list[dict]:
    claims = []
    for line in text.splitlines():
        line = re.sub(r"^[\s•\-\*●]+", "", line).strip()
        if not line or HEADER.match(line):
            continue
        if (not re.search(r"[.!?]$", line) and len(line.split()) <= 8
                and not re.search(r"\d", line)):
            continue  # short line without a period = heading
        for sent in re.split(r"(?<=[.!?])\s+", _protect(line)):
            for part in re.split(r",\s+and\s+|;\s+", sent):
                part = part.replace("§", ".").strip().rstrip(".:")
                part = re.sub(r"^[A-Z][\w&()/\- ]{2,40}:\s+", "", part)  # drop "Label:" prefix
                part = part.strip()
                if len(part.split()) >= 3:
                    claims.append(part)
    return [{"id": i + 1, "text": c} for i, c in enumerate(claims)]