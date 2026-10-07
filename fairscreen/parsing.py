from __future__ import annotations

from pathlib import Path

import fitz
from docx import Document as DocxDocument

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"Unsupported type {suffix!r}. Supported: {sorted(SUPPORTED)}")
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    return _extract_plain(path)


def _extract_pdf(path: Path) -> str:
    pages: list[str] = []
    with fitz.open(path) as doc:
        for page in doc:
            pages.append(page.get_text("text").strip())
    return "\n\n".join(p for p in pages if p).strip()


def _extract_docx(path: Path) -> str:
    document = DocxDocument(path)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()


def _extract_plain(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()
