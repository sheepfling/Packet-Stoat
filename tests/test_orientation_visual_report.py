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
    monkeypatch.setattr(
        run_orientation_visual_report,
        "build_projection_review",
        lambda **kwargs: {
            "engine": kwargs["config_path"].stem.split("_")[0],
            "label": kwargs["label"],
            "status": "expected-fail-observed" if kwargs["label"] == "known_bad" else "passed",
            "expected_result": "fail" if kwargs["label"] == "known_bad" else "pass",
            "observed_projection_pass": False if kwargs["label"] == "known_bad" else True,
            "notes": [],
            "summary": {"image_count": 3, "pass_count": 3, "max_projection_error_px": 0.0},
            "report_path": "verification_reports/alpha2_sample/projection.json",
            "config_path": "configs/orientation/example.yaml",
            "config_hash": "sha256:test",
            "config": {"target_frame": {"engine": "test"}},
        },
    )
    monkeypatch.setattr(
        run_orientation_visual_report.generate_orientation_contact_sheet,
        "run_from_namespace",
        lambda args: (Path(args.out).parent.mkdir(parents=True, exist_ok=True), Path(args.out).write_text("<html></html>", encoding="utf-8"), 0)[2],
    )
    monkeypatch.setattr(sys, "argv", ["run_orientation_visual_report.py", "--out-dir", str(tmp_path)])
    rc = run_orientation_visual_report.main()
    assert rc == 0
    payload = json.loads((tmp_path / "orientation_visual_report.json").read_text(encoding="utf-8"))
    assert payload["lanes"]["unreal"]["5.8"]["status"] == "passed"
    assert payload["unreal_engine_versions"] == ["5.8"]
    assert len(payload["projection_reviews"]) == 4
    assert payload["projection_reviews"][2]["status"] == "expected-fail-observed"
    assert "config_snapshots" in payload
    assert "Orientation Visual Report" in (tmp_path / "orientation_visual_report.md").read_text(encoding="utf-8")


def test_main_supports_multiple_unreal_versions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_orientation_visual_report,
        "run_unreal_lane",
        lambda engine_version, out_dir: {
            "status": "passed",
            "returncode": 0,
            "command": ["unreal", engine_version],
            "notes": [],
            "events": [],
            "summary": {"event_count": 1, "case_count": 1, "failure_count": 0, "max_angle_deg": 0.0, "min_dot": 1.0},
            "raw_output_path": f"verification_reports/alpha2_sample/unreal_visual_{engine_version}.log",
            "harness_log_path": f"verification_reports/alpha2_sample/unreal_visual_harness_{engine_version}.log",
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
    monkeypatch.setattr(
        run_orientation_visual_report,
        "build_projection_review",
        lambda **kwargs: {
            "engine": kwargs["config_path"].stem.split("_")[0],
            "label": kwargs["label"],
            "status": "expected-fail-observed" if kwargs["label"] == "known_bad" else "passed",
            "expected_result": "fail" if kwargs["label"] == "known_bad" else "pass",
            "observed_projection_pass": False if kwargs["label"] == "known_bad" else True,
            "notes": [],
            "summary": {"image_count": 3, "pass_count": 3, "max_projection_error_px": 0.0},
            "report_path": "verification_reports/alpha2_sample/projection.json",
            "config_path": "configs/orientation/example.yaml",
            "config_hash": "sha256:test",
            "config": {"target_frame": {"engine": "test"}},
        },
    )
    monkeypatch.setattr(
        run_orientation_visual_report.generate_orientation_contact_sheet,
        "run_from_namespace",
        lambda args: (Path(args.out).parent.mkdir(parents=True, exist_ok=True), Path(args.out).write_text("<html></html>", encoding="utf-8"), 0)[2],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_orientation_visual_report.py",
            "--out-dir",
            str(tmp_path),
            "--engine-version",
            "5.7",
            "--engine-version",
            "5.8",
        ],
    )
    rc = run_orientation_visual_report.main()
    assert rc == 0
    payload = json.loads((tmp_path / "orientation_visual_report.json").read_text(encoding="utf-8"))
    assert payload["unreal_engine_versions"] == ["5.7", "5.8"]
    assert payload["lanes"]["unreal"]["5.7"]["status"] == "passed"
    assert payload["lanes"]["unreal"]["5.8"]["status"] == "passed"
    markdown = (tmp_path / "orientation_visual_report.md").read_text(encoding="utf-8")
    assert "| unreal-5.7 | passed | 1 | 0.00000000 | 1.00000000 | none |" in markdown
    assert "| unreal-5.8 | passed | 1 | 0.00000000 | 1.00000000 | none |" in markdown
    assert "| unreal/good | passed | 3 | 0.000 | none |" in markdown
    assert "| unreal/known_bad | expected-fail-observed | 3 | 0.000 | none |" in markdown
