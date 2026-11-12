"""LLM judge (Gemini free tier) with caching and retry."""
import os, json, time, hashlib
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()
MODELS = [m.strip() for m in os.getenv(
    "GEMINI_MODELS", "gemini-3.8-flash").split(",")]
CACHE = Path("llm_cache.json")
_cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
_client = None


def judge(claim: str, evidence: list[str]) -> tuple[str, str] | None:
    key = hashlib.md5((claim + "|".join(evidence)).encode()).hexdigest()
    if key in _cache:
        return tuple(_cache[key])
    global _client
    _client = _client or genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"timeout": 15000})
    src = "\n".join(f"- {e}" for e in evidence)
    prompt = (
        "You are a strict fact-checking assistant. Using ONLY the source excerpts, "
        "judge the claim.\n"
        "Supported = every fact in the claim is stated in the sources.\n"
        "Contradicted = the sources state something that conflicts with the claim.\n"
        "Unsupported = the claim contains facts not found in the sources.\n"
        'Reply as JSON: {"verdict": "Supported|Contradicted|Unsupported", '
        '"reason": "one short sentence"}\n\n'
        f"SOURCES:\n{src}\n\nCLAIM: {claim}")
    for attempt in range(2):
        model = MODELS[attempt % len(MODELS)]
        try:
            r = _client.models.generate_content(
                model=model, contents=prompt,
                config={"response_mime_type": "application/json"})
            raw_text = r.text if r.text is not None else "{}"
            d = json.loads(raw_text)
            if not isinstance(d, dict):
                d = {}
            candidate = d.get("verdict")
            v = candidate if isinstance(candidate, str) and candidate in ("Supported", "Contradicted", "Unsupported") else "Unsupported"
            reason = d.get("reason", "")
            out = (v, "Gemini: " + (reason if isinstance(reason, str) else ""))
            _cache[key] = list(out)
            CACHE.write_text(json.dumps(_cache))
            time.sleep(2)  # stay under free-tier rate limits
            return out
        except Exception as e:
            print("Gemini error:", repr(e)[:300])
            time.sleep(3 * (attempt + 1))
    return None