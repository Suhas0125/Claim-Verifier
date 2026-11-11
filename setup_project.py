from pathlib import Path

FILES = {}

FILES[".gitignore"] = """__pycache__/
.venv/
.env
*.db
"""

FILES["requirements.txt"] = """anthropic
sentence-transformers
rank-bm25
streamlit
pandas
numpy
pytest
python-dotenv
"""

FILES[".env"] = "ANTHROPIC_API_KEY=your_key_here\n"

FILES["data/sources/annual_summary.txt"] = """Nimbus Retail Ltd reported revenue of Rs 1,250 crore for FY2025, up from Rs 1,000 crore in FY2024, a growth of 25%.
Net profit for FY2025 was Rs 110 crore.
The company had 4,200 employees as of 31 March 2025.
Nimbus operates 85 stores across 12 states.
Long-term borrowings stood at Rs 300 crore, and Rs 50 crore was repaid during FY2025.
The largest customer, Apex Mart, accounted for 8% of revenue.
The auditor's report, dated 28 May 2025, carried an unqualified opinion.
The board approved a dividend of Rs 4 per share on 15 May 2025.
In October 2024 the company suffered one data breach affecting 12,000 records, which was reported to the regulator within 72 hours.
The company complies with the Companies Act 2013 and Ind AS.
The company spent Rs 90 crore in capital expenditure on warehouse automation in Hyderabad.
"""

FILES["data/sources/vendor_contract.txt"] = """The vendor, SwiftLogix, is engaged for a term of 3 years starting 1 April 2024.
The annual fee payable to SwiftLogix is Rs 12 crore.
Termination of this agreement requires 90 days written notice.
A late-delivery penalty of 2% per week applies, capped at 10% of the annual fee.
"""

FILES["data/draft_memo.txt"] = """Nimbus Retail reported FY2025 revenue of Rs 1,250 crore, up 25% from the prior year. Net profit was Rs 130 crore. The company had 4,200 employees at year end. It operates 85 stores in 15 states. Borrowings of Rs 50 crore were repaid during the year, and Apex Mart remains a key customer at 8% of revenue.
The auditor issued a qualified opinion. The board approved a dividend of Rs 4 per share on 15 June 2025.
In October 2024 a breach affected 12,000 records and was reported to the regulator within 72 hours. The company complies with the Companies Act 2013 and Ind AS, and invested Rs 90 crore in Hyderabad warehouse automation.
Under the SwiftLogix contract, the company pays Rs 12 crore per year for 3 years, and termination requires 60 days notice. Regulatory Circular CYB/2024/17 requires cyber incidents to be disclosed within 24 hours. Management expects FY2026 revenue of Rs 1,600 crore.
"""

FILES["data/answer_key.csv"] = """id,claim,label,error_type
1,Revenue was Rs 1250 crore up 25%,correct,
2,Net profit was Rs 130 crore,error,wrong_number
3,4200 employees,correct,
4,85 stores in 15 states,error,wrong_number
5,Rs 50 crore borrowings repaid,correct,
6,Apex Mart is 8% of revenue,correct,
7,Auditor issued a qualified opinion,error,contradicted
8,Dividend approved on 15 June 2025,error,wrong_date
9,Breach 12000 records reported within 72 hours,correct,
10,Complies with Companies Act 2013 and Ind AS,correct,
11,Rs 90 crore capex Hyderabad warehouse automation,correct,
12,SwiftLogix 3 years at Rs 12 crore per year,correct,
13,Termination needs 60 days notice,error,wrong_number
14,Circular CYB/2024/17 requires disclosure within 24 hours,error,fabricated_citation
15,FY2026 revenue expected Rs 1600 crore,error,unsupported
"""

FILES["src/ingest.py"] = '''"""Load source documents and split them into sentence-level chunks."""
import re
from pathlib import Path


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def load_chunks(source_dir: str = "data/sources") -> list[dict]:
    """Return a list of {id, source, text} chunks, one per sentence."""
    chunks = []
    for path in sorted(Path(source_dir).glob("*.txt")):
        for i, sent in enumerate(split_sentences(path.read_text(encoding="utf-8"))):
            chunks.append({"id": f"{path.stem}-{i}", "source": path.name, "text": sent})
    return chunks


if __name__ == "__main__":
    data = load_chunks()
    print(f"{len(data)} chunks loaded")
    for c in data[:3]:
        print(c)
'''

for empty in ["src/__init__.py", "README.md", "app.py", "src/retrieve.py",
              "src/extract.py", "src/rules.py", "src/verify.py", "src/log.py",
              "eval/evaluate.py", "tests/test_rules.py"]:
    FILES[empty] = ""

for name, content in FILES.items():
    p = Path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8", newline="\n")
    print("created", name)