# PRD: FairScreen

## Problem

Screening resumes by hand takes hours and quietly absorbs the screener's
biases: name familiarity, university prestige, graduation-year age guesses. A
screener that ranks candidates AND audits its own shortlist for adverse impact
gives a recruiting team something defensible: scores with visible components,
skill gaps a human can verify, and a disparity flag they can investigate.

## Target users

- **Recruiter Sameer**: 200 applications for one data-analyst role, needs a ranked shortlist with reasons in 10 minutes.
- **HR compliance lead Ana**: needs evidence that the screening process was checked for adverse impact before anyone gets rejected.

## Functional requirements

- FR-1: Parse resumes as PDF, DOCX, TXT; keep page info for PDFs.
- FR-2: Accept a pasted job description; extract its skills with the lexicon.
- FR-3: Score every resume with TF-IDF cosine similarity (offline, default) plus optional sentence-transformer embeddings enabled by env.
- FR-4: Report per-candidate score components (text similarity, skill coverage) and the concrete missing skills.
- FR-5: PII redaction toggle: remove emails, phone numbers, URLs and the name line before any scoring; show which parts were removed.
- FR-6: Flag demographic proxies present in text: graduation years, gendered pronouns, street-address patterns.
- FR-7: Adverse-impact audit on the ranked list when group metadata exists (synthetic fixture or uploaded metadata CSV): selection rate per group at a configurable cutoff, 4/5ths-rule flag, displayed beside the ranking.
- FR-8: Export the shortlist (rank, name-or-redacted, scores, components, gaps, group if known) to CSV.
- FR-9: Every screen states that scores support human review and do not decide hires.

## Non-functional requirements

- NFR-1: 50 resumes scored in under 5 s with TF-IDF on CPU.
- NFR-2: Semantic mode degrades to TF-IDF with a visible notice if the model cannot load; ranking never breaks.
- NFR-3: Redaction happens before text leaves the parsing stage; unredacted text is never rendered when redaction is on.
- NFR-4: No uploaded resume is persisted; everything lives in memory for the session.

## Out of scope

- Automatic reject/approve decisions
- ATS integrations (export CSV is the handoff)
- Legal compliance certification (the audit is a screening heuristic, the UI says exactly that)
- Multi-language resumes (English only)
