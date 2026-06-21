from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import fastdis_orient


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "data" / "orientation_engine_cases.json"
GODOT_CONFIG = ROOT / "configs" / "orientation" / "godot_standalone_enu_m.yaml"
UNREAL_CONFIG = ROOT / "configs" / "orientation" / "unreal_standalone_neu_cm.yaml"
KNOWN_BAD = ROOT / "tests" / "orientation_known_bad" / "godot_forward_inverted.yaml"
KNOWN_BAD_CASES = {
    "godot": ROOT / "tests" / "orientation_known_bad" / "godot_forward_inverted.yaml",
    "unreal": ROOT / "tests" / "orientation_known_bad" / "unreal_north_east_swap.yaml",
    "unity": ROOT / "tests" / "orientation_known_bad" / "unity_forward_inverted.yaml",
}


def test_compare_good_configs_pass() -> None:
    godot_payload = fastdis_orient.compare_payload(FIXTURES, fastdis_orient.load_structured(GODOT_CONFIG), "godot")
    unreal_payload = fastdis_orient.compare_payload(FIXTURES, fastdis_orient.load_structured(UNREAL_CONFIG), "unreal")
    assert godot_payload["summary"]["pass_count"] == godot_payload["summary"]["case_count"]
    assert unreal_payload["summary"]["pass_count"] == unreal_payload["summary"]["case_count"]


def test_known_bad_config_fails_with_expected_signature() -> None:
    for target, path in KNOWN_BAD_CASES.items():
        payload = fastdis_orient.load_structured(path)
        compare = fastdis_orient.compare_payload(FIXTURES, payload["config"], target)
        assert compare["summary"]["pass_count"] < compare["summary"]["case_count"]
        signatures = {item["failure_signature"] for item in compare["results"] if not item["pass"]}
        assert payload["expected_signature"] in signatures


def test_solver_suggests_good_godot_asset_axes() -> None:
    payload = fastdis_orient.load_structured(KNOWN_BAD)
    solve = fastdis_orient.solve_payload(FIXTURES, payload["config"], "godot", "asset_axes")
    assert solve["candidates"]
    assert solve["base_config"] == payload["config"]
    best = solve["candidates"][0]
    assert best["variant"]["asset.forward_axis"] == "negative_z"
    assert best["variant"]["asset.up_axis"] == "positive_y"


def test_trace_and_diff_capture_asset_basis_change() -> None:
    case = fastdis_orient.load_case(FIXTURES, "level_north")
    good_trace = fastdis_orient.compute_trace(case, fastdis_orient.load_structured(GODOT_CONFIG))
    bad_trace = fastdis_orient.compute_trace(case, fastdis_orient.load_structured(KNOWN_BAD)["config"])
    diff = fastdis_orient.diff_trace_payload(bad_trace, good_trace)
    assert diff["differences"]
    assert diff["before_config"] == bad_trace["config"]
    assert diff["after_config"] == good_trace["config"]
    assert any(item["path"].startswith("stage_4_asset_corrected_basis.") for item in diff["differences"])


def test_diagnose_payload_carries_config_snapshot() -> None:
    payload = fastdis_orient.load_structured(KNOWN_BAD)
    compare = fastdis_orient.compare_payload(FIXTURES, payload["config"], "godot")
    diagnose = fastdis_orient.diagnose_payload(compare)
    assert diagnose["config"] == payload["config"]


def test_compare_cli_writes_json_report(monkeypatch, tmp_path: Path) -> None:
    out_path = tmp_path / "compare.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fastdis_orient.py",
            "compare",
            "--fixtures",
            str(FIXTURES),
            "--config",
            str(GODOT_CONFIG),
            "--target",
            "godot",
            "--out",
            str(out_path),
        ],
    )
    rc = fastdis_orient.main()
    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["target"] == "godot"
    assert payload["summary"]["pass_count"] == payload["summary"]["case_count"]
