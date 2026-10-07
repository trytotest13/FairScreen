# Architecture: FairScreen

## Directory tree

```
05-fairscreen-resume/
├── fairscreen/
│   ├── __init__.py
│   ├── config.py     # env parsing + clamps
│   ├── parsing.py    # pdf/docx/txt -> text
│   ├── matching.py   # lexicon, similarity, score components, gaps
│   ├── bias.py       # redaction, proxy flags, four-fifths audit
│   └── app.py        # Streamlit screener
├── sample_data/
│   └── generate.py   # synthetic fixture (24 resumes + metadata.csv)
├── tests/test_core.py
└── docs/
```

## Data flow

```
upload/generate ──> parsing.extract ──> bias.redact (toggle) ──> matching.rank
                                                                      │
JD paste ──> matching.extract_skills(jd) ─────────────────────────────┤
                                                                      ├──> ranked table (scores + components + gaps)
                                                                      └──> bias.audit(ranked + metadata) ──> 4/5ths table + flag
                                                                                      │
                                                                                      └──> export CSV
```

## Component hierarchy (Streamlit)

```
app.py
├── sidebar: load fixture / upload resumes, JD textarea, redaction toggle, embeddings badge
├── main tabs:
│   ├── Ranking: table (rank, candidate, score, text sim, skill coverage, top gaps) + disclaimer
│   ├── Candidate detail: full text (redacted if on), proxy flags, missing skills
│   └── Bias audit: selection-rate table, disparity ratio, flag banner, explanation of the rule
└── states: no resumes, no JD, parse error per file, embeddings-unavailable notice
```

## Rendering strategy

Ranking recomputes on demand (button + on JD edit) and is cached in
session_state; the audit reads the last ranking. No background jobs.

## Third-party service boundaries

| Service | When contacted | Failure handling |
|---|---|---|
| HuggingFace hub | first semantic-mode run (one-time ~90 MB) | warning banner, TF-IDF fallback, ranking continues |
| nothing else | | fully offline |
