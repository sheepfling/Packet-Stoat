#!/usr/bin/env python3
"""Run Alpha 3 sanitizer smoke and write machine-readable proof artifacts."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha3_current"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown sanitizer proof artifacts")
    parser.add_argument("--build-dir", default="build-alpha3-sanitizers", help="Build directory forwarded to tools/run_sanitizers.py")
    parser.add_argument("--config", default="Debug", help="Build config forwarded to tools/run_sanitizers.py")
    parser.add_argument("--sanitizers", default="asan,ubsan", help="Sanitizer set forwarded to tools/run_sanitizers.py")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha 3 Sanitizer Smoke Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: `{report['status']}`",
        f"- build_dir: `{report['build_dir']}`",
        f"- config: `{report['config']}`",
        f"- sanitizers: `{report['sanitizers']}`",
        "",
        "## Command",
        "",
        "```text",
        report["command"],
        "```",
        "",
        "## Summary",
        "",
        f"- return_code: `{report['return_code']}`",
    ]
    if report.get("note"):
        lines.append(f"- note: {report['note']}")
    lines.extend(
        [
            "",
            "## Output",
            "",
            "```text",
            str(report["output"]).rstrip(),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(ROOT / "tools" / "run_sanitizers.py"),
        "--build-dir",
        args.build_dir,
        "--config",
        args.config,
        "--sanitizers",
        args.sanitizers,
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    status = "passed" if completed.returncode == 0 else "failed"
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "build_dir": args.build_dir,
        "config": args.config,
        "sanitizers": args.sanitizers,
        "return_code": completed.returncode,
        "command": " ".join(command),
        "output": completed.stdout,
        "note": "Alpha 3 release smoke requires at least one ASAN/UBSAN sanitizer-backed native test pass artifact.",
    }

    json_path = out_dir / "sanitizer_smoke_report.json"
    md_path = out_dir / "sanitizer_smoke_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
