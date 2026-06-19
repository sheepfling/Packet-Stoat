from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_orientation_report


def test_build_summary_has_expected_sections() -> None:
    summary = run_orientation_report.build_summary()
    assert summary["status"] == "passed"
    assert summary["golden_fixture"]["schema"] == "fastdis.orientation_golden_cases.v1"
    assert summary["engine_fixture"]["schema"] == "fastdis.orientation_engine_cases.v1"
    assert summary["golden_fixture"]["case_count"] > 0
    assert summary["engine_fixture"]["case_count"] > 0
    assert summary["randomized_properties"]["iterations"] == run_orientation_report.RANDOM_ITERATIONS


def test_main_writes_reports_to_custom_output_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_orientation_report.py", "--output-dir", str(tmp_path)])
    rc = run_orientation_report.main()
    assert rc == 0

    json_path = tmp_path / "orientation_verification_report.json"
    md_path = tmp_path / "orientation_verification_report.md"
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert "shared orientation fixtures" in md_path.read_text(encoding="utf-8")
