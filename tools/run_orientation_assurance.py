#!/usr/bin/env python3
"""Run the orientation assurance closeout lanes and write one summary."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from artifacts import VERIFICATION_REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "orientation_current"
ORACLE_TESTS = [
    "tests/test_orientation_oracle.py",
    "tests/test_orientation_against_scipy.py",
    "tests/test_orientation_sympy_generated.py",
    "tests/test_orientation_engine_cases.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for assurance artifacts")
    parser.add_argument(
        "--run-engine-runtimes",
        action="store_true",
        help="Launch Unreal/Godot runtime orientation lanes instead of only deterministic projection artifacts.",
    )
    parser.add_argument(
        "--engine-version",
        dest="engine_versions",
        action="append",
        help="Unreal version for runtime lanes; pass multiple times for matrix coverage.",
    )
    parser.add_argument("--skip-pytest-oracles", action="store_true", help="Skip SciPy/SymPy/pytest oracle lanes")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_step(name: str, cmd: list[str], out_dir: Path) -> dict[str, Any]:
    log_path = out_dir / f"{name}.log"
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    log_path.write_text(completed.stdout, encoding="utf-8")
    return {
        "name": name,
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "command": cmd,
        "log": display_path(log_path),
    }


def load_json_if_present(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def lane_from_report(name: str, step: dict[str, Any], report_path: Path) -> dict[str, Any]:
    report = load_json_if_present(report_path)
    status = step["status"]
    if report and str(report.get("status", "")).lower() in {"pass", "passed"}:
        status = "pass"
    elif report and str(report.get("status", "")).lower() in {"fail", "failed"}:
        status = "fail"
    return {
        "status": status,
        "command_status": step["status"],
        "report": display_path(report_path),
        "log": step["log"],
        "summary": summarize_report(name, report),
    }


def summarize_report(name: str, report: dict[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return {}
    if name == "fixture_contract":
        return {
            "case_count": report.get("case_count"),
            "error_count": len(report.get("errors", [])),
            "warning_count": len(report.get("warnings", [])),
            "max_abs_basis_dot": report.get("max_abs_basis_dot"),
        }
    if name == "native_math":
        return {
            "status": report.get("status"),
            "golden_cases": report.get("golden_fixture", {}).get("case_count"),
            "engine_cases": report.get("engine_fixture", {}).get("case_count"),
            "random_iterations": report.get("randomized_properties", {}).get("iterations"),
        }
    if name == "visual":
        projection_reviews = report.get("projection_reviews", [])
        return {
            "unreal_versions": report.get("unreal_engine_versions", []),
            "projection_review_count": len(projection_reviews),
            "known_bad_count": sum(1 for item in projection_reviews if item.get("expected_result") == "fail"),
            "known_bad_observed": sum(1 for item in projection_reviews if item.get("status") == "expected-fail-observed"),
            "contact_sheet": report.get("contact_sheet_path"),
        }
    return {}


def pytest_lane(out_dir: Path, skip: bool) -> dict[str, Any]:
    if skip:
        return {"status": "skipped", "reason": "requested by --skip-pytest-oracles"}
    step = run_step(
        "pytest_orientation_oracles",
        [sys.executable, "-m", "pytest", "-q", *ORACLE_TESTS],
        out_dir,
    )
    return {
        "status": step["status"],
        "tests": ORACLE_TESTS,
        "log": step["log"],
        "returncode": step["returncode"],
    }


def visual_lane(out_dir: Path, run_engine_runtimes: bool, engine_versions: list[str] | None) -> dict[str, Any]:
    cmd = [sys.executable, "tools/run_orientation_visual_report.py", "--out-dir", str(out_dir)]
    if not run_engine_runtimes:
        cmd.extend(["--skip-unreal", "--skip-godot"])
    for version in engine_versions or []:
        cmd.extend(["--engine-version", version])
    step = run_step("orientation_visual_report", cmd, out_dir)
    lane = lane_from_report("visual", step, out_dir / "orientation_visual_report.json")
    report = load_json_if_present(out_dir / "orientation_visual_report.json") or {}
    if not run_engine_runtimes:
        lane["status"] = "pass" if step["status"] == "pass" else "fail"
        lane["runtime_lanes"] = "skipped"
        lane["skip_reason"] = "run with --run-engine-runtimes to launch Unreal/Godot"
    else:
        lane["runtime_lanes"] = "requested"
    lane["projection_reviews"] = [
        {
            "engine": item.get("engine"),
            "label": item.get("label"),
            "status": item.get("status"),
            "expected_result": item.get("expected_result"),
            "report_path": item.get("report_path"),
        }
        for item in report.get("projection_reviews", [])
    ]
    return lane


def compute_overall(lanes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    failed = [name for name, lane in lanes.items() if lane.get("status") == "fail"]
    skipped = [name for name, lane in lanes.items() if lane.get("status") == "skipped"]
    runtime_skipped = lanes.get("visual", {}).get("runtime_lanes") == "skipped"
    if failed:
        return "fail", "orientation_not_claimable"
    if skipped or runtime_skipped:
        return "pass_with_skips", "position_verified_orientation_opt_in"
    return "pass", "basis_and_visual_verified_for_requested_lanes"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Orientation Assurance Summary",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- overall_status: `{summary['overall_status']}`",
        f"- release_claim: `{summary['release_claim']}`",
        "",
        "| Lane | Status | Report / Log |",
        "| --- | --- | --- |",
    ]
    for name, lane in summary["lanes"].items():
        report = lane.get("report") or lane.get("log") or lane.get("reason") or ""
        lines.append(f"| {name} | {lane.get('status')} | `{report}` |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Fixture validation checks schema, required vectors, DIS angles, unit length, orthogonality, and determinant sanity.",
            "- Deterministic visual projection artifacts and known-bad checks run without launching engines.",
            "- Use `--run-engine-runtimes` to include live Unreal/Godot runtime lanes in the same report.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_dir = args.out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    fixture_step = run_step(
        "fixture_contract",
        [sys.executable, "tools/check_orientation_fixture_contract.py", "--out-dir", str(out_dir)],
        out_dir,
    )
    native_step = run_step(
        "native_orientation_report",
        [sys.executable, "tools/run_orientation_report.py", "--output-dir", str(out_dir)],
        out_dir,
    )

    lanes: dict[str, dict[str, Any]] = {
        "fixture_contract": lane_from_report("fixture_contract", fixture_step, out_dir / "fixture_contract_report.json"),
        "native_math": lane_from_report("native_math", native_step, out_dir / "orientation_verification_report.json"),
        "pytest_oracles": pytest_lane(out_dir, args.skip_pytest_oracles),
        "visual": visual_lane(out_dir, args.run_engine_runtimes, args.engine_versions),
    }

    overall_status, release_claim = compute_overall(lanes)
    summary = {
        "schema": "fastdis.orientation_assurance_summary.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status,
        "release_claim": release_claim,
        "out_dir": display_path(out_dir),
        "engine_runtimes_requested": bool(args.run_engine_runtimes),
        "lanes": lanes,
    }

    json_path = out_dir / "orientation_assurance_summary.json"
    md_path = out_dir / "orientation_assurance_summary.md"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(f"orientation assurance: {overall_status}")
    print(f"summary: {display_path(md_path)}")
    return 0 if overall_status in {"pass", "pass_with_skips"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
