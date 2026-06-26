#!/usr/bin/env python3
"""Run the shared Unity-vs-GRILL head-to-head comparison when both reports exist."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FASTDIS = ROOT / "build" / "reports" / "engine_benchmarks" / "unity_engine_benchmark_report.json"
DEFAULT_RAW_BASELINE = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"
DEFAULT_IMPORT_SMOKE = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_import_smoke.json"
DEFAULT_GRILL_CANDIDATES = [
    ROOT / "build" / "reports" / "engine_benchmarks" / "grill_unity_engine_benchmark_report.json",
    ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_engine_benchmark_report.json",
]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_head_to_head"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--grill-report", dest="grill_reports", type=Path, action="append", help="Candidate GRILL Unity shared benchmark report path")
    parser.add_argument("--if-available", action="store_true", help="Exit successfully when no current GRILL report is available yet")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "unity_vs_grill.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "unity_vs_grill.md")
    return parser.parse_args(argv)


def select_grill_report(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_unavailable_report(
    args: argparse.Namespace,
    *,
    note: str,
    right_path: Path | None,
) -> None:
    fastdis_payload = load_json(args.fastdis) if args.fastdis.exists() else {}
    report = {
        "schema": "fastdis.engine_head_to_head_report.v1",
        "generated_at_utc": utc_now(),
        "status": "blocked_on_competitor",
        "note": note,
        "inputs": {
            "left": display_path(args.fastdis),
            "right": display_path(right_path) if right_path is not None else None,
            "left_surface": fastdis_payload.get("surface") if isinstance(fastdis_payload, dict) else None,
            "right_surface": "grill_unity",
            "left_host": fastdis_payload.get("host") if isinstance(fastdis_payload.get("host"), dict) else {},
            "right_host": {},
        },
        "validation_errors": [],
        "comparison": {
            "status": "blocked_on_competitor",
            "claim_boundaries": [
                "Direct competitor claims require same-host evidence and matched scenario names.",
                "No current GRILL Unity shared benchmark report is available on this host, so this lane is blocked rather than comparable.",
            ],
            "same_host": False,
            "left_label": "FastDIS Unity",
            "right_label": "GRILL Unity",
            "matched_scenarios": 0,
            "left_only_scenarios": [],
            "right_only_scenarios": [],
            "comparable_metric_rows": 0,
            "rows": [],
        },
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Unity vs GRILL Head-to-Head",
        "",
        f"- status: `{report['status']}`",
        f"- left: `{report['inputs']['left']}`",
        f"- right: `{report['inputs']['right']}`",
        f"- note: `{note}`",
        "",
    ]
    args.md_out.write_text("\n".join(lines), encoding="utf-8")


def build_command(args: argparse.Namespace, *, grill_report: Path) -> list[str]:
    return [
        sys.executable,
        "tools/run_engine_head_to_head_matrix.py",
        "--left",
        str(args.fastdis),
        "--right",
        str(grill_report),
        "--left-label",
        "FastDIS Unity",
        "--right-label",
        "GRILL Unity",
        "--json-out",
        str(args.json_out),
        "--md-out",
        str(args.md_out),
    ]


def build_normalize_command(raw_baseline: Path) -> list[str]:
    return [
        sys.executable,
        "tools/normalize_unity_grill_baseline.py",
        "--input",
        str(raw_baseline),
        "--out-dir",
        str(ROOT / "build" / "reports" / "engine_benchmarks"),
    ]


def build_capture_command() -> list[str]:
    return [
        sys.executable,
        "tools/capture_grill_unity_benchmark.py",
        "--overwrite",
    ]


def import_smoke_passed(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return payload.get("status") == "pass"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    candidates = args.grill_reports or DEFAULT_GRILL_CANDIDATES
    grill_report = select_grill_report(candidates)
    if grill_report is None:
        if DEFAULT_RAW_BASELINE.exists():
            normalize_code = run_step(build_normalize_command(DEFAULT_RAW_BASELINE))
            if normalize_code != 0:
                return normalize_code
            grill_report = select_grill_report(candidates)
        elif import_smoke_passed(DEFAULT_IMPORT_SMOKE):
            capture_code = run_step(build_capture_command())
            if capture_code != 0:
                return capture_code
            normalize_code = run_step(build_normalize_command(DEFAULT_RAW_BASELINE))
            if normalize_code != 0:
                return normalize_code
            grill_report = select_grill_report(candidates)
    if grill_report is None:
        note = "No current GRILL Unity shared benchmark report found."
        write_unavailable_report(args, note=note, right_path=candidates[0] if candidates else None)
        print(note)
        return 0 if args.if_available else 1
    return run_step(build_command(args, grill_report=grill_report))


if __name__ == "__main__":
    raise SystemExit(main())
