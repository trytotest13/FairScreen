# FairScreen

Resume screener for a single job description: rank candidates by match score,
show the skill gaps behind every score, redact identifying details on request,
and run a 4/5ths-rule adverse-impact audit on the resulting shortlist. The
audit measures the ranking you just produced and flags disparity for
investigation.

## What it does

- Parses PDF, DOCX and TXT resumes (page-aware for PDF)
- Matches against a pasted job description with a hybrid score: TF-IDF cosine (always, offline) plus optional sentence-transformer embeddings (`FAIRSCREEN_EMBEDDINGS=on`)
- Extracts skills from both sides with a curated tech lexicon and lists what each candidate is missing
- PII redaction mode: strips emails, phones, URLs and the name line before ranking
- Flags demographic proxies in resume text: graduation years, gendered pronouns, address blocks
- Adverse-impact audit: selection rates per group on the synthetic fixture (or any set with metadata), 4/5ths rule flag, shown next to the ranking
- Exports the ranked shortlist with score components to CSV

## Quick start

```bash
pip install -r requirements.txt

# 1. Generate the synthetic candidate fixture (24 resumes, labeled metadata)
python sample_data/generate.py

# 2. App: load the fixture or upload your own resumes, paste the JD
streamlit run fairscreen/app.py
```

Optional better matching: set `FAIRSCREEN_EMBEDDINGS=on` (first use downloads a ~90 MB local embedding model, then runs offline).

## Honesty notes

- The bundled fixture is synthetic: names, universities and skill sets were generated, and each row carries its group labels so the audit has ground truth. Real resumes have no reliable group labels; the audit on uploaded resumes only reports what is detectable (proxies), not gender or age.
- Match scores rank candidates for human review. They do not decide hires, and the UI says so on every screen.
- The 4/5ths rule is a screening heuristic from US employment law practice, not a verdict. It flags disparity for human investigation.

## Layout

```
fairscreen/
├── config.py      # env config
├── parsing.py     # pdf/docx/txt extraction
├── matching.py    # skills lexicon, TF-IDF + optional embeddings, gap analysis
├── bias.py        # PII redaction, proxy flags, 4/5ths audit
└── app.py         # Streamlit screener
sample_data/generate.py   # synthetic fixture with ground-truth metadata
tests/
```

## Docs

Decisions in `docs/` (prd, trd, architecture, design, schema, implementation, rules); state in `docs/todo.md`.
