from __future__ import annotations

import json
from pathlib import Path

from tests.orientation.harness import compare
from tests.orientation.harness import run_scenario
from tests.orientation.harness import snapshot


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "tests" / "orientation" / "scenarios" / "level_flight.json"
BASELINE = ROOT / "tests" / "orientation" / "baselines" / "level_flight" / "golden"


def test_headless_snapshot_uses_canonical_orientation_case() -> None:
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    case = snapshot.load_case(str(scenario["case"]))
    payload = snapshot.snapshot_for_case(case, tick=5, engine="headless")

    assert payload["entity_id"] == "level_north"
    assert payload["basis"]["forward"] == [0.0, 1.0, 0.0]
    assert payload["euler_deg_frd"] == [0.0, 0.0, 0.0]


def test_orientation_compare_passes_against_checked_in_baseline(tmp_path: Path) -> None:
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    run_dir = tmp_path / "run"
    snapshot.write_snapshots(scenario, engine="headless", out_dir=run_dir)

    report = compare.compare_snapshots(run_dir, BASELINE, scenario)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0


def test_orientation_compare_reports_snapshot_drift(tmp_path: Path) -> None:
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    run_dir = tmp_path / "run"
    snapshot.write_snapshots(scenario, engine="headless", out_dir=run_dir)
    path = run_dir / "state_snapshot_tick_0005.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["basis"]["forward"] = [1.0, 0.0, 0.0]
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = compare.compare_snapshots(run_dir, BASELINE, scenario)

    assert report["status"] == "fail"
    assert any(diff["name"].endswith("basis.forward") for diff in report["diffs"] if diff["status"] == "fail")


def test_run_scenario_all_quick_writes_report(tmp_path: Path) -> None:
    result = run_scenario.run_one(SCENARIO, engine="headless", out_root=tmp_path, update_baseline=False)

    assert result["status"] == "pass"
    assert (tmp_path / "level_flight_headless" / "orientation_compare_report.json").is_file()
