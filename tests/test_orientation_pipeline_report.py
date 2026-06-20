from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_orientation_pipeline_report


def test_orientation_pipeline_report_writes_outputs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_orientation_pipeline_report.py",
            "--out-dir",
            str(tmp_path),
        ],
    )
    rc = run_orientation_pipeline_report.main()
    assert rc == 0
    payload = json.loads((tmp_path / "orientation_pipeline_report.json").read_text(encoding="utf-8"))
    assert payload["good_configs"]["godot"]["pass_count"] == payload["good_configs"]["godot"]["case_count"]
    assert payload["good_configs"]["unreal"]["pass_count"] == payload["good_configs"]["unreal"]["case_count"]
    assert payload["known_bad"]["most_likely_issue"] == "asset_front_mismatch"
    assert "config" in payload["good_configs"]["godot"]
    assert "config" in payload["good_configs"]["unreal"]
    assert "config" in payload["known_bad"]
    assert (tmp_path / "orientation_pipeline_report.md").is_file()
