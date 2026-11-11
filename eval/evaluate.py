"""Compare three setups on a dev set and a held-out set."""
from pathlib import Path
import pandas as pd
from src.ingest import load_chunks
from src.extract import extract_claims
from src.verify import Verifier

DATASETS = {
    "dev": ("data/draft_memo.txt", "data/answer_key.csv"),
    "held-out": ("data/draft_memo2.txt", "data/answer_key2.csv"),
}
SETUPS = [
    ("dense only", "dense", False),
    ("hybrid", "hybrid", False),
    ("hybrid + rules", "hybrid", True),
]


def score(v, memo, key_path, show_misses=False):
    claims = extract_claims(Path(memo).read_text(encoding="utf-8"))
    key = pd.read_csv(key_path)
    assert len(claims) == len(key), f"{len(claims)} claims vs {len(key)} labels"
    tp = fp = fn = tn = 0
    for c, (_, row) in zip(claims, key.iterrows()):
        r = v.verify(c["text"])
        flagged, truth = r["status"] != "Supported", row["label"] == "error"
        tp += flagged and truth
        fp += flagged and not truth
        fn += (not flagged) and truth
        tn += (not flagged) and not truth
        if show_misses and flagged != truth:
            et = row["error_type"] if pd.notna(row["error_type"]) else "correct claim"
            print(f"   MISS #{row['id']} ({et}): "
                  f"{r['status']} | {c['text'][:60]}")
    p = tp / (tp + fp) if tp + fp else 0.0
    r_ = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r_ / (p + r_) if p + r_ else 0.0
    return dict(TP=tp, FP=fp, FN=fn, TN=tn, precision=round(p, 2),
                recall=round(r_, 2), f1=round(f1, 2))


if __name__ == "__main__":
    v = Verifier(load_chunks())
    rows = []
    for ds, (memo, key) in DATASETS.items():
        for name, mode, use_rules in SETUPS:
            v.mode = mode
            v.use_rules = use_rules
            print(f"[{ds}] {name}")
            rows.append(dict(dataset=ds, setup=name,
                             **score(v, memo, key, show_misses=(name == "hybrid + rules"))))
    df = pd.DataFrame(rows)
    print("\n", df.to_string(index=False))
    df.to_csv("eval/results.csv", index=False)
    print("\nSaved eval/results.csv")