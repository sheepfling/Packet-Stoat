from __future__ import annotations

from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import report_envelope


def test_stamp_report_adds_shared_metadata() -> None:
    payload = report_envelope.stamp_report(
        {"status": "pass"},
        schema="fastdis.example.v1",
        report_path=Path("artifacts/reports/example.json"),
        producer="tools/example.py",
    )

    assert payload["schema"] == "fastdis.example.v1"
    assert "generated_at_utc" in payload
    assert payload["report_meta"]["canonical_format"] == "json"
    assert payload["report_meta"]["markdown_policy"] == "leaf-only"
    assert payload["report_meta"]["producer"] == "tools/example.py"
    assert payload["report_meta"]["report_path"] == "artifacts/reports/example.json"


def test_stamp_report_preserves_existing_generated_at_field() -> None:
    payload = report_envelope.stamp_report(
        {"generated_at": "2026-07-02T00:00:00+00:00"},
        schema="fastdis.example.v1",
        generated_at_field="generated_at",
    )

    assert payload["generated_at"] == "2026-07-02T00:00:00+00:00"
    assert payload["report_meta"]["generated_at_field"] == "generated_at"
    assert payload["report_meta"]["generated_at"] == "2026-07-02T00:00:00+00:00"
