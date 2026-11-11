from src.ingest import load_chunks
from src.verify import Verifier, softmax
import numpy as np

v = Verifier(load_chunks())
claims = [
    "In October 2024 a breach affected 12,000 records and was reported to the regulator within 72 hours",
    "Under the SwiftLogix contract, the company pays Rs 12 crore per year for 3 years",
]
for c in claims:
    print("\nCLAIM:", c)
    ev = v.retriever.search(c, k=3, mode="hybrid")
    p = softmax(np.array(v.nli.predict([(e["text"], c) for e in ev])))
    for e, row in zip(ev, p):
        print(f"  con={row[0]:.2f} ent={row[1]:.2f} neu={row[2]:.2f} | {e['text'][:80]}")