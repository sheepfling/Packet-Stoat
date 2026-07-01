#!/usr/bin/env python3
"""Import the GRILL Unity plugin into a scratch project and record startup evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform as host_platform
import shlex
import shutil
import subprocess
import tarfile
import time
from typing import Any

import grill_paths
import load_local_env
import prepare_grill_source_route
import run_unity_editor_tests
import run_unity_install_smoke
import run_unity_startup_probe
import unity_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN_ROOT = grill_paths.UNITY_PLUGIN
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _is_unitypackage(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".unitypackage"


def extract_unitypackage(package_path: Path, assets_dir: Path) -> None:
    with tarfile.open(package_path, "r:gz") as archive:
        members = archive.getmembers()
        prefixes = sorted({member.name.split("/", 1)[0] for member in members if "/" in member.name})
        for prefix in prefixes:
            pathname_member = next((member for member in members if member.name == f"{prefix}/pathname"), None)
            asset_member = next((member for member in members if member.name == f"{prefix}/asset"), None)
            asset_meta_member = next((member for member in members if member.name == f"{prefix}/asset.meta"), None)
            if pathname_member is None or asset_member is None:
                continue
            pathname_file = archive.extractfile(pathname_member)
            asset_file = archive.extractfile(asset_member)
            if pathname_file is None or asset_file is None:
                continue
            relative_path = pathname_file.read().decode("utf-8").strip().lstrip("/")
            if not relative_path:
                continue
            target = assets_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(asset_file.read())
            if asset_meta_member is not None:
                meta_file = archive.extractfile(asset_meta_member)
                if meta_file is not None:
                    target.with_name(target.name + ".meta").write_bytes(meta_file.read())


def create_project(project_dir: Path, plugin_source: Path, unity_version: str) -> None:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    (project_dir / "Assets").mkdir(parents=True)
    (project_dir / "Packages").mkdir(parents=True)
    (project_dir / "ProjectSettings").mkdir(parents=True)
    _write_text(project_dir / "Packages" / "manifest.json", json.dumps({"dependencies": {}}, indent=2) + "\n")
    _write_text(
        project_dir / "ProjectSettings" / "ProjectVersion.txt",
        f"m_EditorVersion: {unity_version}\nm_EditorVersionWithRevision: {unity_version}\n",
    )
    if _is_unitypackage(plugin_source):
        extract_unitypackage(plugin_source, project_dir / "Assets")
    else:
        shutil.copytree(plugin_source, project_dir / "Assets" / "GRILL_DIS", ignore=shutil.ignore_patterns(".git", ".DS_Store"))


def default_prepare_checkout(plugin_source: Path) -> bool:
    return plugin_source.expanduser().resolve() == DEFAULT_PLUGIN_ROOT.resolve()


def enable_required_builtin_modules(project_dir: Path) -> None:
    manifest_path = project_dir / "Packages" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dependencies = manifest.setdefault("dependencies", {})
    dependencies["com.unity.modules.imgui"] = "1.0.0"
    dependencies["com.unity.modules.physics"] = "1.0.0"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def startup_unity_command(editor: str, project_dir: Path, log_path: Path) -> list[str]:
    return [
        editor,
        "-accept-apiupdate",
        "-quit",
        "-projectPath",
        str(project_dir),
        "-logFile",
        str(log_path),
    ]


def run_startup_probe_report(
    install: unity_env.UnityInstall,
    *,
    out_dir: Path,
    timeout: int,
    project_dir: Path,
) -> dict[str, Any]:
    json_path = out_dir / "grill_unity_startup_probe.json"
    md_path = out_dir / "grill_unity_startup_probe.md"
    log_path = out_dir / "grill_unity_startup_probe.log"
    run_unity_startup_probe.create_project(project_dir)
    attempts = run_unity_startup_probe.startup_attempts(install, project_dir, out_dir)
    run_unity_install_smoke.clear_previous_artifacts(
        json_path,
        md_path,
        log_path,
        *[attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)],
    )

    attempt_summaries: list[dict[str, object]] = []
    selected_attempt: dict[str, object] | None = None
    remaining_timeout = timeout
    passed = False
    for index, attempt in enumerate(attempts):
        run_unity_install_smoke.clear_previous_artifacts(log_path, attempt["launcher_log"])
        attempt_timeout = run_unity_startup_probe.attempt_timeout_budget(remaining_timeout, attempts, index)
        started = time.monotonic()
        returncode, timed_out = run_unity_startup_probe.run_attempt(
            attempt["cmd"],
            env=attempt["env"] if isinstance(attempt.get("env"), dict) or attempt.get("env") is None else None,
            launcher_log_path=attempt["launcher_log"],
            timeout=attempt_timeout,
        )
        elapsed = round(time.monotonic() - started, 3)
        remaining_timeout = max(30, remaining_timeout - attempt_timeout)
        state = run_unity_install_smoke.project_state(project_dir)
        status = "pass" if state["library_exists"] else ("timeout" if timed_out else "fail")
        attempt_summaries.append(
            {
                "launch": attempt["launch"],
                "mode": attempt["mode"],
                "status": status,
                "returncode": returncode,
                "timed_out": timed_out,
                "elapsed_seconds": elapsed,
                "timeout_budget_seconds": attempt_timeout,
            }
        )
        selected_attempt = attempt
        if state["library_exists"]:
            break

    state = run_unity_install_smoke.project_state(project_dir)
    if passed:
        detail = "Unity created the blank scratch startup-probe project Library/ directory."
        status = "pass"
    else:
        hint = run_unity_startup_probe.launcher_failure_hint(
            *(attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path))
        )
        detail = (
            "Unity did not begin importing the blank scratch startup-probe project before the timeout; "
            "the project Library/ directory was never created."
            + (f" Diagnostic hint: {hint}." if hint else "")
        )
        status = "fail"

    report: dict[str, Any] = {
        "schema": "fastdis.unity_startup_probe.v1",
        "status": status,
        "requested_version": install.version,
        "unity_version": install.version,
        "host_platform": run_unity_install_smoke.host_label(),
        "detail": detail,
        "editor": install.editor_path,
        "project_dir": str(project_dir),
        "project_state": state,
        "log": str(log_path),
        "launch": None if selected_attempt is None else selected_attempt["launch"],
        "mode": None if selected_attempt is None else selected_attempt["mode"],
        "launcher_log": None if selected_attempt is None else str(selected_attempt["launcher_log"]),
        "attempts": attempt_summaries,
    }
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(run_unity_startup_probe.render_markdown(report), encoding="utf-8")
    return report


def startup_attempts(install: unity_env.UnityInstall, project_dir: Path, out_dir: Path) -> list[dict[str, object]]:
    log_path = out_dir / "grill_unity_import_smoke.log"
    attempts: list[dict[str, object]] = []
    interactive_cmd = startup_unity_command(install.editor_path or "", project_dir, log_path)
    if host_platform.system().lower() == "darwin":
        attempts.append(
            {
                "mode": "interactive",
                "launch": "login-shell",
                "cmd": ["/bin/zsh", "-lc", " ".join(shlex.quote(part) for part in interactive_cmd)],
                "env": None,
                "log": log_path,
                "launcher_log": out_dir / "grill_unity_import_smoke_login_shell_launcher.log",
            }
        )
        if install.editor_app_path:
            attempts.append(
                {
                    "mode": "interactive",
                    "launch": "launch-services",
                    "cmd": ["open", "-W", "-n", "-a", install.editor_app_path, "--args", *interactive_cmd[1:]],
                    "env": None,
                    "log": log_path,
                    "launcher_log": out_dir / "grill_unity_import_smoke_launch_services_launcher.log",
                }
            )
    return attempts


def import_log_analysis(log_path: Path) -> dict[str, Any]:
    analysis = run_unity_editor_tests.analyze_log(log_path)
    return analysis if isinstance(analysis, dict) else {}


def classify_report(
    *,
    startup_probe_report: dict[str, Any] | None,
    state: dict[str, object],
    log_analysis: dict[str, Any],
    hint: str | None,
) -> dict[str, str]:
    startup_status = None if startup_probe_report is None else str(startup_probe_report.get("status") or "")
    if startup_status and startup_status != "pass":
        return {
            "status": "blocked-host-startup",
            "failure_stage": "host-startup",
            "failure_reason": "unity-baseline-startup-failed",
            "detail": (
                "Unity could not reliably start and import a blank scratch project on the current host/editor route, "
                "so the GRILL plugin import route is not yet meaningfully testable here."
                + (f" Diagnostic hint: {hint}." if hint else "")
            ),
        }
    if not state.get("library_exists", False):
        return {
            "status": "fail",
            "failure_stage": "plugin-import",
            "failure_reason": "grill-project-import-never-started",
            "detail": (
                "Unity baseline startup succeeded, but the scratch project containing the GRILL plugin never created its "
                "Library/ directory."
                + (f" Diagnostic hint: {hint}." if hint else "")
            ),
        }
    if not state.get("script_assemblies_exists", False):
        return {
            "status": "fail",
            "failure_stage": "plugin-import",
            "failure_reason": "script-assemblies-missing",
            "detail": "Unity started importing the GRILL project, but no ScriptAssemblies directory was produced.",
        }
    log_status = str(log_analysis.get("status") or "")
    if log_status in {"compile_error", "package_resolution_failed", "unity_asset_meta_invalid", "blocked_license"}:
        return {
            "status": "fail",
            "failure_stage": "plugin-import",
            "failure_reason": str(log_analysis.get("code") or log_status),
            "detail": str(log_analysis.get("detail") or "Unity reported an import or compile failure while loading GRILL."),
        }
    return {
        "status": "pass",
        "failure_stage": "none",
        "failure_reason": "none",
        "detail": "Unity imported the scratch GRILL project and produced ScriptAssemblies.",
    }


def run_attempt(cmd: list[str], *, env: dict[str, str] | None, launcher_log_path: Path, timeout: int) -> tuple[int, bool]:
    launcher_log_path.parent.mkdir(parents=True, exist_ok=True)
    with launcher_log_path.open("w", encoding="utf-8") as handle:
        try:
            completed = subprocess.run(cmd, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT, text=True, timeout=timeout)
            return completed.returncode, False
        except subprocess.TimeoutExpired:
            return -15, True


def render_markdown(report: dict[str, object]) -> str:
    state = report.get("project_state") or {}
    lines = [
        "# GRILL Unity Import Smoke",
        "",
        f"- status: `{report['status']}`",
        f"- host_platform: `{report.get('host_platform', 'unknown')}`",
        f"- unity_version: `{report.get('unity_version', 'unknown')}`",
        f"- plugin_root: `{report.get('plugin_root', '')}`",
        f"- detail: `{report.get('detail', '')}`",
        f"- launch: `{report.get('launch', 'unknown')}`",
        f"- log: `{report.get('log', '')}`",
        f"- launcher_log: `{report.get('launcher_log', '')}`",
        f"- failure_stage: `{report.get('failure_stage', 'unknown')}`",
        f"- failure_reason: `{report.get('failure_reason', 'unknown')}`",
        "",
        "## Evidence",
        "",
        f"- project_state.library_exists: `{state.get('library_exists', False)}`",
        f"- project_state.package_cache_exists: `{state.get('package_cache_exists', False)}`",
        f"- project_state.script_assemblies_exists: `{state.get('script_assemblies_exists', False)}`",
        "",
        "## Startup Probe",
        "",
        f"- startup_probe.status: `{report.get('startup_probe', {}).get('status', 'unknown') if isinstance(report.get('startup_probe'), dict) else 'unknown'}`",
        f"- startup_probe.detail: `{report.get('startup_probe', {}).get('detail', '') if isinstance(report.get('startup_probe'), dict) else ''}`",
        "",
        "## Attempts",
        "",
    ]
    for attempt in report.get("attempts", []):
        if isinstance(attempt, dict):
            lines.append(
                f"- launch={attempt.get('launch', 'unknown')} status={attempt.get('status', 'unknown')} "
                f"returncode={attempt.get('returncode', 'unknown')} timed_out={attempt.get('timed_out', False)} "
                f"elapsed={attempt.get('elapsed_seconds', 0)}"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    parser.add_argument("--unity-version", default="6000.5")
    parser.add_argument("--project-dir", type=Path, help="Scratch Unity project path")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--prepare-checkout", dest="prepare_checkout", action="store_true", help="Fetch and switch the local GRILL Unity source checkout onto its expected benchmark branch before import.")
    parser.add_argument("--no-prepare-checkout", dest="prepare_checkout", action="store_false", help="Skip automatic GRILL Unity checkout preparation.")
    parser.set_defaults(prepare_checkout=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "grill_unity_import_smoke.json"
    md_path = args.out_dir / "grill_unity_import_smoke.md"
    log_path = args.out_dir / "grill_unity_import_smoke.log"
    project_dir = args.project_dir or (unity_env.work_root() / "grill_unity_import_smoke_project")
    startup_project_dir = unity_env.work_root() / "grill_unity_startup_probe_project"
    prepare_checkout = default_prepare_checkout(args.plugin_root) if args.prepare_checkout is None else bool(args.prepare_checkout)

    if not args.plugin_root.exists() or (not args.plugin_root.is_dir() and not _is_unitypackage(args.plugin_root)):
        report = {
            "schema": "fastdis.grill_unity_import_smoke.v1",
            "status": "skip",
            "requested_version": args.unity_version,
            "host_platform": run_unity_install_smoke.host_label(),
            "detail": "GRILL plugin source not found",
            "plugin_root": str(args.plugin_root),
            "log": str(log_path),
            "project_dir": str(project_dir),
            "project_state": run_unity_install_smoke.project_state(project_dir),
            "attempts": [],
        }
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {json_path}")
        print(f"Markdown: {md_path}")
        return 2

    checkout_prepare: dict[str, Any] | None = None
    if prepare_checkout and args.plugin_root.is_dir():
        checkout_prepare = prepare_grill_source_route.build_report(
            [
                prepare_grill_source_route.RepoSpec(
                    key="unity_plugin",
                    label="GRILL Unity plugin",
                    path=args.plugin_root.expanduser().resolve(),
                    target_branch="main",
                )
            ],
            fetch=True,
            allow_dirty=False,
            update_submodules=False,
        )
        prep_rows = checkout_prepare.get("repos") if isinstance(checkout_prepare.get("repos"), list) else []
        failed = [row for row in prep_rows if isinstance(row, dict) and row.get("status") != "prepared"]
        if failed:
            report = {
                "schema": "fastdis.grill_unity_import_smoke.v1",
                "status": "checkout-prepare-failed",
                "requested_version": args.unity_version,
                "host_platform": run_unity_install_smoke.host_label(),
                "detail": "GRILL Unity checkout preparation failed before the import smoke ran.",
                "plugin_root": str(args.plugin_root),
                "log": str(log_path),
                "project_dir": str(project_dir),
                "project_state": run_unity_install_smoke.project_state(project_dir),
                "attempts": [],
                "failure_stage": "checkout-prepare",
                "failure_reason": "checkout-prepare-failed",
                "checkout_prepare": checkout_prepare,
            }
            json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            md_path.write_text(render_markdown(report), encoding="utf-8")
            print(f"JSON: {json_path}")
            print(f"Markdown: {md_path}")
            return 1

    install = unity_env.resolve_install(args.unity_version)
    if install is None or not install.editor_path:
        report = {
            "schema": "fastdis.grill_unity_import_smoke.v1",
            "status": "skip",
            "requested_version": args.unity_version,
            "host_platform": run_unity_install_smoke.host_label(),
            "detail": "Unity editor not found",
            "plugin_root": str(args.plugin_root),
            "log": str(log_path),
            "project_dir": str(project_dir),
            "project_state": run_unity_install_smoke.project_state(project_dir),
            "attempts": [],
        }
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {json_path}")
        print(f"Markdown: {md_path}")
        return 2

    startup_probe_report = run_startup_probe_report(
        install,
        out_dir=args.out_dir,
        timeout=args.timeout,
        project_dir=startup_project_dir,
    )
    if startup_probe_report.get("status") != "pass":
        classification = classify_report(
            startup_probe_report=startup_probe_report,
            state=run_unity_install_smoke.project_state(project_dir),
            log_analysis={},
            hint=run_unity_startup_probe.launcher_failure_hint(
                *(Path(str(attempt.get("launcher_log"))) for attempt in startup_probe_report.get("attempts", []) if isinstance(attempt, dict) and attempt.get("launcher_log"))
            ),
        )
        report = {
            "schema": "fastdis.grill_unity_import_smoke.v1",
            "status": classification["status"],
            "requested_version": args.unity_version,
            "unity_version": install.version,
            "host_platform": run_unity_install_smoke.host_label(),
            "plugin_root": str(args.plugin_root),
            "detail": classification["detail"],
            "failure_stage": classification["failure_stage"],
            "failure_reason": classification["failure_reason"],
            "editor": install.editor_path,
            "project_dir": str(project_dir),
            "project_state": run_unity_install_smoke.project_state(project_dir),
            "startup_probe": startup_probe_report,
            "log": str(log_path),
            "launch": startup_probe_report.get("launch"),
            "mode": startup_probe_report.get("mode"),
            "launcher_log": startup_probe_report.get("launcher_log"),
            "attempts": [],
        }
        if checkout_prepare is not None:
            report["checkout_prepare"] = checkout_prepare
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {json_path}")
        print(f"Markdown: {md_path}")
        return 1

    create_project(project_dir, args.plugin_root, install.version)
    enable_required_builtin_modules(project_dir)
    attempts = startup_attempts(install, project_dir, args.out_dir)
    run_unity_install_smoke.clear_previous_artifacts(
        json_path,
        md_path,
        log_path,
        *[attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path)],
    )

    attempt_summaries: list[dict[str, object]] = []
    selected_attempt: dict[str, object] | None = None
    for attempt in attempts:
        run_unity_install_smoke.clear_previous_artifacts(log_path, attempt["launcher_log"])
        started = time.monotonic()
        returncode, timed_out = run_attempt(
            attempt["cmd"],
            env=attempt["env"] if isinstance(attempt.get("env"), dict) or attempt.get("env") is None else None,
            launcher_log_path=attempt["launcher_log"],
            timeout=args.timeout,
        )
        elapsed = round(time.monotonic() - started, 3)
        state = run_unity_install_smoke.project_state(project_dir)
        status = "pass" if state["library_exists"] else ("timeout" if timed_out else "fail")
        attempt_summaries.append(
            {
                "launch": attempt["launch"],
                "mode": attempt["mode"],
                "status": status,
                "returncode": returncode,
                "timed_out": timed_out,
                "elapsed_seconds": elapsed,
            }
        )
        selected_attempt = attempt
        if state["library_exists"]:
            break

    state = run_unity_install_smoke.project_state(project_dir)
    hint = run_unity_startup_probe.launcher_failure_hint(
        *(attempt["launcher_log"] for attempt in attempts if isinstance(attempt.get("launcher_log"), Path))
    )
    classification = classify_report(
        startup_probe_report=startup_probe_report,
        state=state,
        log_analysis=import_log_analysis(log_path),
        hint=hint,
    )

    report = {
        "schema": "fastdis.grill_unity_import_smoke.v1",
        "status": classification["status"],
        "requested_version": args.unity_version,
        "unity_version": install.version,
        "host_platform": run_unity_install_smoke.host_label(),
        "plugin_root": str(args.plugin_root),
        "detail": classification["detail"],
        "failure_stage": classification["failure_stage"],
        "failure_reason": classification["failure_reason"],
        "editor": install.editor_path,
        "project_dir": str(project_dir),
        "project_state": state,
        "startup_probe": startup_probe_report,
        "log": str(log_path),
        "launch": None if selected_attempt is None else selected_attempt["launch"],
        "mode": None if selected_attempt is None else selected_attempt["mode"],
        "launcher_log": None if selected_attempt is None else str(selected_attempt["launcher_log"]),
        "attempts": attempt_summaries,
    }
    if checkout_prepare is not None:
        report["checkout_prepare"] = checkout_prepare
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if classification["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
