import re
from pathlib import Path
from typing import List, Dict

import streamlit as st
import pandas as pd
import pdfplumber

# --------------------------------------------------
# Configuration / Constants
# --------------------------------------------------

# Directory that contains PDF resumes *locally*.
# For simplicity we look for a sibling folder called "resumes" that sits
# inside the same backend directory (create it if it doesn't exist).
RESUME_DIR = Path(__file__).resolve().parent / "resumes"

ROLE_CONFIGS: Dict[str, Dict[str, List[str]]] = {
    "Backend engineer": {
        "must_have": ["python", "sql"],
        "nice_to_have": ["aws", "docker", "microservices"],
    },
    "Fullstack": {
        "must_have": ["javascript", "react", "node"],
        "nice_to_have": ["typescript", "aws", "docker", "graphql"],
    },
}

MUST_WEIGHT = 2.0
NICE_WEIGHT = 1.0

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def list_local_pdfs() -> List[Path]:
    """Return list of PDF file paths in RESUME_DIR."""
    if not RESUME_DIR.exists():
        return []
    return sorted(p for p in RESUME_DIR.iterdir() if p.suffix.lower() == ".pdf")


def extract_text(pdf_path: Path) -> str:
    """Extract raw text from a PDF file using pdfplumber."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        all_text = []
        for page in pdf.pages:
            txt = page.extract_text() or ""
            all_text.append(txt)
    return "\n".join(all_text)


def score_resume(text: str, role: str) -> Dict[str, float]:
    """Return dict containing hit counts and score for the given role."""
    cfg = ROLE_CONFIGS[role]
    lower_text = text.lower()
    must_hits = sum(1 for kw in cfg["must_have"] if re.search(rf"\b{re.escape(kw)}\b", lower_text))
    nice_hits = sum(1 for kw in cfg["nice_to_have"] if re.search(rf"\b{re.escape(kw)}\b", lower_text))
    total_score = MUST_WEIGHT * must_hits + NICE_WEIGHT * nice_hits
    return {"must_hits": must_hits, "nice_hits": nice_hits, "score": total_score}

# --------------------------------------------------
# Streamlit UI
# --------------------------------------------------

st.set_page_config(page_title="Candidate Scorer", layout="wide")

st.title("📄 Candidate Resume Ranking (Local Folder)")

role = st.selectbox("Select Role", list(ROLE_CONFIGS.keys()))
job_desc = st.text_area("Paste the Job Description (optional)")

if not RESUME_DIR.exists():
    st.warning(
        "No 'resumes' directory found inside backend folder. "
        "Create the folder and drop PDF files inside, then refresh this page."
    )
    st.stop()

st.markdown(f"**Scanning PDF files in:** `{RESUME_DIR}`")

rank_button = st.button("🔍 RANK")

if rank_button:
    pdf_files = list_local_pdfs()
    if not pdf_files:
        st.warning("No PDF files found in the resumes folder.")
        st.stop()

    rows = []
    progress = st.progress(0)
    for idx, pdf_path in enumerate(pdf_files, start=1):
        progress.progress(idx / len(pdf_files))
        text = extract_text(pdf_path)
        metrics = score_resume(text, role)
        rows.append(
            {
                "Candidate": pdf_path.name,
                "Score": metrics["score"],
                "Must-Have Hits": metrics["must_hits"],
                "Nice-to-Have Hits": metrics["nice_hits"],
            }
        )

    ranked = sorted(rows, key=lambda x: x["Score"], reverse=True)
    df = pd.DataFrame(ranked)

    st.success(f"Ranking complete. {len(df)} candidates processed.")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Select a role, optionally paste a job description, and click RANK.") 