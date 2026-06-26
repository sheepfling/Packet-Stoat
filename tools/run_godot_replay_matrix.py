#!/usr/bin/env python3
"""Run the canonical Godot replay runtime matrix."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports" / "godot_replay_matrix"
CORE_ROUTE_CONFIGS = (
    {
        "scenario": "entity_state_1x10hz",
        "count": 24,
        "entity_count": 1,
        "rate_hz": 10.0,
    },
    {
        "scenario": "entity_state_100x30hz",
        "count": 300,
        "entity_count": 100,
        "rate_hz": 30.0,
    },
    {
        "scenario": "entity_state_1000x60hz",
        "count": 1000,
        "entity_count": 1000,
        "rate_hz": 60.0,
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--godot", help="Explicit godot executable path")
    parser.add_argument("--skip-build", action="store_true", help="Do not rebuild/stage the Godot extension before running")
    parser.add_argument("--if-available", action="store_true", help="Exit successfully when replay routes are present but failed or pending")
    return parser.parse_args()


def extract_json(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object found in stdout")
    return json.loads(stdout[start:])


def run_route(config: dict[str, Any], *, godot: str | None, skip_build: bool) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_godot_replay_smoke.py"),
        "--scenario",
        str(config["scenario"]),
        "--count",
        str(config["count"]),
        "--entity-count",
        str(config["entity_count"]),
        "--rate-hz",
        str(config["rate_hz"]),
    ]
    if godot:
        command.extend(["--godot", godot])
    if skip_build:
        command.append("--skip-build")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    payload = None
    errors: list[str] = []
    try:
        payload = extract_json(completed.stdout)
    except Exception as exc:
        errors.append(f"runner JSON parse failed: {exc}")
    if payload is None:
        return {
            "surface": "godot",
            "mode": "replay",
            "scenario": str(config["scenario"]),
            "scenario_suite": "core_matrix",
            "status": "failed" if completed.returncode else "pending",
            "notes": "Godot replay runner did not emit a parseable JSON payload",
            "recv_command": command,
            "recv_returncode": completed.returncode,
            "recv_output": completed.stdout,
            "errors": errors,
        }
    payload["notes"] = f"headless Godot replay runtime smoke route for {config['scenario']}"
    return payload


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Godot Replay Matrix",
        "",
        f"- generated_at: `{report['generated_at']}`",
        "",
        "| Surface | Mode | Scenario | Status | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["routes"]:
        lines.append(f"| {row['surface']} | {row['mode']} | {row.get('scenario')} | {row['status']} | {row['notes']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    routes = [run_route(config, godot=args.godot, skip_build=args.skip_build) for config in CORE_ROUTE_CONFIGS]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "routes": routes,
    }
    json_path = out_dir / "godot_replay_matrix.json"
    md_path = out_dir / "godot_replay_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {json_path}")
    print(f"md: {md_path}")

    if all(str(row.get("status")) == "passed" for row in routes):
        return 0
    if args.if_available and all(str(row.get("status")) in {"passed", "failed", "pending"} for row in routes):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
