# TRD: FairScreen

## Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Parsing | PyMuPDF + python-docx | | page-aware PDF, DOCX paragraphs |
| Lexical match | sklearn TfidfVectorizer + cosine_similarity | >=1.5 | offline default, inspectable |
| Semantic match | sentence-transformers all-MiniLM-L6-v2 | >=3.0 | optional, lazy-loaded, env-gated |
| Skills | curated lexicon (~70 tech skills with aliases) | | deterministic, auditable, no NER model to trust |
| Audit | pandas + the 4/5ths rule | | transparent arithmetic, testable |
| App | Streamlit + plotly | | ranking table, audit table, gap lists |
| Tests | pytest | | redaction, audit math, matching |

## Matching design

`score = 0.6 * text_similarity + 0.4 * skill_coverage` where text_similarity is
cosine (semantic embeddings when enabled, TF-IDF otherwise) and skill_coverage
is matched-JD-skills / total-JD-skills. Components are reported separately so
no score is a black box. The lexicon is data (a dict in `matching.py`),
deliberately not an NER model: recruiters can read and extend it.

## State management

Streamlit session_state holds parsed resumes, the JD, the redaction toggle and
the ranking result. Nothing persists to disk; uploaded bytes are parsed in
memory. Embedding model cached per process via `lru_cache`.

## API strategy

No HTTP API; single-user screening tool. CSV export is the integration surface.

## Environment variables

`.env.example`, names only:

- `FAIRSCREEN_EMBEDDINGS`: `off` (default) | `on`.
- `FAIRSCREEN_CUTOFF`: top-N shortlist for the audit, default 8, clamped 1..100.

No secrets in this project.

## Bias audit arithmetic (documented so it can be challenged)

For each group g with n_g candidates: selection_rate_g = selected_g / n_g at
the cutoff. disparity_ratio = min(rate) / max(rate). Flag when ratio < 0.8
(the four-fifths rule). Groups come only from attached metadata (fixture rows
carry them; an upload may supply a CSV with `filename,group`). The audit never
infers protected attributes from text; it reports proxies instead.
