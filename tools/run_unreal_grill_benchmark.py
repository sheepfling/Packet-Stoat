#!/usr/bin/env python3
"""Run the shared Unreal-vs-GRILL head-to-head comparison when both reports exist."""

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
DEFAULT_FASTDIS = ROOT / "build" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json"
DEFAULT_RAW_BASELINE = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json"
DEFAULT_GRILL_CANDIDATES = [
    ROOT / "build" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.json",
    ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_engine_benchmark_report.json",
    ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json",
]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "engine_head_to_head"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--grill-report", dest="grill_reports", type=Path, action="append", help="Candidate GRILL Unreal shared benchmark report path")
    parser.add_argument("--allow-sample-grill", action="store_true", help="Allow a sample GRILL report when no current report exists")
    parser.add_argument("--if-available", action="store_true", help="Exit successfully when no compatible GRILL report is available yet")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "unreal_vs_grill.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "unreal_vs_grill.md")
    return parser.parse_args(argv)


def classify_path(path: Path) -> str:
    if "/samples/" in path.as_posix() or ".sample." in path.name:
        return "sample"
    return "current"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_grill_report(candidates: list[Path], *, allow_sample: bool) -> Path | None:
    existing = [path for path in candidates if path.exists()]
    for path in existing:
        if classify_path(path) == "current":
            return path
    if allow_sample:
        for path in existing:
            if classify_path(path) == "sample":
                return path
    return None


def first_existing_path(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return candidates[0] if candidates else None


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
            "right_surface": "grill_unreal",
            "left_host": fastdis_payload.get("host") if isinstance(fastdis_payload.get("host"), dict) else {},
            "right_host": {},
        },
        "validation_errors": [],
        "comparison": {
            "status": "blocked_on_competitor",
            "claim_boundaries": [
                "Direct competitor claims require same-host evidence and matched scenario names.",
                "No current GRILL Unreal shared benchmark report is available on this host, so this lane is blocked rather than comparable.",
            ],
            "same_host": False,
            "left_label": "FastDIS Unreal",
            "right_label": "GRILL Unreal",
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
        "# Unreal vs GRILL Head-to-Head",
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
        "FastDIS Unreal",
        "--right-label",
        "GRILL Unreal",
        "--json-out",
        str(args.json_out),
        "--md-out",
        str(args.md_out),
    ]


def build_normalize_command(raw_baseline: Path) -> list[str]:
    return [
        sys.executable,
        "tools/normalize_unreal_grill_baseline.py",
        "--input",
        str(raw_baseline),
        "--out-dir",
        str(ROOT / "build" / "reports" / "engine_benchmarks"),
    ]


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    candidates = args.grill_reports or DEFAULT_GRILL_CANDIDATES
    grill_report = select_grill_report(candidates, allow_sample=bool(args.allow_sample_grill))
    if grill_report is None and DEFAULT_RAW_BASELINE.exists():
        normalize_code = run_step(build_normalize_command(DEFAULT_RAW_BASELINE))
        if normalize_code != 0:
            return normalize_code
        grill_report = select_grill_report(candidates, allow_sample=bool(args.allow_sample_grill))
    if grill_report is None:
        note = "No compatible GRILL Unreal shared benchmark report found."
        write_unavailable_report(args, note=note, right_path=first_existing_path(candidates))
        print(note)
        return 0 if args.if_available else 1
    return run_step(build_command(args, grill_report=grill_report))


if __name__ == "__main__":
    raise SystemExit(main())
