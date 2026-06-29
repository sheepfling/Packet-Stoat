#!/usr/bin/env python3
"""Generate an Alpha 3 report for Python and plugin-facing I/O verification routes."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha3_current"
GODOT_REPLAY_PATH = ROOT / "packages" / "godot" / "fastdis_demo" / "data" / "synthetic.fastdispkt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown report outputs")
    parser.add_argument("--count", type=int, default=24, help="Packet count forwarded to the Python net smoke")
    parser.add_argument("--entity-count", type=int, default=3, help="Entity count forwarded to the Python net smoke")
    parser.add_argument("--site", type=int, default=100, help="Site ID used by the generated replay route")
    parser.add_argument("--application", type=int, default=1, help="Application ID used by the generated replay route")
    parser.add_argument("--entity", type=int, default=0, help="First entity ID used by the generated replay route")
    parser.add_argument("--skip-godot", action="store_true", help="Skip the Godot demo route check")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_step(cmd: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    src = ROOT / "src"
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "output": completed.stdout,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 3 I/O Routes Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        "",
        "| Route | Status | Notes |",
        "| --- | --- | --- |",
    ]
    for route in report["routes"]:
        note = route.get("note", "")
        lines.append(f"| {route['name']} | {route['status']} | {note} |")
    lines.extend(["", "## Route Details", ""])
    for route in report["routes"]:
        lines.extend(
            [
                f"### {route['name']}",
                "",
                f"- status: `{route['status']}`",
                f"- command: `{' '.join(route['command'])}`",
                "",
                "```text",
                str(route["output"]).rstrip(),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    routes: list[dict[str, object]] = []
    net_smoke = run_step(
        [
            sys.executable,
            "-m",
            "fastdis.tools.net_smoke",
            "--count",
            str(args.count),
            "--entity-count",
            str(args.entity_count),
            "--site",
            str(args.site),
            "--application",
            str(args.application),
            "--entity",
            str(args.entity),
            "--write-replay",
            str(GODOT_REPLAY_PATH),
            "--print-json",
        ]
    )
    net_smoke["name"] = "python_net_smoke"
    net_smoke["note"] = "localhost UDP send/receive plus native scanner/entity-table/snapshot verification"
    routes.append(net_smoke)

    if not args.skip_godot:
        godot = run_step(
            [
                sys.executable,
                str(ROOT / "tools" / "run_godot_demo_smoke.py"),
                "--skip-build",
                "--skip-replay-generation",
            ]
        )
        godot["name"] = "godot_demo_replay_route"
        godot["note"] = "Godot plugin/demo consumes replay emitted by the Python net smoke route"
        routes.append(godot)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "routes": routes,
    }
    json_path = out_dir / "io_routes_report.json"
    md_path = out_dir / "io_routes_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    overall_ok = all(route["status"] == "passed" for route in routes)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
