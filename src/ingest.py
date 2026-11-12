"""Load .txt and .pdf sources and split them into sentence-level chunks."""
import re
from pathlib import Path
from pypdf import PdfReader


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        pages = (p.extract_text() or "" for p in PdfReader(str(path)).pages)
        text = re.sub(r"\s+", " ", " ".join(pages))
        return re.sub(r"\.{3,}", " ", text)  # remove table dot leaders
    return path.read_text(encoding="utf-8")


def load_chunks(source_dir: str = "data/sources") -> list[dict]:
    chunks = []
    files = sorted(p for p in Path(source_dir).iterdir()
                   if p.suffix.lower() in {".txt", ".pdf"})
    for path in files:
        sents = [s for s in split_sentences(read_file(path)) if len(s.split()) >= 4]
        for i, sent in enumerate(sents):
            chunks.append({"id": f"{path.stem}-{i}", "source": path.name, "text": sent})
        for i in range(len(sents) - 1):
            chunks.append({"id": f"{path.stem}-w{i}", "source": path.name,
                           "text": sents[i] + " " + sents[i + 1]})
    return chunks


if __name__ == "__main__":
    data = load_chunks()
    print(f"{len(data)} chunks loaded")