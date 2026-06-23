"""Run deterministic orientation scenarios through a headless adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from . import compare
from . import snapshot


ROOT = Path(__file__).resolve().parents[3]
SCENARIO_DIR = ROOT / "tests" / "orientation" / "scenarios"
DEFAULT_OUT_ROOT = ROOT / "build" / "orientation" / "runs"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_paths(all_quick: bool, scenario: Path | None) -> list[Path]:
    if all_quick:
        return sorted(SCENARIO_DIR.glob("*.json"))
    if scenario is None:
        raise SystemExit("--scenario is required unless --all-quick is used")
    return [scenario]


def run_one(path: Path, *, engine: str, out_root: Path, update_baseline: bool) -> dict[str, object]:
    scenario = load_json(path)
    if engine != "headless":
        raise SystemExit(f"Only the headless orientation adapter is implemented in this harness; requested {engine}")
    run_dir = out_root / f"{scenario['name']}_{engine}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    written = snapshot.write_snapshots(scenario, engine=engine, out_dir=run_dir)
    baseline_dir = ROOT / "tests" / "orientation" / "baselines" / str(scenario["name"]) / "golden"
    if update_baseline:
        if baseline_dir.exists():
            shutil.rmtree(baseline_dir)
        shutil.copytree(run_dir, baseline_dir)
    report = compare.compare_snapshots(run_dir, baseline_dir, scenario)
    report_path = run_dir / "orientation_compare_report.json"
    compare.write_json(report_path, report)
    return {
        "scenario": scenario["name"],
        "engine": engine,
        "status": report["status"],
        "run_dir": str(run_dir),
        "baseline_dir": str(baseline_dir),
        "snapshots": [str(item) for item in written],
        "report": str(report_path),
        "summary": report["summary"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--engine", choices=("headless", "unreal", "godot", "unity"), default="headless")
    parser.add_argument("--all-quick", action="store_true")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--update-baseline", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reports = [run_one(path, engine=args.engine, out_root=args.out_root, update_baseline=args.update_baseline) for path in scenario_paths(args.all_quick, args.scenario)]
    payload = {
        "schema": "fastdis.orientation.scenario_run.v1",
        "status": "pass" if all(report["status"] == "pass" for report in reports) else "fail",
        "reports": reports,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
