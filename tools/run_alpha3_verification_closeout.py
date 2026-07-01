#!/usr/bin/env python3
"""Run the Alpha 3 closeout verification lanes and write a combined summary."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import evidence_layout
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = evidence_layout.ALPHA3_CURRENT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--engine-version", dest="engine_versions", action="append")
    parser.add_argument("--unreal-engine-version", default="5.8")
    parser.add_argument("--engine-entity-count", type=int, default=1)
    parser.add_argument("--skip-orientation-core", action="store_true")
    parser.add_argument("--skip-orientation-pipeline", action="store_true")
    parser.add_argument("--skip-orientation-visual", action="store_true")
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--skip-sanitizer", action="store_true")
    parser.add_argument("--skip-benchmarks", action="store_true")
    parser.add_argument("--skip-release-audit", action="store_true")
    parser.add_argument("--skip-stage-host", action="store_true")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_step(command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout


def lane_status(code: int) -> str:
    return "passed" if code == 0 else "failed"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha 3 Verification Closeout",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- out_dir: `{report['out_dir']}`",
        "",
        "| Lane | Status | Command |",
        "| --- | --- | --- |",
    ]
    for lane in report["lanes"]:
        lines.append(f"| {lane['name']} | {lane['status']} | `{' '.join(lane['command'])}` |")
    lines.extend(["", "## Artifacts", ""])
    for artifact in report["artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    engine_versions = args.engine_versions or ["5.8"]

    lanes: list[dict[str, Any]] = []
    artifacts: list[str] = []

    if not args.skip_orientation_core:
        command = [sys.executable, "tools/run_orientation_report.py", "--output-dir", str(out_dir)]
        code, output = run_step(command)
        lanes.append({"name": "orientation_core", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(out_dir / "orientation_verification_report.json"),
                display_path(out_dir / "orientation_verification_report.md"),
            ]
        )

    if not args.skip_orientation_pipeline:
        command = [sys.executable, "tools/run_orientation_pipeline_report.py", "--out-dir", str(out_dir)]
        code, output = run_step(command)
        lanes.append({"name": "orientation_pipeline", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(out_dir / "orientation_pipeline_report.json"),
                display_path(out_dir / "orientation_pipeline_report.md"),
            ]
        )

    if not args.skip_orientation_visual:
        command = [sys.executable, "tools/run_orientation_visual_report.py", "--out-dir", str(out_dir)]
        for version in engine_versions:
            command.extend(["--engine-version", version])
        code, output = run_step(command)
        lanes.append({"name": "orientation_visual", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(out_dir / "orientation_visual_report.json"),
                display_path(out_dir / "orientation_visual_report.md"),
                display_path(out_dir / "orientation_visual_review" / "index.html"),
            ]
        )

    if not args.skip_network:
        command = [
            sys.executable,
            "tools/run_network_ingest_matrix.py",
            "--out-dir",
            str(out_dir),
            "--engine-entity-count",
            str(args.engine_entity_count),
            "--unreal-engine-version",
            str(args.unreal_engine_version),
        ]
        code, output = run_step(command)
        lanes.append({"name": "network_ingest", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(out_dir / "network_ingest_matrix.json"),
                display_path(out_dir / "network_ingest_matrix.md"),
            ]
        )

    if not args.skip_sanitizer:
        command = [sys.executable, "tools/run_alpha3_sanitizer_report.py", "--out-dir", str(out_dir)]
        code, output = run_step(command)
        lanes.append({"name": "sanitizer_smoke", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(out_dir / "sanitizer_smoke_report.json"),
                display_path(out_dir / "sanitizer_smoke_report.md"),
            ]
        )

    if not args.skip_benchmarks:
        command = [
            sys.executable,
            "tools/run_benchmarks.py",
            "--out-dir",
            str(ROOT / "benchmark_reports" / "alpha3_matrix"),
            "--format",
            "json",
        ]
        code, output = run_step(command)
        lanes.append({"name": "benchmark_matrix", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(ROOT / "benchmark_reports" / "alpha3_matrix" / "current.json"),
                display_path(ROOT / "benchmark_reports" / "alpha3_matrix" / "qualification.json"),
                display_path(ROOT / "benchmark_reports" / "alpha3_matrix" / "summary.md"),
            ]
        )

    if not args.skip_release_audit:
        command = [sys.executable, "tools/run_alpha3_release_audit.py", "--out-dir", str(out_dir)]
        code, output = run_step(command)
        lanes.append({"name": "release_audit", "status": lane_status(code), "command": command, "output": output})
        artifacts.extend(
            [
                display_path(out_dir / "alpha3_release_audit_report.json"),
                display_path(out_dir / "alpha3_release_audit_report.md"),
            ]
        )

    if not args.skip_stage_host:
        command = [
            sys.executable,
            "tools/stage_alpha3_host_report.py",
            "--source-dir",
            str(out_dir),
            "--overwrite",
        ]
        code, output = run_step(command)
        lanes.append({"name": "stage_host_bundle", "status": lane_status(code), "command": command, "output": output})

    overall_status = "passed" if all(lane["status"] == "passed" for lane in lanes) else "failed"
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "out_dir": display_path(out_dir),
        "overall_status": overall_status,
        "lanes": lanes,
        "artifacts": artifacts,
    }
    json_path = out_dir / "alpha3_verification_closeout.json"
    md_path = out_dir / "alpha3_verification_closeout.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
