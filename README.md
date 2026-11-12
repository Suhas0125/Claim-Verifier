# Claim Verifier

A reviewer assistant that checks every claim in an AI-drafted memo against source documents. It flags contradicted or unsupported claims with evidence, ranks them by risk, and logs every human decision. The reviewer always makes the final call.

**Why:** AI tools draft reports faster than people can review them. This prototype does the first pass, so reviewers see the riskiest claims first. Everything runs locally, with no API key and no data leaving the machine.

**User:** an audit or consulting reviewer.

## How it works

Draft memo -> claim extraction -> hybrid retrieval (BM25 + embeddings) -> NLI model + rule checks -> verdict with evidence -> risk ranking -> reviewer Agree/Override -> SQLite audit log

| Verdict | Meaning |
|---|---|
| 🟢 Supported | Source backs the claim |
| 🔴 Contradicted | Source disagrees (e.g. different number, date, unit) |
| 🟡 Partial | Related source found, reviewer should check |
| 🟠 Unsupported | Nothing in the sources supports it |

## Setup

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The first run downloads two small models (embeddings and NLI) from Hugging Face.

## Run

```powershell
python -m streamlit run app.py      # web app
python -m eval.evaluate             # precision/recall on dev and held-out sets
python -m eval.triage               # does risk ranking find errors early?
python -m pytest tests -q           # unit tests for the rule checks
```

## Using the app

1. Pick a **Sample memo** in the sidebar, or choose **Upload my own**.
2. For your own data: upload source documents (text-based PDF or TXT) and paste the draft to check.
3. Click **Verify draft**.
4. Review the cards (riskiest first). Each shows the verdict, the reason, and the closest source sentence.
5. Click **Agree with verdict** or **Override**. Decisions appear in the **Audit log** tab, with an override rate and CSV export.

## Files

| File | What it does |
|---|---|
| `app.py` | Streamlit web app (upload, review queue, audit log) |
| `src/ingest.py` | Reads PDF/TXT, cleans text, splits into sentence chunks (plus two-sentence windows) |
| `src/extract.py` | Splits a draft into claims; handles bullets, headers, abbreviations, wrapped lines |
| `src/retrieve.py` | Finds best source chunks: dense embeddings, BM25, or hybrid (reciprocal rank fusion) |
| `src/rules.py` | Exact checks for numbers, dates, units (million vs billion) and opposite words (qualified/unqualified) |
| `src/verify.py` | Core logic: retrieval + NLI model + rules -> verdict, reason, evidence |
| `src/risk.py` | Risk score (0 to 1) used to rank the review queue |
| `src/log.py` | SQLite audit log of reviewer decisions |
| `src/llm_verify.py` | Optional Gemini judge. Not used by default and not evaluated (free API was overloaded) |
| `eval/evaluate.py` | Compares setups: dense only, hybrid, hybrid + rules |
| `eval/triage.py` | Errors found when reviewing only the top-k claims, ranked vs random |
| `tests/test_rules.py` | Unit tests for the rule checks |
| `data/` | Synthetic sources, sample memos and answer keys; `data/real/` holds the real-PDF test |

## Results

Dev set (15 claims, rules were tuned on it) and held-out set (17 claims, not tuned on):

| Dataset | Setup | Precision | Recall | F1 |
|---|---|---|---|---|
| dev | dense only | 1.00 | 0.86 | 0.92 |
| dev | hybrid | 1.00 | 0.86 | 0.92 |
| dev | hybrid + rules | 1.00 | 1.00 | 1.00 |
| held-out | dense only | 0.88 | 1.00 | 0.93 |
| held-out | hybrid | 0.88 | 1.00 | 0.93 |
| held-out | hybrid + rules | 0.88 | 1.00 | 0.93 |

- Rules lifted dev recall from 0.86 to 1.00 by catching "qualified vs unqualified", which the NLI model missed.
- Hybrid and dense retrieval tie on held-out. An earlier gap vanished when chunking changed, so with this little data the comparison is inconclusive.
- Unseen PDF test: 4 of 4 planted edits caught (including million vs billion), 2 false alarms on table rows.

### Real-document test
Source: Berkshire Hathaway 2023 shareholder letter (public PDF). Draft: a chatbot-written summary (30 claims). I checked every claim by hand: all 30 are correct, so every flag is a false alarm.

| Version | Flagged | Hard "Contradicted" | Partial |
|---|---|---|---|
| v1 | 25/30 | ~20 | n/a |
| v2 (extractor, rules, chunking, Partial verdict) | 25/30 | 2 | 15 |

Retrieval usually found the right sentence, but a small NLI model could not verify long compound claims. The fixes cut false hard contradictions from about 20 to 2 and turned most flags into "please check".

## Limitations
- Small, mostly synthetic test sets: one claim moves a metric by about 0.1. The held-out set was written by the same author as the system.
- Checks consistency with the sources, not whether the sources are true.
- Weak on tables (rows are checked as plain text), scanned PDFs (no OCR), long compound claims and heavy paraphrase.
- Derived numbers (e.g. a growth rate the draft computed) fail the number check.
- Claim extraction is rule-based and can split sentences oddly.
- Polarity check uses a small hand-built word list.

## Next steps
Table-aware parsing and OCR, an LLM verifier for hard cases, saved vector index for large documents (FAISS or pgvector), confidence calibration, and testing with real reviewers.