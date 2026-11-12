"""Verify each claim: retrieval -> NLI model -> rule checks -> verdict."""
import numpy as np
from sentence_transformers import CrossEncoder
from src.retrieve import Retriever
from src.rules import check as rule_check, polarity_check

NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
# output order of this model: contradiction, entailment, neutral


def softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


class Verifier:
    def __init__(self, chunks, mode="hybrid", use_rules=True, k=3,
                 ent_th=0.5, con_th=0.5, use_llm=False):
        self.retriever = Retriever(chunks)
        self.all_texts = [c["text"] for c in chunks]
        self.nli = CrossEncoder(NLI_MODEL)
        self.mode, self.use_rules, self.k = mode, use_rules, k
        self.ent_th, self.con_th = ent_th, con_th
        self.use_llm = use_llm

    def verify(self, claim: str) -> dict:
        evidence = self.retriever.search(claim, k=self.k, mode=self.mode)
        texts = [e["text"] for e in evidence]
        probs = softmax(np.array(self.nli.predict([(t, claim) for t in texts])))
        joined = softmax(np.array(self.nli.predict([(" ".join(texts), claim)])))[0]
        con, ent = probs[:, 0], probs[:, 1]
        best = int(np.argmax(ent))
        ent_score = max(float(ent.max()), float(joined[1]))
        con_score = float(con[0])  # only the top-ranked sentence may contradict
        sim = float(self.retriever._dense_scores(claim).max())

        if self.use_rules:
            rules = rule_check(claim, self.all_texts)
            pol = polarity_check(claim, texts[0])
        else:
            rules = {"status": "n/a", "reason": "rules disabled"}
            pol = {"status": "pass", "reason": ""}

        if rules["status"] == "fail":
            status, reason = "Contradicted", "Rule check: " + rules["reason"]
        elif pol["status"] == "fail":
            status, reason = "Contradicted", "Polarity check: " + pol["reason"]
        elif ent_score >= self.ent_th:
            status, reason = "Supported", f"NLI entailment {ent_score:.2f}"
        elif con_score >= self.con_th:
            status, reason = "Contradicted", f"NLI contradiction {con_score:.2f}"
        elif sim >= 0.6:
            status, reason = "Partial", f"Related source found (similarity {sim:.2f}); reviewer should check"
        else:
            status, reason = "Unsupported", "No source sentence supports this claim"

        if self.use_llm and rules["status"] != "fail" and pol["status"] != "fail":
            from src.llm_verify import judge
            ev5 = [e["text"] for e in self.retriever.search(claim, k=5, mode=self.mode)]
            llm = judge(claim, ev5)
            if llm:
                status, reason = llm
            else:
                reason += " (Gemini unavailable, NLI verdict kept)"
        
        return {
            "claim": claim, "status": status, "reason": reason,
            "confidence": max(ent_score, con_score),
            "evidence": texts[best], "source": evidence[best]["source"],
        }


if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path
    from src.ingest import load_chunks
    from src.extract import extract_claims

    v = Verifier(load_chunks())
    claims = extract_claims(Path("data/draft_memo.txt").read_text(encoding="utf-8"))
    key = pd.read_csv("data/answer_key.csv")

    tp = fp = fn = tn = 0
    for c, (_, row) in zip(claims, key.iterrows()):
        r = v.verify(c["text"])
        flagged = r["status"] != "Supported"
        truth = row["label"] == "error"
        tp += flagged and truth
        fp += flagged and not truth
        fn += (not flagged) and truth
        tn += (not flagged) and not truth
        mark = "OK " if flagged == truth else "XX "
        print(f"{mark}#{c['id']:>2} {r['status']:<12} {r['reason'][:70]}")

    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    print(f"\nTP={tp} FP={fp} FN={fn} TN={tn}  precision={prec:.2f} recall={rec:.2f}")