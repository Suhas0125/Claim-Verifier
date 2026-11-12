import streamlit as st
from pathlib import Path
from src.ingest import load_chunks
from src.extract import extract_claims
from src.verify import Verifier, NLI_MODEL
from src import log
from src.risk import risk_score
import tempfile, hashlib

st.set_page_config(page_title="Claim Verifier", layout="wide")
log.init_db()

ICON = {"Supported": "🟢", "Contradicted": "🔴", "Unsupported": "🟠", "Partial": "🟡"}


@st.cache_resource
def get_verifier(source_dir):
    return Verifier(load_chunks(source_dir))


def save_uploads(files):
    h = hashlib.md5(b"".join(f.getvalue() for f in files)).hexdigest()[:10]
    d = Path(tempfile.gettempdir()) / f"cv_{h}"
    d.mkdir(exist_ok=True)
    for f in files:
        (d / f.name).write_bytes(f.getvalue())
    return str(d)


st.title("Claim Verifier")
st.caption("Checks every claim in an AI-drafted memo against source documents. "
           "The reviewer makes the final call.")

# ---- sidebar ----
with st.sidebar:
    st.header("Settings")
    sample = st.selectbox("Sample memo", ["Dev memo", "Held-out memo",
                                          "Real document demo", "Upload my own"])
    uploaded = []
    if sample == "Upload my own":
        uploaded = st.file_uploader("Source documents (PDF or TXT)",
                                    type=["pdf", "txt"], accept_multiple_files=True)
        
    mode = st.selectbox("Retrieval", ["hybrid", "dense"])
    use_rules = st.checkbox("Rule checks (numbers, dates, polarity)", value=True)

if sample == "Upload my own":
    SRC_DIR = save_uploads(uploaded) if uploaded else None
elif sample == "Real document demo":
    SRC_DIR = "data/real/sources"
else:
    SRC_DIR = "data/sources"

if sample == "Upload my own":
    memo = st.text_area("Paste the draft to check", height=200)
else:
    path = {"Dev memo": "data/draft_memo.txt",
            "Held-out memo": "data/draft_memo2.txt",
            "Real document demo": "data/real/draft.txt"}[sample]
    memo = Path(path).read_text(encoding="utf-8")
    st.text_area("Draft memo", memo, height=200, disabled=True)


tab_review, tab_log = st.tabs(["Review", "Audit log"])

# ---- review ----
with tab_review:
    if st.button("Verify draft", type="primary"):
        if not memo.strip() or SRC_DIR is None:
            st.warning("Upload source documents and paste a draft first.")
        else:
            v = get_verifier(SRC_DIR)
            v.mode, v.use_rules = mode, use_rules
            claims = extract_claims(memo)
            with st.spinner("Verifying claims..."):
                res = [v.verify(c["text"]) for c in claims]
                st.session_state.results = [{**r, "risk": risk_score(r)} for r in res]
            st.session_state.decided = {}

    results = st.session_state.get("results") or []
    if results:
        flagged = sum(r["status"] != "Supported" for r in results)
        c1, c2, c3 = st.columns(3)
        c1.metric("Claims", len(results))
        c2.metric("Flagged", flagged)
        c3.metric("Reviewed", len(st.session_state.decided))

        only_flagged = st.checkbox("Show only flagged claims")
        by_risk = st.checkbox("Sort by risk (riskiest first)", value=True)
        order = (sorted(range(len(results)), key=lambda i: -results[i]["risk"])
                 if by_risk else list(range(len(results))))
        
        for i in order:
            r = results[i]
            if only_flagged and r["status"] == "Supported":
                continue
            with st.container(border=True):
                st.markdown(f"{ICON[r['status']]} **{r['status']}** "
                    f"(confidence {r['confidence']:.2f}, risk {r['risk']:.2f})")
                st.write(r["claim"])
                st.caption(f"Why: {r['reason']}")
                st.markdown(f"> **Closest evidence** ({r['source']}): {r['evidence']}")
                done = st.session_state.decided.get(i)
                if done:
                    st.success(f"Logged: {done}")
                else:
                    a, b, _ = st.columns([1, 1, 4])
                    model_v = f"{NLI_MODEL} | {mode} | rules={use_rules}"
                    if a.button("Agree with verdict", key=f"a{i}"):
                        log.log_decision(r, "agree", model_v)
                        st.session_state.decided[i] = "agree"
                        st.rerun()
                    if b.button("Override", key=f"o{i}"):
                        log.log_decision(r, "override", model_v)
                        st.session_state.decided[i] = "override"
                        st.rerun()

# ---- audit log ----
with tab_log:
    df = log.load_decisions()
    if df.empty:
        st.info("No decisions logged yet.")
    else:
        n_over = (df["decision"] == "override").sum()
        st.metric("Override rate (proxy for model error)",
                  f"{n_over / len(df):.0%}", f"{n_over} of {len(df)} decisions")
        st.dataframe(df, use_container_width=True)
        st.download_button("Export CSV", df.to_csv(index=False),
                           "audit_log.csv", "text/csv")