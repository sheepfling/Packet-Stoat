#!/usr/bin/env python3
"""Shared helpers for canonical JSON report metadata and writes."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from artifacts import rel


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def stamp_report(
    payload: dict[str, Any],
    *,
    schema: str | None = None,
    report_path: Path | None = None,
    producer: str | None = None,
    generated_at_field: str = "generated_at_utc",
) -> dict[str, Any]:
    stamped = dict(payload)
    if schema is not None:
        stamped["schema"] = schema
    if generated_at_field not in stamped:
        stamped[generated_at_field] = utc_now()
    meta = stamped.get("report_meta")
    if not isinstance(meta, dict):
        meta = {}
    meta = dict(meta)
    meta.setdefault("canonical_format", "json")
    meta.setdefault("markdown_policy", "leaf-only")
    meta.setdefault("generated_at_field", generated_at_field)
    meta.setdefault("generated_at", str(stamped[generated_at_field]))
    if producer:
        meta.setdefault("producer", producer)
    if report_path is not None:
        meta.setdefault("report_path", rel(report_path))
    stamped["report_meta"] = meta
    return stamped


def write_json_report(
    path: Path,
    payload: dict[str, Any],
    *,
    schema: str | None = None,
    producer: str | None = None,
    generated_at_field: str = "generated_at_utc",
) -> dict[str, Any]:
    stamped = stamp_report(
        payload,
        schema=schema,
        report_path=path,
        producer=producer,
        generated_at_field=generated_at_field,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stamped, indent=2) + "\n", encoding="utf-8")
    return stamped
