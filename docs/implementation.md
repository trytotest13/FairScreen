# Implementation: FairScreen

## Phase 1: Setup

- T1.1: `.gitignore`, `.env.example`, `requirements.txt`, `README.md`.
  Acceptance: env/data paths untracked.
- T1.2: `config.py` validation with cutoff clamp.
  Acceptance: non-integer cutoff raises a readable error.

## Phase 2: Parsing and matching

- T2.1: `parsing.py`: txt/md/pdf/docx extractors.
  Acceptance: txt round-trips; unsupported type raises with supported list.
- T2.2: `matching.py`: skills lexicon + extraction, TF-IDF cosine, score components, gap list.
  Acceptance: a resume containing 4 of 5 JD skills gets coverage 0.8; identical text scores similarity 1.0.
- T2.3: Semantic engine behind env flag with graceful fallback.
  Acceptance: with the model unavailable, ranking returns TF-IDF scores and the caller can detect the fallback.

## Phase 3: Bias tooling

- T3.1: `bias.py`: PII redaction (email/phone/URL/name line) + proxy detection (graduation year, pronouns, address).
  Acceptance: every category strips cleanly on the fixture texts; redacted text contains none of the patterns.
- T3.2: `bias.py`: four-fifths audit.
  Acceptance: unit tests cover a passing case (ratio >= 0.8) and a flagged case (ratio < 0.8) with exact arithmetic.
- T3.3: `sample_data/generate.py`: 24 deterministic synthetic resumes + metadata.csv.
  Acceptance: same seed twice produces identical files; metadata covers two groups with unequal counts.

## Phase 4: App and delivery

- T4.1: `app.py` with ranking, detail, audit tabs and all four design states.
  Acceptance: boots offline; fixture ranking shows components and gaps; audit renders the arithmetic.
- T4.2: CSV export button writes the schema contract columns.
- T4.3: Tests green, git init, secret scan, initial commit.
