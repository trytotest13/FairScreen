# Rules: FairScreen

## Python standards

- Python 3.11+. Type hints on public functions; `from __future__ import annotations`.
- No `Any` without justification. Modules snake_case, constants UPPER_SNAKE.
- Imports: stdlib, third-party, local; no wildcards.

## Matching conventions

- Score components are always reported with the total; a bare number is a bug.
- The skills lexicon is data at the top of `matching.py`; additions never change scoring code.
- Semantic mode is opt-in and must degrade to TF-IDF without losing the ranking.

## Bias-audit conventions

- The audit computes only on provided metadata; it never infers protected attributes from text.
- Every audit display shows the arithmetic (rates, ratio, threshold) alongside the verdict.
- Proxy flags name the category and show the matched fragment; they are informational, never penalties.
- The synthetic fixture is labeled synthetic everywhere it appears.

## Error handling

- Parse failures are per-file and non-fatal; the batch continues.
- No bare `except:`.

## Secrets (always enforced)

- Secrets live only in `.env` (gitignored); `.env.example` has names only. This project needs none.
- Before every commit, scan staged files for secret-shaped strings; if one slipped in, stop and rotate immediately.

## Design compliance

- Match `design.md` tokens; every state in design.md exists in code.
- No em dashes in user-facing copy; the "supports human review" disclaimer appears on ranking and audit screens.

## Project conventions

- `pytest -q` passes fully offline (TF-IDF path).
- Update `docs/todo.md` after every completed task without being asked.
