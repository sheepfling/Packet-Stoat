#!/usr/bin/env python3
"""Host-smart bootstrap for the FastDIS Godot and Unreal routes."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
from pathlib import Path
import platform
import subprocess
import time

import godot_env
import host_capability_matrix
import load_local_env
import prepare_grill_source_route
from report_envelope import write_json_report
import unity_env
import unreal_env
import workspace_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports"
BOOTSTRAP_PROFILES = ("fastdis-dev", "comparison")
GRILL_REPO_URLS = {
    "unreal_plugin": "https://github.com/AF-GRILL/DISPluginForUnreal",
    "unreal_example": "https://github.com/AF-GRILL/DISForUnrealExample",
    "unity_plugin": "https://github.com/AF-GRILL/DISPluginForUnity",
    "unity_example": "https://github.com/AF-GRILL/DISForUnityExample",
}


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


def default_grill_repo_specs() -> list[prepare_grill_source_route.RepoSpec]:
    return prepare_grill_source_route.default_repo_specs()


def _git_output(path: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout or ""


def _submodules_ready(path: Path) -> bool:
    if not (path / ".gitmodules").is_file():
        return True
    output = _git_output(path, ["submodule", "status"])
    rows = [line.strip() for line in output.splitlines() if line.strip()]
    if not rows:
        return False
    return all(not row.startswith("-") for row in rows)


def grill_checkout_state() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in default_grill_repo_specs():
        path = spec.path
        exists = path.is_dir()
        is_git_checkout = bool(exists and (path / ".git").exists())
        submodules_ready = bool(is_git_checkout and _submodules_ready(path)) if exists else False
        rows.append(
            {
                "key": spec.key,
                "label": spec.label,
                "path": str(path),
                "relative_path": path.relative_to(ROOT).as_posix() if path.is_absolute() and str(path).startswith(str(ROOT)) else str(path),
                "target_branch": spec.target_branch,
                "exists": exists,
                "is_git_checkout": is_git_checkout,
                "submodules_ready": submodules_ready,
                "required_for_profiles": ["comparison"],
            }
        )
    return rows


def clone_command_for_row(row: dict[str, object]) -> str:
    key = str(row["key"])
    recurse = " --recurse-submodules" if "example" in key else ""
    return f"git clone{recurse} {GRILL_REPO_URLS[key]} {row['relative_path']}"


def acquire_comparison_externals(grill_state: list[dict[str, object]]) -> dict[str, object]:
    commands: list[dict[str, object]] = []
    cloned: list[str] = []
    for row in grill_state:
        if row.get("exists") and row.get("submodules_ready", True):
            continue
        key = str(row["key"])
        repo_url = GRILL_REPO_URLS[key]
        target_path = ROOT / str(row["relative_path"]).replace("/", "\\")
        if not row.get("exists"):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            clone_cmd = ["git", "clone"]
            if "example" in key:
                clone_cmd.append("--recurse-submodules")
            clone_cmd.extend([repo_url, str(target_path)])
            completed = subprocess.run(
                clone_cmd,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            commands.append(
                {
                    "cmd": clone_cmd,
                    "returncode": completed.returncode,
                    "output": completed.stdout or "",
                }
            )
            if completed.returncode != 0:
                return {
                    "status": "failed",
                    "commands": commands,
                    "cloned": cloned,
                    "detail": f"failed to clone {key}",
                }
            cloned.append(key)
    prep_report = prepare_grill_source_route.build_report(
        default_grill_repo_specs(),
        fetch=True,
        allow_dirty=False,
        update_submodules=True,
    )
    return {
        "status": "prepared" if prep_report.get("status") == "pass" else "partial",
        "commands": commands,
        "cloned": cloned,
        "detail": "comparison externals acquired",
        "prepare_report": prep_report,
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


def comparison_plan(args: argparse.Namespace, grill_state: list[dict[str, object]]) -> dict[str, object]:
    if args.profile != "comparison":
        return {
            "enabled": False,
            "action": "skipped",
            "note": "comparison profile not selected",
            "missing_repos": [],
            "ready_repos": [str(row["key"]) for row in grill_state if row.get("exists")],
            "prepare_command": None,
            "clone_commands": [],
        }
    missing = [row for row in grill_state if not row.get("exists")]
    incomplete = [row for row in grill_state if row.get("exists") and not row.get("submodules_ready", True)]
    clone_commands = [
        clone_command_for_row(row)
        for row in [*missing, *incomplete]
    ]
    note = (
        "comparison externals are present"
        if not missing and not incomplete
        else "comparison profile requires AF-GRILL external source checkouts and initialized submodules before competitor lanes can run"
    )
    return {
        "enabled": True,
        "action": "ready" if not missing and not incomplete else ("prepare-submodules" if incomplete and not missing else "acquire-externals"),
        "note": note,
        "missing_repos": [str(row["key"]) for row in missing],
        "incomplete_repos": [str(row["key"]) for row in incomplete],
        "ready_repos": [str(row["key"]) for row in grill_state if row.get("exists")],
        "prepare_command": "python tools/prepare_grill_source_route.py",
        "clone_commands": clone_commands,
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
    elif args.profile == "comparison":
        installs = unreal_env.discover_installs()
        if not installs:
            plan["unreal"] = plan_lane(
                "unreal",
                "missing",
                "skipped",
                "comparison profile still needs a local Unreal install for FastDIS/GRILL Unreal lanes",
            )
        else:
            found = ", ".join(install.version or install.editor_path for install in installs[:3])
            if len(installs) > 3:
                found = f"{found}, +{len(installs) - 3} more"
            plan["unreal"] = plan_lane(
                "unreal",
                found,
                "run",
                "tools/unreal_workflow.py full and GRILL comparison lanes",
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
    parts = ["packet-stoat", "bootstrap"]
    if getattr(args, "profile", "fastdis-dev") != "fastdis-dev":
        parts.extend(["--profile", args.profile])
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
    profile = str(report.get("profile") or "fastdis-dev")
    comparison = report.get("comparison") if isinstance(report.get("comparison"), dict) else {}
    unity_snippet = host.get("unity_override_snippet") or unity_override_snippet(host)
    lines = [
        "# FastDIS Bootstrap Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- profile: `{profile}`",
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
    if profile == "comparison":
        lines.extend(["", "## Comparison Route", ""])
        lines.append(f"- action: `{comparison.get('action') or 'unknown'}`")
        lines.append(f"- note: {comparison.get('note') or 'none'}")
        missing = comparison.get("missing_repos") or []
        lines.append(f"- missing_repos: `{', '.join(missing) or 'none'}`")
        lines.append(f"- prepare_command: `{comparison.get('prepare_command') or 'none'}`")
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
    grill_state: list[dict[str, object]],
    comparison: dict[str, object],
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
        f"- profile: `{args.profile}`",
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
        "- bootstrap_profiles:",
        "  - fastdis-dev: build and test FastDIS-owned routes without competitor externals",
        "  - comparison: acquire AF-GRILL externals and light up competitor/storefront comparison lanes",
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
        "- comparison_route:",
        f"  - enabled: `{comparison.get('enabled')}`",
        f"  - action: `{comparison.get('action')}`",
        f"  - note: {comparison.get('note')}",
        f"  - prepare_command: `{comparison.get('prepare_command') or 'none'}`",
        "  - af_grill_externals:",
    ])
    for row in grill_state:
        status = "ready" if row.get("is_git_checkout") else ("present" if row.get("exists") else "missing")
        if row.get("exists") and not row.get("submodules_ready", True):
            status = "submodules-pending"
        lines.append(
            f"    - {row['key']}: status={status}; path={row['relative_path']}; branch={row['target_branch']}; required_for={','.join(row.get('required_for_profiles') or [])}"
        )
    clone_commands = comparison.get("clone_commands") or []
    lines.append("  - clone_commands:")
    if clone_commands:
        for command in clone_commands:
            lines.append(f"    - {command}")
    else:
        lines.append("    - none")
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
    parser.add_argument("--profile", choices=BOOTSTRAP_PROFILES, default="fastdis-dev", help="Bootstrap profile to light up")
    parser.add_argument("--acquire-externals", action="store_true", help="Clone and prepare AF-GRILL external repos needed for the comparison profile")
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
    grill_state = grill_checkout_state()
    acquisition_report: dict[str, object] | None = None
    if args.acquire_externals:
        if args.profile != "comparison":
            raise SystemExit("--acquire-externals requires --profile comparison")
        acquisition_report = acquire_comparison_externals(grill_state)
        grill_state = grill_checkout_state()
    comparison = comparison_plan(args, grill_state)
    route_payload = host_capability_matrix.build_payload()
    if args.doctor:
        print(summarize_doctor(host, plan, args, unreal_version, route_payload, grill_state, comparison))
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
        "profile": args.profile,
        "host": host,
        "lanes": lanes,
        "comparison": comparison,
        "acquisition": acquisition_report,
    }
    json_path = out_dir / "bootstrap_report.json"
    md_path = out_dir / "bootstrap_report.md"
    write_json_report(
        json_path,
        report,
        schema="fastdis.bootstrap_report.v1",
        producer="tools/bootstrap_workflow.py",
        generated_at_field="generated_at",
    )
    md_path.write_text(summarize_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")

    failed = [lane for lane in lanes.values() if lane["status"] == "failed"]
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
