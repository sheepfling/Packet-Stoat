"""Compare orientation scenario run snapshots against baselines."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Diff:
    name: str
    status: str
    detail: str
    delta: float | None = None
    tolerance: float | None = None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def snapshot_files(root: Path) -> dict[str, Path]:
    return {path.stem: path for path in sorted(root.glob("state_snapshot_tick_*.json"))}


def max_abs(left: list[float], right: list[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right))


def compare_vector(name: str, current: dict[str, Any], baseline: dict[str, Any], field: str, tolerance: float) -> Diff:
    left = current.get(field)
    right = baseline.get(field)
    if not isinstance(left, list) or not isinstance(right, list):
        return Diff(f"{name}.{field}", "fail", "field missing or not a list")
    delta = max_abs([float(value) for value in left], [float(value) for value in right])
    return Diff(
        f"{name}.{field}",
        "pass" if delta <= tolerance else "fail",
        "within tolerance" if delta <= tolerance else "outside tolerance",
        delta,
        tolerance,
    )


def compare_basis(name: str, current: dict[str, Any], baseline: dict[str, Any], tolerance: float) -> list[Diff]:
    diffs: list[Diff] = []
    current_basis = current.get("basis", {})
    baseline_basis = baseline.get("basis", {})
    if not isinstance(current_basis, dict) or not isinstance(baseline_basis, dict):
        return [Diff(f"{name}.basis", "fail", "basis missing")]
    for axis in ("forward", "right", "up"):
        left = current_basis.get(axis)
        right = baseline_basis.get(axis)
        if not isinstance(left, list) or not isinstance(right, list):
            diffs.append(Diff(f"{name}.basis.{axis}", "fail", "axis missing"))
            continue
        delta = max_abs([float(value) for value in left], [float(value) for value in right])
        diffs.append(
            Diff(
                f"{name}.basis.{axis}",
                "pass" if delta <= tolerance else "fail",
                "within tolerance" if delta <= tolerance else "outside tolerance",
                delta,
                tolerance,
            )
        )
    return diffs


def compare_snapshots(run_dir: Path, baseline_dir: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    current_files = snapshot_files(run_dir)
    baseline_files = snapshot_files(baseline_dir)
    diffs: list[Diff] = []
    missing = sorted(set(baseline_files) - set(current_files))
    extra = sorted(set(current_files) - set(baseline_files))
    diffs.append(Diff("snapshot.file_set", "pass" if not missing and not extra else "fail", f"missing={missing or []} extra={extra or []}"))

    tolerances = scenario["tolerances"]
    for stem in sorted(set(current_files) & set(baseline_files)):
        current = load_json(current_files[stem])
        baseline = load_json(baseline_files[stem])
        diffs.extend(
            [
                compare_vector(stem, current, baseline, "ecef_m", float(tolerances["position_m_abs"])),
                compare_vector(stem, current, baseline, "quat_wxyz", float(tolerances["quat_abs"])),
                compare_vector(stem, current, baseline, "euler_deg_frd", float(tolerances["euler_deg_abs"])),
                compare_vector(stem, current, baseline, "lin_vel_mps", float(tolerances["velocity_mps_abs"])),
            ]
        )
        diffs.extend(compare_basis(stem, current, baseline, float(tolerances["axis_component_abs"])))
    failures = [diff for diff in diffs if diff.status != "pass"]
    return {
        "schema": "fastdis.orientation.compare_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario": scenario["name"],
        "status": "pass" if not failures else "fail",
        "summary": {
            "checks": len(diffs),
            "passed": len(diffs) - len(failures),
            "failed": len(failures),
        },
        "diffs": [diff.__dict__ for diff in diffs],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scenario = load_json(args.scenario)
    report = compare_snapshots(args.run_dir, args.baseline_dir, scenario)
    if args.out:
        write_json(args.out, report)
    if args.verbose or not args.out:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
