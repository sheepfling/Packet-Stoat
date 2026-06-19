from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_orientation_visual_report


def test_parse_scene_events_extracts_case_level_metrics() -> None:
    text = (
        "FASTDIS_ORIENTATION_SCENE case=level_north status=PASS "
        "forward_angle_deg=0.00000100 forward_dot=1.00000000 "
        "right_angle_deg=0.00000200 right_dot=0.99999999 "
        "up_angle_deg=0.00000300 up_dot=0.99999998 threshold_deg=0.01000000"
    )
    events = run_orientation_visual_report.parse_scene_events(text)
    assert len(events) == 1
    assert events[0]["case"] == "level_north"
    assert events[0]["status"] == "pass"
    assert events[0]["up_angle_deg"] == 3e-06


def test_summarize_scene_events_reports_extrema() -> None:
    summary = run_orientation_visual_report.summarize_scene_events(
        [
            {
                "case": "a",
                "status": "pass",
                "forward_angle_deg": 0.1,
                "forward_dot": 0.99,
                "right_angle_deg": 0.2,
                "right_dot": 0.98,
                "up_angle_deg": 0.3,
                "up_dot": 0.97,
                "threshold_deg": 0.5,
            }
        ]
    )
    assert summary["case_count"] == 1
    assert summary["max_angle_deg"] == 0.3
    assert summary["min_dot"] == 0.97


def test_main_writes_reports_from_stubbed_lanes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_orientation_visual_report,
        "run_unreal_lane",
        lambda engine_version, out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["unreal"],
            "notes": [],
            "events": [],
            "summary": {"event_count": 1, "case_count": 1, "failure_count": 0, "max_angle_deg": 0.0, "min_dot": 1.0},
            "raw_output_path": "verification_reports/alpha2_sample/unreal_visual.log",
            "harness_log_path": "verification_reports/alpha2_sample/unreal_visual_harness.log",
        },
    )
    monkeypatch.setattr(
        run_orientation_visual_report,
        "run_godot_lane",
        lambda out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["godot"],
            "notes": [],
            "events": [],
            "summary": {"event_count": 1, "case_count": 1, "failure_count": 0, "max_angle_deg": 0.0, "min_dot": 1.0},
            "raw_output_path": "verification_reports/alpha2_sample/godot_visual.log",
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_orientation_visual_report.py", "--out-dir", str(tmp_path)])
    rc = run_orientation_visual_report.main()
    assert rc == 0
    payload = json.loads((tmp_path / "orientation_visual_report.json").read_text(encoding="utf-8"))
    assert payload["lanes"]["unreal"]["status"] == "passed"
    assert "Orientation Visual Report" in (tmp_path / "orientation_visual_report.md").read_text(encoding="utf-8")
