#!/usr/bin/env python3
"""Shared contract helpers for machine-readable proof artifacts.

FastDIS verification and aggregation tools must treat JSON as the canonical
report format. Markdown siblings are human-readable leaf outputs derived from
JSON and must not be consumed as machine inputs for proof, signoff, or
aggregation lanes.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOTS = (
    ROOT / "artifacts" / "reports",
    ROOT / "artifacts" / "verification_reports",
    ROOT / "verification_reports",
)


def is_report_markdown_path(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.suffix.lower() != ".md":
        return False
    text = candidate.as_posix().lower()
    return any(
        text == root.relative_to(ROOT).as_posix().lower()
        or text.startswith(root.relative_to(ROOT).as_posix().lower() + "/")
        or root.as_posix().lower() in text
        for root in REPORT_ROOTS
    )
