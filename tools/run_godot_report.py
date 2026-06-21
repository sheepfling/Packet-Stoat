#!/usr/bin/env python3
"""Run the Godot workflow lanes and write a machine-readable proof report."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import subprocess
import tempfile

import godot_workflow
import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    parser.add_argument("--skip-build", action="store_true", help="Skip the build/stage lane")
    parser.add_argument("--skip-verify", action="store_true", help="Skip the orientation verification lane")
    parser.add_argument("--skip-demo", action="store_true", help="Skip the replay demo smoke lane")
    parser.add_argument("--skip-missing-lib", action="store_true", help="Skip the missing-native-library lane")
    return parser.parse_args()


def critical_doctor_failures(payload: dict[str, object]) -> list[dict[str, str]]:
    checks = payload["checks"]
    critical_names = {
        "godot",
        "scons",
        "work root has no spaces",
        "cmake",
        "godot-cpp",
    }
    return [check for check in checks if check["name"] in critical_names and check["status"] != "ok"]


def run_step(cmd: list[str]) -> tuple[int, str]:
    with tempfile.TemporaryFile(mode="w+b") as capture:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=capture,
            stderr=subprocess.STDOUT,
        )
        capture.seek(0)
        output = capture.read().decode("utf-8", errors="replace")
    return completed.returncode, output


def summarize_markdown(report: dict[str, object]) -> str:
    host = report["doctor"]["host"]
    lanes = report["lanes"]
    lines = [
        "# Godot Workflow Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- host_platform: `{host['platform']}`",
        f"- host_arch: `{host['arch']}`",
        "",
        "| Lane | Status | Notes |",
        "| --- | --- | --- |",
        f"| doctor | {report['doctor']['status']} | {'; '.join(report['doctor']['notes']) if report['doctor']['notes'] else 'none'} |",
        f"| build | {lanes['build']['status']} | {'; '.join(lanes['build']['notes']) if lanes['build']['notes'] else 'none'} |",
        f"| verify | {lanes['verify']['status']} | {'; '.join(lanes['verify']['notes']) if lanes['verify']['notes'] else 'none'} |",
        f"| demo | {lanes['demo']['status']} | {'; '.join(lanes['demo']['notes']) if lanes['demo']['notes'] else 'none'} |",
        f"| missing-lib | {lanes['missing_lib']['status']} | {'; '.join(lanes['missing_lib']['notes']) if lanes['missing_lib']['notes'] else 'none'} |",
        "",
        "## Doctor Checks",
        "",
    ]
    for check in report["doctor"]["checks"]:
        lines.append(f"- {check['name']}: {check['status']} ({check['detail']})")
    lines.extend(
        [
            "",
            "## Host",
            "",
            f"- godot: `{host['godot'] or 'missing'}`",
            f"- scons: `{host['scons'] or 'missing'}`",
            f"- repo_alias_root: `{host['repo_alias_root']}`",
            f"- work_root: `{host['work_root']}`",
            f"- work_root_has_spaces: `{host.get('work_root_has_spaces', False)}`",
            "",
        ]
    )
    return "\n".join(lines)


def blocked_lane(reason: str) -> dict[str, object]:
    return {
        "status": "blocked",
        "returncode": None,
        "command": None,
        "notes": [reason],
    }


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    doctor = godot_workflow.doctor_payload()
    blocking = critical_doctor_failures(doctor)
    doctor_notes = [f"{check['name']} failed: {check['detail']}" for check in blocking]

    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "doctor": {
            "status": "passed" if not blocking else "needs-attention",
            "checks": doctor["checks"],
            "notes": doctor_notes,
            "host": doctor["host"],
        },
        "lanes": {
            "build": {"status": "skipped" if args.skip_build else "pending", "returncode": None, "command": None, "notes": []},
            "verify": {"status": "skipped" if args.skip_verify else "pending", "returncode": None, "command": None, "notes": []},
            "demo": {"status": "skipped" if args.skip_demo else "pending", "returncode": None, "command": None, "notes": []},
            "missing_lib": {"status": "skipped" if args.skip_missing_lib else "pending", "returncode": None, "command": None, "notes": []},
        },
    }

    if blocking:
        reason = "doctor proved a host/tooling blocker before runnable lanes could be trusted"
        if not args.skip_build:
            report["lanes"]["build"] = blocked_lane(reason)
        if not args.skip_verify:
            report["lanes"]["verify"] = blocked_lane(reason)
        if not args.skip_demo:
            report["lanes"]["demo"] = blocked_lane(reason)
        if not args.skip_missing_lib:
            report["lanes"]["missing_lib"] = blocked_lane(reason)
    else:
        if not args.skip_build:
            cmd = godot_workflow.godot_env.python_command() + ["tools/build_godot_extension.py"]
            code, output = run_step(cmd)
            lane = report["lanes"]["build"]
            lane["command"] = cmd
            lane["returncode"] = code
            lane["status"] = "passed" if code == 0 else "failed"
            lane["output"] = output
            if code != 0:
                lane["notes"].append("build/stage lane failed")

        if not args.skip_verify:
            cmd = godot_workflow.godot_env.python_command() + ["tools/run_godot_orientation_verification.py", "--skip-build"]
            code, output = run_step(cmd)
            lane = report["lanes"]["verify"]
            lane["command"] = cmd
            lane["returncode"] = code
            lane["status"] = "passed" if code == 0 else "failed"
            lane["output"] = output
            if code != 0:
                lane["notes"].append("orientation verification failed")

        if not args.skip_demo:
            cmd = godot_workflow.godot_env.python_command() + ["tools/run_godot_demo_smoke.py", "--skip-build"]
            code, output = run_step(cmd)
            lane = report["lanes"]["demo"]
            lane["command"] = cmd
            lane["returncode"] = code
            lane["status"] = "passed" if code == 0 else "failed"
            lane["output"] = output
            if code != 0:
                lane["notes"].append("demo smoke failed")

        if not args.skip_missing_lib:
            cmd = godot_workflow.godot_env.python_command() + ["tools/run_godot_missing_library_check.py", "--skip-build"]
            code, output = run_step(cmd)
            lane = report["lanes"]["missing_lib"]
            lane["command"] = cmd
            lane["returncode"] = code
            lane["status"] = "passed" if code == 0 else "failed"
            lane["output"] = output
            if code != 0:
                lane["notes"].append("missing-native-library lane failed")
    json_path = out_dir / "godot_workflow_report.json"
    md_path = out_dir / "godot_workflow_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(summarize_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")

    statuses = [report["doctor"]["status"]]
    statuses.extend(lane["status"] for lane in report["lanes"].values())
    return 0 if all(status in {"passed", "skipped"} for status in statuses) else 2


if __name__ == "__main__":
    raise SystemExit(main())
