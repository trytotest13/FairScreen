from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+|linkedin\.com/\S+|github\.com/\S+")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
PRONOUN_RE = re.compile(r"\b(he|she|his|her|him)\b", re.IGNORECASE)
ADDRESS_RE = re.compile(r"\b\d{1,5}\s+\w+(\s\w+)*\s+(street|st|avenue|ave|road|rd|lane|ln|blvd|boulevard)\b", re.IGNORECASE)


@dataclass
class Redaction:
    text: str
    removed: list[str] = field(default_factory=list)


def redact(text: str) -> Redaction:
    """Remove contact PII and the name line before scoring."""
    removed: list[str] = []
    result = EMAIL_RE.sub("[email removed]", text)
    if EMAIL_RE.search(text):
        removed.append("email")
    if PHONE_RE.search(result):
        result = PHONE_RE.sub("[phone removed]", result)
        removed.append("phone")
    if URL_RE.search(result):
        result = URL_RE.sub("[link removed]", result)
        removed.append("link")

    lines = result.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped and len(stripped) <= 48 and not any(c.isdigit() for c in stripped) and "@" not in stripped:
            result = "\n".join(["[name removed]"] + lines[index + 1 :])
            removed.append("name line")
            break

    return Redaction(text=result, removed=removed)


def proxy_flags(text: str) -> list[dict]:
    """Demographic proxies detectable in text. Informational only, never penalties."""
    flags = []
    years = YEAR_RE.findall(text)
    if years:
        flags.append({"category": "graduation years", "fragment": ", ".join(sorted(set(years))[:4])})
    pronouns = PRONOUN_RE.findall(text)
    if pronouns:
        flags.append({"category": "gendered pronouns", "fragment": ", ".join(sorted({p.lower() for p in pronouns}))})
    address = ADDRESS_RE.search(text)
    if address:
        flags.append({"category": "street address", "fragment": address.group(0)})
    return flags


@dataclass
class AuditResult:
    groups: dict[str, dict]
    ratio: float
    threshold: float
    flagged: bool


def four_fifths_audit(ranked: list[dict], cutoff: int, threshold: float = 0.8) -> AuditResult | None:
    """4/5ths rule over group labels attached to ranked candidates.

    `ranked` rows need `filename` and optional `group`. Rows without a group
    are excluded from the arithmetic (the audit reports only known groups).
    """
    selected_names = {row["filename"] for row in ranked[:cutoff]}
    tally: dict[str, dict[str, int]] = {}
    for row in ranked:
        group = row.get("group")
        if not group:
            continue
        stats = tally.setdefault(group, {"n": 0, "selected": 0})
        stats["n"] += 1
        if row["filename"] in selected_names:
            stats["selected"] += 1

    if len(tally) < 2:
        return None

    groups = {
        group: {
            "n": stats["n"],
            "selected": stats["selected"],
            "rate": round(stats["selected"] / stats["n"], 4),
        }
        for group, stats in sorted(tally.items())
    }
    rates = [entry["rate"] for entry in groups.values()]
    highest = max(rates)
    ratio = round(min(rates) / highest, 4) if highest > 0 else 1.0
    return AuditResult(groups=groups, ratio=ratio, threshold=threshold, flagged=ratio < threshold)


def audit_frame(audit: AuditResult) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"group": group, "candidates": stats["n"], "selected": stats["selected"], "selection rate": stats["rate"]}
            for group, stats in audit.groups.items()
        ]
    )
