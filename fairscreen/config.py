from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Config:
    embeddings_enabled: bool
    cutoff: int
    fixture_dir: Path


def load_config() -> Config:
    embeddings = os.environ.get("FAIRSCREEN_EMBEDDINGS", "off").strip().lower()
    if embeddings not in ("off", "on"):
        raise RuntimeError(f"FAIRSCREEN_EMBEDDINGS must be 'off' or 'on', got {embeddings!r}")

    raw_cutoff = os.environ.get("FAIRSCREEN_CUTOFF", "8")
    try:
        cutoff = int(raw_cutoff)
    except ValueError as exc:
        raise RuntimeError(f"FAIRSCREEN_CUTOFF must be an integer, got {raw_cutoff!r}") from exc
    cutoff = max(1, min(cutoff, 100))

    return Config(
        embeddings_enabled=embeddings == "on",
        cutoff=cutoff,
        fixture_dir=ROOT / "sample_data" / "out",
    )
