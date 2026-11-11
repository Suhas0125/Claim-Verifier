"""Load source documents and split them into sentence-level chunks."""
import re
from pathlib import Path


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def load_chunks(source_dir: str = "data/sources") -> list[dict]:
    """Return a list of {id, source, text} chunks, one per sentence."""
    chunks = []
    for path in sorted(Path(source_dir).glob("*.txt")):
        for i, sent in enumerate(split_sentences(path.read_text(encoding="utf-8"))):
            chunks.append({"id": f"{path.stem}-{i}", "source": path.name, "text": sent})
    return chunks


if __name__ == "__main__":
    data = load_chunks()
    print(f"{len(data)} chunks loaded")
    for c in data[:3]:
        print(c)
