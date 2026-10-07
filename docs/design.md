# Design: FairScreen

Streamlit app, light theme. One accent (indigo) for actions and the score bar;
semantic colors reserved for the audit flag.

## Color palette

| Token | Hex | Tailwind class | Used for |
|---|---|---|---|
| ink | #1F2937 | `text-gray-800` | text |
| muted | #6B7280 | `text-gray-500` | captions, disclaimers |
| surface | #F8FAFC | `bg-slate-50` | background |
| accent | #4338CA | `bg-indigo-700` | score bars, run button |
| flag | #B91C1C | `text-red-700` | audit flag, proxy warnings |
| ok | #15803D | `text-green-700` | clean audit result |

## Typography

System font stack. Scores in tabular numerals at 1.4rem in the detail view;
table cells regular. Gap lists as plain text chips, no icons.

## Spacing & radii

8px rhythm; 10px radius on cards; tables hairline-separated.

## Core components

- **Ranking table**: rank, candidate, match score (inline bar), text similarity, skill coverage, top 3 gaps. Score bar in accent.
- **Candidate detail**: redacted preview when on, proxy flags listed with the exact matched text, full missing-skills list.
- **Audit banner**: red "disparity flagged (ratio 0.62 < 0.8)" or green "no disparity flagged (ratio 0.95)", always with the arithmetic shown.
- **Disclaimer line**: on ranking and audit tabs: "Scores support human review. They do not decide hires."

## UI states (required)

- No resumes: instructions + "generate the demo fixture" button.
- No JD: ranking tab shows what to paste.
- Parse error: per-file inline error, other files continue.
- Embeddings unavailable: warning banner once, TF-IDF badge stays visible.

## Accessibility

Contrast: ink 15.8:1, muted 4.8:1, accent-white 7.6:1, flag 5.9:1 on white.
Audit result is text + color. No em dashes.
