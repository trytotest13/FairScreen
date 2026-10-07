from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from fairscreen.bias import audit_frame, four_fifths_audit, proxy_flags, redact
from fairscreen.config import load_config
from fairscreen.matching import extract_skills, rank
from fairscreen.parsing import SUPPORTED, extract_text

st.set_page_config(page_title="FairScreen", page_icon=None)
cfg = load_config()

DISCLAIMER = "Scores support human review. They do not decide hires."
FIXTURE_JD = (
    "Data Analyst, Growth Team. Own reporting and experiments for the growth team. "
    "Build Tableau dashboards, write SQL and Python (pandas) analysis, design A/B tests "
    "with statistical rigor, work with the data warehouse (Snowflake or BigQuery), "
    "and analyze funnels in Google Analytics."
)

st.title("FairScreen")
st.caption("Rank resumes against one job description, with PII redaction and a 4/5ths adverse-impact audit on the shortlist.")


def extract_text_from_bytes(data: bytes, suffix: str) -> str:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    try:
        return extract_text(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

# ---------------- sidebar: inputs ----------------
with st.sidebar:
    st.header("Candidates")
    source = st.radio("Source", ["Demo fixture (synthetic)", "Upload files"])
    resumes: list[tuple[str, str]] = []
    metadata: dict[str, str] = {}

    if source.startswith("Demo"):
        if not cfg.fixture_dir.exists():
            st.info("Fixture not generated yet. Run: python sample_data/generate.py")
        else:
            for path in sorted((cfg.fixture_dir / "resumes").glob("*.txt")):
                resumes.append((path.name, path.read_text(encoding="utf-8")))
            meta_path = cfg.fixture_dir / "metadata.csv"
            if meta_path.exists():
                frame = pd.read_csv(meta_path)
                metadata = dict(zip(frame["filename"], frame["group"]))
            st.caption(f"{len(resumes)} synthetic resumes loaded. Names, universities and skills are generated.")

    else:
        uploads = st.file_uploader("Resumes (PDF, DOCX, TXT)", type=["pdf", "docx", "txt", "md"], accept_multiple_files=True)
        for upload in uploads or []:
            try:
                suffix = Path(upload.name).suffix.lower()
                if suffix not in SUPPORTED:
                    raise ValueError(f"Unsupported type {suffix}")
                resumes.append((upload.name, extract_text_from_bytes(upload.getvalue(), suffix)))
            except Exception as exc:
                st.error(f"{upload.name}: {exc}")
        group_csv = st.file_uploader("Optional group metadata CSV (filename, group)", type=["csv"])
        if group_csv is not None:
            frame = pd.read_csv(group_csv)
            if {"filename", "group"}.issubset(frame.columns):
                metadata = dict(zip(frame["filename"], frame["group"]))
            else:
                st.error("Metadata CSV needs 'filename' and 'group' columns")

    redact_on = st.toggle("Redact PII before scoring", value=True)
    use_semantic = st.toggle(
        "Semantic matching (slower, downloads a model once)",
        value=cfg.embeddings_enabled,
        help="Off uses TF-IDF only: fully offline and instant",
    )

    st.header("Job description")
    jd = st.text_area("Paste the job description", value=FIXTURE_JD, height=240)
    run = st.button("Rank candidates", type="primary", use_container_width=True)

st.subheader("Ranked candidates")
st.caption(DISCLAIMER)

if run or "ranking" in st.session_state:
    if run:
        if not resumes:
            st.warning("No candidates loaded. Use the demo fixture or upload files.")
            st.stop()
        if not jd.strip():
            st.warning("Paste a job description first.")
            st.stop()

        prepared: list[tuple[str, str]] = []
        redactions: dict[str, list[str]] = {}
        for filename, text in resumes:
            if redact_on:
                result = redact(text)
                redactions[filename] = result.removed
                prepared.append((filename, result.text))
            else:
                prepared.append((filename, text))

        with st.spinner("Scoring"):
            results, engine = rank(jd, prepared, use_semantic=use_semantic)

        ranked_rows = []
        for position, result in enumerate(results, start=1):
            ranked_rows.append(
                {
                    "rank": position,
                    "filename": result.filename,
                    "candidate": metadata.get(result.filename, result.filename),
                    "group": metadata.get(result.filename),
                    "score": result.score,
                    "text similarity": result.text_similarity,
                    "skill coverage": result.skill_coverage,
                    "gaps": ", ".join(result.gaps) or "none",
                    "redactions": ", ".join(redactions.get(result.filename, [])) or "none",
                }
            )
        st.session_state["ranking"] = ranked_rows
        st.session_state["engine"] = engine
        st.session_state["prepared"] = dict(prepared)
        st.session_state["results_by_name"] = {r.filename: r for r in results}
        st.session_state["jd_skill_count"] = len(results[0].jd_skills) if results else 0

    ranked_rows = st.session_state.get("ranking", [])
    if not ranked_rows:
        st.stop()

    st.markdown(
        f"Match engine: **{st.session_state.get('engine', 'tfidf')}** · "
        f"JD skills detected: {st.session_state.get('jd_skill_count', 0)}"
    )

    tab_rank, tab_detail, tab_audit, tab_export = st.tabs(["Ranking", "Candidate detail", "Bias audit", "Export"])

    with tab_rank:
        frame = pd.DataFrame(ranked_rows)
        st.dataframe(
            frame[["rank", "candidate", "score", "text similarity", "skill coverage", "gaps"]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(DISCLAIMER)

    with tab_detail:
        pick = st.selectbox("Candidate", [row["filename"] for row in ranked_rows])
        result = st.session_state["results_by_name"][pick]
        scored_text = st.session_state["prepared"][pick]
        st.markdown(f"**Score {result.score:.3f}** = 0.6 × {result.text_similarity:.3f} (text) + 0.4 × {result.skill_coverage:.2f} (skills)")
        st.markdown(f"**Missing skills:** {', '.join(result.gaps) or 'none'}")
        flags = proxy_flags(scored_text)
        if flags:
            st.markdown("**Demographic proxies found in the text (informational, not penalties):**")
            for flag in flags:
                st.markdown(f"- {flag['category']}: {flag['fragment']}")
        else:
            st.markdown("**Demographic proxies found in the text:** none")
        st.text_area("Text as scored", value=scored_text, height=420)

    with tab_audit:
        audit = four_fifths_audit(ranked_rows, cutoff=cfg.cutoff)
        st.caption(
            f"4/5ths rule at selection cutoff {cfg.cutoff}: the least-selected group's rate "
            "must be at least 80 percent of the most-selected group's rate. This is a screening "
            "heuristic that flags disparity for human investigation, not a legal verdict."
        )
        if audit is None:
            st.info("No group metadata available, so there is nothing to audit. The demo fixture ships with group labels; uploads can attach them via a CSV.")
        else:
            if audit.flagged:
                st.error(f"Disparity flagged: ratio {audit.ratio:.2f} is below {audit.threshold:.2f}. Investigate before acting on this shortlist.")
            else:
                st.success(f"No disparity flagged: ratio {audit.ratio:.2f} meets the {audit.threshold:.2f} threshold.")
            st.dataframe(audit_frame(audit), use_container_width=True, hide_index=True)
            st.caption(DISCLAIMER)

    with tab_export:
        export_frame = pd.DataFrame(ranked_rows)[
            ["rank", "filename", "group", "score", "text similarity", "skill coverage", "gaps", "redactions"]
        ]
        st.download_button(
            "Download shortlist CSV",
            export_frame.to_csv(index=False).encode("utf-8"),
            file_name="fairscreen_shortlist.csv",
            mime="text/csv",
        )
else:
    st.info("Load candidates and a job description in the sidebar, then press Rank candidates.")
