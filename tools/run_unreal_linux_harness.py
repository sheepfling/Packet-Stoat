#!/usr/bin/env python3
"""Run or classify the Linux Unreal live-harness lanes."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import platform
import subprocess

import load_local_env
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "unreal_fastdis_baseline"
MODE_TO_TOOL = {
    "verify": "tools/run_unreal_orientation_verification.py",
    "demo": "tools/run_unreal_demo_smoke.py",
}
MODE_TO_JSON = {
    "verify": "fastdis_unreal_linux_verify.json",
    "demo": "fastdis_unreal_linux_demo.json",
}
MODE_TO_MD = {
    "verify": "fastdis_unreal_linux_verify.md",
    "demo": "fastdis_unreal_linux_demo.md",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(MODE_TO_TOOL), required=True)
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--unreal", help="Explicit Unreal editor executable path")
    parser.add_argument("--json-out", help="Override the JSON report output path")
    parser.add_argument("--md-out", help="Override the Markdown report output path")
    parser.add_argument("--dry-run", action="store_true", help="Do not execute the lane; emit the delegated command and report only")
    return parser.parse_args(argv)


def default_output_path(mode: str, suffix: str) -> Path:
    filename = MODE_TO_JSON[mode] if suffix == "json" else MODE_TO_MD[mode]
    return DEFAULT_OUT_DIR / filename


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def delegated_command(args: argparse.Namespace) -> list[str]:
    cmd = unreal_env.python_command() + [MODE_TO_TOOL[args.mode]]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.unreal:
        cmd.extend(["--unreal", args.unreal])
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def build_report(
    args: argparse.Namespace,
    *,
    command: list[str],
    status: str,
    exit_code: int | None,
    blockers: list[str],
    claim_boundary: str,
    executed: bool,
) -> dict[str, object]:
    host_system = platform.system()
    host_platform = host_system.lower()
    lane = f"linux-{args.mode}"
    return {
        "schema": "fastdis.unreal_linux_harness_lane.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "lane": lane,
        "mode": args.mode,
        "status": status,
        "claim_boundary": claim_boundary,
        "host": {
            "platform_system": host_system,
            "platform_name": host_platform,
            "machine": platform.machine(),
        },
        "target_platform": "linux",
        "engine_version": args.engine_version,
        "executed": executed,
        "exit_code": exit_code,
        "runner": MODE_TO_TOOL[args.mode],
        "command": command,
        "command_display": " ".join(command),
        "blockers": blockers,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        f"# Unreal Linux {report['mode'].title()} Harness",
        "",
        f"- lane: `{report['lane']}`",
        f"- status: `{report['status']}`",
        f"- host_platform: `{report['host']['platform_name']}`",
        f"- machine: `{report['host']['machine']}`",
        f"- target_platform: `{report['target_platform']}`",
        f"- engine_version: `{report.get('engine_version') or 'default'}`",
        f"- executed: `{report['executed']}`",
        f"- exit_code: `{report['exit_code']}`",
        "",
        report["claim_boundary"],
        "",
        "## Delegated Command",
        "",
        f"- runner: `{report['runner']}`",
        f"- command: `{report['command_display']}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = report.get("blockers") or []
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_outputs(report: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    json_out = Path(args.json_out).expanduser().resolve() if args.json_out else default_output_path(args.mode, "json")
    md_out = Path(args.md_out).expanduser().resolve() if args.md_out else default_output_path(args.mode, "md")
    command = delegated_command(args)
    host_is_linux = platform.system().lower() == "linux"

    if args.dry_run:
        report = build_report(
            args,
            command=command,
            status="dry-run",
            exit_code=0,
            blockers=[] if host_is_linux else [f"current host is {platform.system()}, not Linux"],
            claim_boundary=(
                "Dry-run only. This artifact proves the Linux Unreal live-harness lane is wrapped and rerunnable, "
                "but it does not claim execution on the current host."
            ),
            executed=False,
        )
        write_outputs(report, json_out, md_out)
        print(f"JSON: {display_path(json_out)}")
        print(f"Markdown: {display_path(md_out)}")
        return 0

    if not host_is_linux:
        report = build_report(
            args,
            command=command,
            status="blocked-host-platform",
            exit_code=None,
            blockers=[f"current host is {platform.system()}, so the Linux Unreal live-harness lane cannot execute here"],
            claim_boundary=(
                "Blocked-host-platform only. This artifact proves the Linux Unreal live-harness lane has a typed rerun path, "
                "but it does not claim Linux execution, runtime proof, or benchmark evidence on this non-Linux host."
            ),
            executed=False,
        )
        write_outputs(report, json_out, md_out)
        print(f"JSON: {display_path(json_out)}")
        print(f"Markdown: {display_path(md_out)}")
        return 2

    completed = subprocess.run(command, cwd=ROOT, env=unreal_env.build_env())
    report = build_report(
        args,
        command=command,
        status="pass" if completed.returncode == 0 else "fail",
        exit_code=completed.returncode,
        blockers=[],
        claim_boundary=(
            "Linux live-harness execution only. This artifact proves the selected Unreal Linux harness lane ran on a Linux host. "
            "It does not by itself prove same-host GRILL comparison parity or broader performance leadership."
        ),
        executed=True,
    )
    write_outputs(report, json_out, md_out)
    print(f"JSON: {display_path(json_out)}")
    print(f"Markdown: {display_path(md_out)}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
