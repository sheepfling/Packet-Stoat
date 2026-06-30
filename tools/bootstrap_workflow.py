#!/usr/bin/env python3
"""Host-smart bootstrap for the FastDIS Godot and Unreal routes."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import platform
import subprocess
import time

import godot_env
import host_capability_matrix
import load_local_env
import unity_env
import unreal_env
import workspace_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports"


def collect_legacy_output_dirs() -> list[dict[str, str]]:
    mappings = (
        (ROOT / "build" / "reports", ROOT / "artifacts" / "reports"),
        (ROOT / "build" / "benchmark_results", ROOT / "artifacts" / "benchmark_results"),
        (ROOT / "build" / "release_artifacts", ROOT / "artifacts" / "release_artifacts"),
        (ROOT / "build" / "verification_reports", ROOT / "artifacts" / "verification_reports"),
        (ROOT / "build" / "dist", ROOT / "artifacts" / "dist"),
        (ROOT / "dist", ROOT / "artifacts" / "dist"),
        (ROOT / "benchmark_reports", ROOT / "artifacts" / "reports"),
        (ROOT / "benchmark_results", ROOT / "artifacts" / "benchmark_results"),
        (ROOT / "release_artifacts", ROOT / "artifacts" / "release_artifacts"),
        (ROOT / "verification_reports", ROOT / "artifacts" / "verification_reports"),
    )
    rows: list[dict[str, str]] = []
    seen: set[Path] = set()
    for source, destination in mappings:
        if source in seen or not source.exists():
            continue
        seen.add(source)
        rows.append(
            {
                "source": source.relative_to(ROOT).as_posix(),
                "destination": destination.relative_to(ROOT).as_posix(),
            }
        )
    return rows


def host_payload() -> dict[str, str]:
    unity_install = unity_env.resolve_install()
    unity_overrides = unity_env.recommended_editor_overrides(unity_install)
    return {
        "platform": platform.system(),
        "arch": platform.machine(),
        "godot": godot_env.resolve_godot() or "",
        "scons": godot_env.resolve_scons() or "",
        "unity_editor": unity_install.editor_path if unity_install and unity_install.editor_path else "",
        "unity_install_root": unity_install.install_root if unity_install else "",
        "unity_override_editor": unity_overrides.get("FASTDIS_UNITY_EDITOR", ""),
        "unity_override_editor_dir": unity_overrides.get("FASTDIS_UNITY_EDITOR_DIR", ""),
        "unity_override_snippet": unity_override_snippet(
            {
                "platform": platform.system(),
                "unity_editor": unity_install.editor_path if unity_install and unity_install.editor_path else "",
                "unity_install_root": unity_install.install_root if unity_install else "",
                "unity_override_editor": unity_overrides.get("FASTDIS_UNITY_EDITOR", ""),
                "unity_override_editor_dir": unity_overrides.get("FASTDIS_UNITY_EDITOR_DIR", ""),
            }
        ),
        "unreal_host": unreal_env.platform_dir_name(),
    }


def run_lane(label: str, cmd: list[str], env: dict[str, str]) -> dict[str, object]:
    print("+", " ".join(cmd))
    started = time.monotonic()
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = completed.stdout or ""
    if output:
        print(output, end="")
    return {
        "label": label,
        "command": cmd,
        "returncode": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "output": output,
        "notes": [],
    }


def skip_lane(label: str, note: str) -> dict[str, object]:
    return {
        "label": label,
        "command": None,
        "returncode": None,
        "status": "skipped",
        "elapsed_seconds": 0.0,
        "output": "",
        "notes": [note],
    }


def plan_lane(label: str, found: str, action: str, note: str) -> dict[str, str]:
    return {
        "label": label,
        "found": found,
        "action": action,
        "note": note,
    }


def build_bootstrap_plan(args: argparse.Namespace, host: dict[str, str]) -> dict[str, dict[str, str]]:
    plan: dict[str, dict[str, str]] = {}

    if args.skip_godot:
        plan["godot"] = plan_lane(
            "godot",
            host["godot"] or host["scons"] or "missing",
            "skipped",
            "user requested skip",
        )
    elif host["godot"] or host["scons"]:
        plan["godot"] = plan_lane(
            "godot",
            host["godot"] or host["scons"] or "missing",
            "run",
            "tools/run_godot_report.py",
        )
    else:
        plan["godot"] = plan_lane(
            "godot",
            "missing",
            "skipped",
            "no Godot executable or scons was detected on this host",
        )

    if args.skip_unreal:
        plan["unreal"] = plan_lane(
            "unreal",
            "skipped by user",
            "skipped",
            "user requested skip",
        )
    else:
        installs = unreal_env.discover_installs()
        if not installs:
            plan["unreal"] = plan_lane(
                "unreal",
                "missing",
                "skipped",
                "no Unreal install was detected on this host",
            )
        else:
            found = ", ".join(install.version or install.editor_path for install in installs[:3])
            if len(installs) > 3:
                found = f"{found}, +{len(installs) - 3} more"
            plan["unreal"] = plan_lane(
                "unreal",
                found,
                "run",
                "tools/unreal_workflow.py full",
            )

    return plan


def selected_unreal_version(args: argparse.Namespace, installs: list[object]) -> str | None:
    version = getattr(args, "unreal_version", None)
    if version:
        return version
    versions = {
        getattr(install, "version", None)
        for install in installs
        if getattr(install, "version", None)
    }
    if len(versions) == 1:
        return next(iter(versions))
    return None


def next_command(args: argparse.Namespace, unreal_version: str | None) -> str:
    parts = ["fastdis", "bootstrap"]
    if getattr(args, "skip_godot", False):
        parts.append("--skip-godot")
    if getattr(args, "skip_unreal", False):
        parts.append("--skip-unreal")
    if unreal_version:
        parts.extend(["--unreal-version", unreal_version])
    return " ".join(parts)


def unity_override_snippet(host: dict[str, str]) -> list[str]:
    editor = host.get("unity_override_editor") or host.get("unity_editor") or ""
    editor_dir = host.get("unity_override_editor_dir") or host.get("unity_install_root") or ""
    if not editor or not editor_dir:
        return []
    system = str(host.get("platform") or "").lower()
    if system == "windows":
        editor_value = editor.replace("'", "''")
        editor_dir_value = editor_dir.replace("'", "''")
        return [
            "$env:FASTDIS_UNITY_EDITOR = '" + editor_value + "'",
            "$env:FASTDIS_UNITY_EDITOR_DIR = '" + editor_dir_value + "'",
        ]
    return [
        f"export FASTDIS_UNITY_EDITOR=\"{editor}\"",
        f"export FASTDIS_UNITY_EDITOR_DIR=\"{editor_dir}\"",
    ]


def cross_platform_policy(host_platform: str) -> list[str]:
    return workspace_manifest.cross_platform_policy(str(host_platform).lower())


def summarize_markdown(report: dict[str, object]) -> str:
    host = report["host"]
    unity_snippet = host.get("unity_override_snippet") or unity_override_snippet(host)
    lines = [
        "# FastDIS Bootstrap Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- host_platform: `{host['platform']}`",
        f"- host_arch: `{host['arch']}`",
        f"- unreal_host_label: `{host['unreal_host']}`",
        "",
        "| Lane | Status | Notes |",
        "| --- | --- | --- |",
        f"| godot | {report['lanes']['godot']['status']} | {'; '.join(report['lanes']['godot']['notes']) if report['lanes']['godot']['notes'] else 'none'} |",
        f"| unreal | {report['lanes']['unreal']['status']} | {'; '.join(report['lanes']['unreal']['notes']) if report['lanes']['unreal']['notes'] else 'none'} |",
        "",
        "## Host",
        "",
        f"- godot: `{host['godot'] or 'missing'}`",
        f"- scons: `{host['scons'] or 'missing'}`",
        f"- unity_editor: `{host.get('unity_editor') or 'missing'}`",
        f"- unity_install_root: `{host.get('unity_install_root') or 'missing'}`",
        "",
        "## Unity Session",
        "",
        f"- recommended_FASTDIS_UNITY_EDITOR: `{host.get('unity_override_editor') or 'missing'}`",
        f"- recommended_FASTDIS_UNITY_EDITOR_DIR: `{host.get('unity_override_editor_dir') or 'missing'}`",
        "- session_snippet:",
        "",
    ]
    if unity_snippet:
        lines.extend([f"  - {line}" for line in unity_snippet])
    else:
        lines.append("  - missing")
    lines.extend([
        "",
        "## Lane Commands",
        "",
    ])
    for lane in ("godot", "unreal"):
        command = report["lanes"][lane]["command"]
        lines.append(f"- {lane}: `{ ' '.join(command) if command else 'skipped' }`")
    lines.extend(["", "## Cross-Platform Policy", ""])
    for item in cross_platform_policy(str(host["platform"])):
        lines.append(f"- {item}")
    return "\n".join(lines)


def summarize_doctor(
    host: dict[str, str],
    plan: dict[str, dict[str, str]],
    args: argparse.Namespace,
    unreal_version: str | None,
    route_payload: dict[str, object],
) -> str:
    routes = route_payload.get("routes", [])
    if not isinstance(routes, list):
        routes = []
    relevant_routes = [
        route for route in routes
        if isinstance(route, dict) and workspace_manifest.route_bootstrap_capable(workspace_manifest.route_spec(str(route.get("name") or "")))
    ]
    legacy_outputs = collect_legacy_output_dirs()
    lines = [
        "FastDIS bootstrap doctor",
        "",
        f"- host_platform: `{host['platform']}`",
        f"- host_arch: `{host['arch']}`",
        f"- unreal_host_label: `{host['unreal_host']}`",
        f"- godot: `{host['godot'] or 'missing'}`",
        f"- scons: `{host['scons'] or 'missing'}`",
        f"- unity_editor: `{host['unity_editor'] or 'missing'}`",
        f"- unity_install_root: `{host['unity_install_root'] or 'missing'}`",
        f"- unreal_version: `{unreal_version or 'none'}`",
        f"- next_command: `{next_command(args, unreal_version)}`",
        f"- legacy_output_dirs: `{len(legacy_outputs)}`",
        "",
        "- cross_platform_policy:",
    ]
    for item in cross_platform_policy(str(host["platform"])):
        lines.append(f"  - {item}")
    lines.extend([
        "",
        "- local_output_policy:",
    ])
    if legacy_outputs:
        lines.append("  - warning: legacy local outputs were found under old build/ or repo-root locations")
        lines.append("  - remediation: remove or relocate these directories before trusting the local output tree")
        for row in legacy_outputs:
            lines.append(f"  - {row['source']} -> {row['destination']}")
    else:
        lines.append("  - status: using current artifacts/ layout only")
    lines.extend([
        "",
        "- godot:",
        f"  - found: `{plan['godot']['found']}`",
        f"  - action: `{plan['godot']['action']}`",
        f"  - note: {plan['godot']['note']}",
        "- unity:",
        f"  - editor: `{host['unity_editor'] or 'missing'}`",
        f"  - install_root: `{host['unity_install_root'] or 'missing'}`",
        f"  - recommended_FASTDIS_UNITY_EDITOR: `{host['unity_override_editor'] or 'missing'}`",
        f"  - recommended_FASTDIS_UNITY_EDITOR_DIR: `{host['unity_override_editor_dir'] or 'missing'}`",
        "  - session_snippet:",
    ])
    snippet = unity_override_snippet(host)
    if snippet:
        lines.extend([f"    {line}" for line in snippet])
    else:
        lines.append("    missing")
    lines.extend(["- route_activation:"])
    for route in relevant_routes:
        lines.append(f"  - {route['name']}: {route['activation']}")
        lines.append(f"    light_up: {route.get('light_up_command') or 'none'}")
        lines.append(f"    evidence: {', '.join(route.get('evidence_commands') or []) or 'none'}")
        lines.append(f"    missing_installs: {', '.join(route.get('missing_installs') or []) or 'none'}")
        lines.append(f"    install_commands: {', '.join(route.get('install_commands') or []) or 'none'}")
        lines.append(f"    missing_setup_steps: {', '.join(route.get('missing_setup_steps') or []) or 'none'}")
        lines.append(f"    remediation_steps: {', '.join(route.get('remediation_steps') or []) or 'none'}")
    lines.extend([
        "- unreal:",
        f"  - found: `{plan['unreal']['found']}`",
        f"  - action: `{plan['unreal']['action']}`",
        f"  - note: {plan['unreal']['note']}",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    parser.add_argument("--doctor", action="store_true", help="Print a one-screen bootstrap discovery summary and exit")
    parser.add_argument("--skip-godot", action="store_true", help="Skip the Godot bootstrap lane")
    parser.add_argument("--skip-unreal", action="store_true", help="Skip the Unreal bootstrap lane")
    parser.add_argument("--unreal-version", help="Explicit Unreal engine version for the Unreal lane")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    host = host_payload()
    installs = unreal_env.discover_installs()
    unreal_version = selected_unreal_version(args, installs)
    plan = build_bootstrap_plan(args, host)
    route_payload = host_capability_matrix.build_payload()
    if args.doctor:
        print(summarize_doctor(host, plan, args, unreal_version, route_payload))
        return 0

    lanes: dict[str, dict[str, object]] = {}

    if plan["godot"]["action"] == "run":
        lanes["godot"] = run_lane(
            "godot",
            godot_env.python_command() + ["tools/run_godot_report.py"],
            godot_env.build_env(),
        )
    else:
        lanes["godot"] = skip_lane("godot", plan["godot"]["note"])

    if plan["unreal"]["action"] == "run":
        cmd = unreal_env.python_command() + ["tools/unreal_workflow.py", "full"]
        if unreal_version:
            cmd.extend(["--engine-version", unreal_version])
        lanes["unreal"] = run_lane("unreal", cmd, unreal_env.build_env())
    else:
        lanes["unreal"] = skip_lane("unreal", plan["unreal"]["note"])

    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "host": host,
        "lanes": lanes,
    }
    json_path = out_dir / "bootstrap_report.json"
    md_path = out_dir / "bootstrap_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(summarize_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")

    failed = [lane for lane in lanes.values() if lane["status"] == "failed"]
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
