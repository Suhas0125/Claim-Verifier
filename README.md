# Claim Verifier

A reviewer assistant that checks every claim in an AI-drafted memo against source documents, flags unsupported or contradicted claims with evidence, and logs each human decision.

**Why:** AI agents now draft work papers and reports quickly, but reviewers still need to confirm that each claim is backed by the sources. Manual checking eats the time savings and risks missed errors. This prototype makes that review faster and more traceable, with the human making the final call.

**User:** an audit or consulting reviewer.
**Success metrics:** precision and recall on planted errors; reviewer override rate.

## Pipeline

Draft memo -> claim extraction -> hybrid retrieval (BM25 + embeddings, RRF) -> NLI model (DeBERTa) + rule checks (numbers, dates, polarity) -> verdict + evidence -> reviewer Agree/Override -> SQLite audit log

Everything runs locally: no API keys and no client data leaving the machine.

## Results

17-claim dev set (rules were tuned on it) and 17-claim held-out set (not tuned on).

| Dataset | Setup | Precision | Recall | F1 |
|---|---|---|---|---|
| dev | dense only | 1.00 | 0.86 | 0.92 |
| dev | hybrid | 1.00 | 0.86 | 0.92 |
| dev | hybrid + rules | 1.00 | 1.00 | 1.00 |
| held-out | dense only | 0.88 | 1.00 | 0.93 |
| held-out | hybrid | 0.88 | 1.00 | 0.93 |
| held-out | hybrid + rules | 0.88 | 1.00 | 0.93 |

Note: the dev set has 15 claims, the held-out set has 17. Update the heading if you prefer exact counts.

**Takeaways**
- Hybrid retrieval cut false alarms vs dense-only on the held-out set.
- Rules fixed the NLI model's weakness on negation prefixes (qualified vs unqualified) on the dev set. They added nothing on the held-out set, where NLI already caught every error.

## Limitations (honest)
- Tiny, synthetic, single-domain data; one claim changes a metric by about 0.1. Results are suggestive, not statistically meaningful.
- The held-out set was written by the same author as the system.
- One held-out false alarm: the claim added "at year end", which the source doesn't state. Arguably a correct flag, left unfixed to keep the set held-out.
- Rule-based claim extraction drops subjects in some split clauses.
- Polarity checks use a small hand-built word list.
- Fabricated citations and unsupported claims are caught only through the number checks and low entailment scores; retrieval can't flag them by itself.

## Next steps
Per-chunk number checks, an LLM-based claim extractor, calibration analysis of confidence scores, real documents (PDF ingestion), and stakeholder testing with real reviewers.

## Run
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m eval.evaluate
python -m streamlit run app.py
```