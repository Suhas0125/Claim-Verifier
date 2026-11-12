import csv
from pathlib import Path
from collections import Counter
from src.ingest import load_chunks
from src.extract import extract_claims
from src.verify import Verifier

v = Verifier(load_chunks("data/real/sources"))
claims = extract_claims(Path("data/real/draft.txt").read_text(encoding="utf-8"))
rows = [v.verify(c["text"]) for c in claims]

kinds = Counter(r["reason"].split(":")[0].split(" ")[0] + " / " + r["status"] for r in rows)
print("Breakdown (reason type / status):")
for k, n in kinds.most_common():
    print(f"  {n:>2}  {k}")

print("\nFlagged claims:")
for i, r in enumerate(rows, 1):
    if r["status"] != "Supported":
        print(f"\n#{i} {r['status']} | {r['reason'][:80]}")
        print("  CLAIM   :", r["claim"][:110])
        print("  EVIDENCE:", r["evidence"][:110])

with open("eval/real_review.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "claim", "tool_status", "reason", "human_label"])
    for i, r in enumerate(rows, 1):
        w.writerow([i, r["claim"], r["status"], r["reason"], ""])
print("\nSaved eval/real_review.csv")