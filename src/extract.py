"""Split a draft memo into atomic, checkable claims (rule-based, no LLM)."""
import re


def extract_claims(text: str) -> list[dict]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    claims = []
    for s in sentences:
        # split compound sentences on ", and " (keeps "Act 2013 and Ind AS" intact)
        for part in re.split(r",\s+and\s+", s):
            part = part.strip().rstrip(".")
            if len(part.split()) >= 3:
                claims.append(part)
    return [{"id": i + 1, "text": c} for i, c in enumerate(claims)]


if __name__ == "__main__":
    from pathlib import Path

    claims = extract_claims(Path("data/draft_memo.txt").read_text(encoding="utf-8"))
    print(f"{len(claims)} claims")
    for c in claims:
        print(c["id"], c["text"])