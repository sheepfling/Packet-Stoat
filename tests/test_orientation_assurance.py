from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_orientation_fixture_contract
import run_orientation_assurance


def test_orientation_fixture_contract_passes_canonical_fixture() -> None:
    report = check_orientation_fixture_contract.validate_fixture(ROOT / "tests" / "data" / "orientation_engine_cases.json")
    assert report["status"] == "pass"
    assert report["case_count"] >= 8
    assert report["max_abs_basis_dot"] <= 1e-8
    assert not report["errors"]


def test_orientation_fixture_contract_rejects_missing_expected_vector(tmp_path: Path) -> None:
    fixture_path = tmp_path / "orientation_engine_cases.json"
    payload = json.loads((ROOT / "tests" / "data" / "orientation_engine_cases.json").read_text(encoding="utf-8"))
    del payload["cases"][0]["expected"]["unreal_forward"]
    fixture_path.write_text(json.dumps(payload), encoding="utf-8")

    report = check_orientation_fixture_contract.validate_fixture(fixture_path)
    assert report["status"] == "fail"
    assert any("unreal_forward" in error for error in report["errors"])


def test_orientation_assurance_summary_handles_pass_with_runtime_skips() -> None:
    lanes = {
        "fixture_contract": {"status": "pass"},
        "native_math": {"status": "pass"},
        "pytest_oracles": {"status": "pass"},
        "visual": {"status": "pass", "runtime_lanes": "skipped"},
    }
    status, claim = run_orientation_assurance.compute_overall(lanes)
    assert status == "pass_with_skips"
    assert claim == "position_verified_orientation_opt_in"


def test_orientation_assurance_summary_fails_on_failed_lane() -> None:
    lanes = {
        "fixture_contract": {"status": "pass"},
        "native_math": {"status": "fail"},
        "pytest_oracles": {"status": "pass"},
        "visual": {"status": "pass", "runtime_lanes": "skipped"},
    }
    status, claim = run_orientation_assurance.compute_overall(lanes)
    assert status == "fail"
    assert claim == "orientation_not_claimable"
