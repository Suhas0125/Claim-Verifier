"""If a reviewer checks only the top-k claims, how many real errors do they catch?"""
import random
from pathlib import Path
import pandas as pd
from src.ingest import load_chunks
from src.extract import extract_claims
from src.verify import Verifier
from src.risk import risk_score
from eval.evaluate import DATASETS

if __name__ == "__main__":
    v = Verifier(load_chunks())
    v.mode, v.use_rules = "hybrid", True
    rows = []
    for ds, (memo, key_path) in DATASETS.items():
        claims = extract_claims(Path(memo).read_text(encoding="utf-8"))
        truth = [lab == "error" for lab in pd.read_csv(key_path)["label"]]
        scores = [risk_score(v.verify(c["text"])) for c in claims]
        n, n_err = len(claims), sum(truth)
        ranked = sorted(range(n), key=lambda i: -scores[i])
        rng = random.Random(0)
        for k in (3, 5, 7):
            rand = []
            for _ in range(2000):
                order = list(range(n)); rng.shuffle(order)
                rand.append(sum(truth[i] for i in order[:k]))
            rows.append(dict(
                dataset=ds, reviewed=k, total_errors=n_err,
                found_ranked=sum(truth[i] for i in ranked[:k]),
                found_doc_order=sum(truth[i] for i in range(k)),
                found_random=round(sum(rand) / len(rand), 1)))
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    df.to_csv("eval/triage_results.csv", index=False)