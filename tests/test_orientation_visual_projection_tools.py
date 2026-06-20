from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import compare_orientation_screenshots
import generate_orientation_contact_sheet


def _compare_payload(pass_result: bool, signature: str | None = None) -> dict[str, object]:
    return {
        "target": "godot",
        "config_hash": "sha256:test",
        "config": {
            "target_frame": {"engine": "godot"},
            "asset": {"forward_axis": "negative_z", "up_axis": "positive_y"},
        },
        "results": [
            {
                "case": "level_north",
                "config_hash": "sha256:test",
                "expected_visible_basis": {
                    "forward": [0.0, 0.0, -1.0],
                    "right": [1.0, 0.0, 0.0],
                    "up": [0.0, 1.0, 0.0],
                },
                "asset_stage": {
                    "forward": [0.0, 0.0, -1.0] if pass_result else [0.0, 0.0, 1.0],
                    "right": [1.0, 0.0, 0.0] if pass_result else [-1.0, 0.0, 0.0],
                    "up": [0.0, 1.0, 0.0],
                },
                "max_axis_error_deg": 0.0 if pass_result else 180.0,
                "failure_signature": signature,
                "pass": pass_result,
            }
        ],
    }


def test_compare_orientation_screenshots_generates_projection_artifacts(tmp_path: Path) -> None:
    compare_path = tmp_path / "compare.json"
    visual_cases_path = tmp_path / "visual_cases.json"
    compare_path.write_text(json.dumps(_compare_payload(True), indent=2), encoding="utf-8")
    visual_cases_path.write_text(
        json.dumps(
            {
                "image": {"width": 320, "height": 200, "axis_scale_px": 60, "origin": [160, 120]},
                "cameras": [
                    {
                        "name": "top_down",
                        "screen_right": [0.0, 1.0, 0.0],
                        "screen_up": [1.0, 0.0, 0.0],
                    }
                ],
                "cases": ["level_north"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "review"
    rc = compare_orientation_screenshots.run_from_namespace(
        argparse.Namespace(
            compare=str(compare_path),
            visual_cases=str(visual_cases_path),
            label="good",
            out_dir=str(out_dir),
        )
    )
    assert rc == 0
    report = json.loads((out_dir / "godot_good_projection_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["pass_count"] == 1
    assert "config" in report
    assert (out_dir / "baselines" / "godot_good_level_north_top_down_expected.png").is_file()
    assert (out_dir / "renders" / "godot_good_level_north_top_down_actual.png").is_file()
    assert (out_dir / "sidecars" / "godot_good_level_north_top_down.json").is_file()


def test_compare_orientation_screenshots_fails_known_bad_projection(tmp_path: Path) -> None:
    compare_path = tmp_path / "compare.json"
    compare_path.write_text(json.dumps(_compare_payload(False, "asset_front_mismatch"), indent=2), encoding="utf-8")
    out_dir = tmp_path / "review"
    rc = compare_orientation_screenshots.run_from_namespace(
        argparse.Namespace(
            compare=str(compare_path),
            visual_cases=str(ROOT / "tests" / "data" / "orientation_visual_cases.json"),
            label="known_bad",
            out_dir=str(out_dir),
        )
    )
    assert rc == 1
    report = json.loads((out_dir / "godot_known_bad_projection_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["pass_count"] < report["summary"]["image_count"]


def test_generate_orientation_contact_sheet_writes_html(tmp_path: Path) -> None:
    review_dir = tmp_path / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "expected.png").write_bytes(b"fake")
    (review_dir / "actual.png").write_bytes(b"fake")
    report_path = tmp_path / "projection.json"
    report_path.write_text(
        json.dumps(
            {
                "engine": "godot",
                "label": "good",
                "results": [
                    {
                        "case": "level_north",
                        "camera": "top_down",
                        "failure_signature": None,
                        "pass": True,
                        "expected_image": str((review_dir / "expected.png").resolve()),
                        "actual_image": str((review_dir / "actual.png").resolve()),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "index.html"
    rc = generate_orientation_contact_sheet.run_from_namespace(
        argparse.Namespace(report=[str(report_path)], out=str(out_path))
    )
    assert rc == 0
    assert "FastDIS Orientation Contact Sheet" in out_path.read_text(encoding="utf-8")
