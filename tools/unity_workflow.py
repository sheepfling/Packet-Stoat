#!/usr/bin/env python3
"""Operator-facing Unity workflow wrapper for discovery, demo proof, package checks, and reports."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess

import check_unity_parity
import grill_paths
import load_local_env
import run_unity_install_smoke
import unity_env


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "packages" / "unity" / "com.sheepfling.fastdis"
DEFAULT_REPORT_DIR = ROOT / "build" / "reports"
INSTALL_MATRIX_HOSTS = ("macos", "windows", "linux")
PARITY_MILESTONES = ("alpha6", "alpha7", "alpha8", "beta1")


def host_native_key() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos_dylib"
    if system == "windows":
        return "windows_dll"
    return "linux_so"


def host_install_label() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def run_step(cmd: list[str], *, preserve_unity_login: bool = False) -> int:
    print("+", " ".join(cmd))
    if preserve_unity_login:
        old_preserve = os.environ.get("FASTDIS_UNITY_PRESERVE_HOME")
        os.environ["FASTDIS_UNITY_PRESERVE_HOME"] = "1"
        try:
            env = unity_env.build_env()
        finally:
            if old_preserve is None:
                os.environ.pop("FASTDIS_UNITY_PRESERVE_HOME", None)
            else:
                os.environ["FASTDIS_UNITY_PRESERVE_HOME"] = old_preserve
    else:
        env = unity_env.build_env()
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    return completed.returncode


def package_state() -> dict[str, bool]:
    required = {
        "package_json": PACKAGE_ROOT / "package.json",
        "readme": PACKAGE_ROOT / "README.md",
        "runtime_asmdef": PACKAGE_ROOT / "Runtime" / "FastDIS.Runtime.asmdef",
        "editor_asmdef": PACKAGE_ROOT / "Editor" / "FastDIS.Editor.asmdef",
        "runtime_tests": PACKAGE_ROOT / "Tests" / "Runtime" / "FastDIS.Runtime.Tests.asmdef",
        "editor_tests": PACKAGE_ROOT / "Tests" / "Editor" / "FastDIS.Editor.Tests.asmdef",
        "docs": PACKAGE_ROOT / "Documentation~" / "index.md",
        "minimal_sample": PACKAGE_ROOT / "Samples~" / "Minimal Receiver" / "README.md",
        "udp_sample": PACKAGE_ROOT / "Samples~" / "UDP Loopback" / "README.md",
        "orientation_sample": PACKAGE_ROOT / "Samples~" / "Orientation Verification" / "README.md",
        "lattice_sample": PACKAGE_ROOT / "Samples~" / "Lattice Lab Bridge" / "README.md",
    }
    return {name: path.exists() for name, path in required.items()}


def staged_native_state() -> dict[str, bool]:
    return {
        "windows_dll": (PACKAGE_ROOT / "Runtime" / "Plugins" / "Windows" / "x86_64" / "fastdis.dll").is_file(),
        "macos_dylib": (PACKAGE_ROOT / "Runtime" / "Plugins" / "macOS" / "libfastdis.dylib").is_file(),
        "linux_so": (PACKAGE_ROOT / "Runtime" / "Plugins" / "Linux" / "x86_64" / "libfastdis.so").is_file(),
    }


def truthy_env(name: str) -> bool:
    return os.environ.get(name) in {"1", "true", "TRUE", "yes", "YES"}


def unity_runtime_launcher_mode() -> str:
    if platform.system().lower() == "darwin" and not truthy_env("FASTDIS_UNITY_BATCHMODE"):
        return "macos-login-shell-interactive"
    if truthy_env("FASTDIS_UNITY_FORCE_NOGRAPHICS"):
        return "batchmode-nographics"
    return "batchmode"


def latest_runtime_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_runtime_verification.json")


def _read_json_report(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def latest_bridge_probe_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_csharp_bridge_probe.json")


def latest_orientation_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_orientation_verification.json")


def latest_startup_probe_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_startup_probe.json")


def latest_install_smoke_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    host_path = out_dir / f"unity_install_smoke_{host_install_label()}.json"
    return _read_json_report(host_path) or _read_json_report(out_dir / "unity_install_smoke.json")


def latest_native_matrix_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_native_matrix.json")


def latest_install_matrix_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_install_matrix.json")


def latest_host_matrix_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_host_matrix.json")


def latest_signoff_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_signoff_report.json")


def latest_cross_engine_equivalence_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_cross_engine_equivalence.json")


def latest_head_to_head_benchmark_report(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object] | None:
    return _read_json_report(out_dir / "unity_head_to_head_benchmark.json")


def _report_error_list(report: dict[str, object] | None, namespace: str) -> list[str]:
    if report is None:
        return []
    validation = report.get("validation")
    if not isinstance(validation, dict):
        return []
    errors = validation.get(namespace)
    if not isinstance(errors, list):
        return []
    return [str(error) for error in errors]


def install_smoke_matrix_reports(out_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, dict[str, object]]:
    reports: dict[str, dict[str, object]] = {}
    for host in INSTALL_MATRIX_HOSTS:
        report = _read_json_report(out_dir / f"unity_install_smoke_{host}.json")
        if report is not None:
            reports[host] = report
    generic = _read_json_report(out_dir / "unity_install_smoke.json")
    if generic is not None:
        generic_host = str(generic.get("host_platform") or host_install_label())
        reports.setdefault(generic_host, generic)
    return reports


def install_smoke_failure_fields(report: dict[str, object]) -> tuple[str, str]:
    stage = report.get("failure_stage")
    reason = report.get("failure_reason")
    if isinstance(stage, str) and isinstance(reason, str):
        return stage, reason
    project_state = report.get("project_state")
    if isinstance(project_state, dict) and not project_state.get("library_exists", False):
        return "host-startup", "project-import-never-started"
    if not report.get("package_cache_locations"):
        return "package-install", "package-cache-missing"
    return "none", "none"


def doctor_payload(version: str | None, report_dir: Path = DEFAULT_REPORT_DIR) -> dict[str, object]:
    install = unity_env.resolve_install(version)
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str, *, warn: bool = False) -> None:
        checks.append({"name": name, "status": "ok" if ok else ("warn" if warn else "fail"), "detail": detail})

    add_check("unity editor", install is not None and install.editor_path is not None, install.editor_path if install and install.editor_path else "missing Unity editor")
    if install is not None:
        add_check("unity version", True, install.version)
        for quirk in install.quirks:
            add_check(f"quirk:{quirk}", False, install.install_root, warn=True)

    work_ok, work_detail = unity_env.path_writable(unity_env.work_root())
    add_check("permission:work_root", work_ok, work_detail)
    package_ok, package_detail = unity_env.path_writable(PACKAGE_ROOT / "Runtime" / "Plugins")
    add_check("permission:package_plugins", package_ok, package_detail)

    for name, ok in package_state().items():
        add_check(f"package:{name}", ok, str(PACKAGE_ROOT))

    package = package_state()
    native_matrix_report = latest_native_matrix_report(report_dir)
    if native_matrix_report:
        raw_native_matrix_status = str(native_matrix_report.get("status") or "not_run")
        native_matrix_status = {"pass": "pass", "fail": "fail"}.get(raw_native_matrix_status, "fail")
        native_matrix_targets = [
            target
            for target, data in (native_matrix_report.get("targets") or {}).items()
            if isinstance(data, dict) and str(data.get("status")) == "pass"
        ]
    else:
        native_matrix_status = "not_run"
        native_matrix_targets = []
    native = staged_native_state()
    current_native_ok = native[host_native_key()]
    add_check("native:current-platform", current_native_ok, host_native_key(), warn=True)
    add_check("native:macos", native["macos_dylib"], "Runtime/Plugins/macOS/libfastdis.dylib", warn=True)
    add_check("native:windows", native["windows_dll"], "Runtime/Plugins/Windows/x86_64/fastdis.dll", warn=True)
    add_check("native:linux", native["linux_so"], "Runtime/Plugins/Linux/x86_64/libfastdis.so", warn=True)
    if native_matrix_report:
        native_matrix_detail = f"{native_matrix_status}; targets={','.join(native_matrix_targets) or 'none'}; report={report_dir / 'unity_native_matrix.json'}"
    else:
        native_matrix_detail = "no build/reports/unity_native_matrix.json yet"
    add_check("runtime:native-matrix", native_matrix_status == "pass", native_matrix_detail, warn=True)
    launcher_mode = unity_runtime_launcher_mode()
    add_check("runtime:launcher", True, launcher_mode)
    if platform.system().lower() == "darwin":
        add_check(
            "runtime:macos-license-path",
            not truthy_env("FASTDIS_UNITY_BATCHMODE") and not truthy_env("FASTDIS_UNITY_FORCE_NOGRAPHICS"),
            "default login-shell interactive launcher avoids Unity Personal headless entitlement",
            warn=True,
        )
    if truthy_env("FASTDIS_UNITY_BATCHMODE"):
        add_check(
            "env:FASTDIS_UNITY_BATCHMODE",
            False,
            "forces batchmode; Unity Personal may fail with com.unity.editor.headless missing",
            warn=True,
        )
    if truthy_env("FASTDIS_UNITY_FORCE_NOGRAPHICS"):
        add_check(
            "env:FASTDIS_UNITY_FORCE_NOGRAPHICS",
            False,
            "forces -nographics; Unity Personal may fail with com.unity.editor.headless missing",
            warn=True,
        )

    runtime_report = latest_runtime_report(report_dir)
    bridge_probe = latest_bridge_probe_report(report_dir)
    orientation_report = latest_orientation_report(report_dir)
    startup_probe_report = latest_startup_probe_report(report_dir)
    install_smoke_report = latest_install_smoke_report(report_dir)
    install_matrix_report = latest_install_matrix_report(report_dir)
    host_matrix_report = latest_host_matrix_report(report_dir)
    signoff_report = latest_signoff_report(report_dir)
    cross_engine_report = latest_cross_engine_equivalence_report(report_dir)
    head_to_head_report = latest_head_to_head_benchmark_report(report_dir)
    parity_reports: dict[str, dict[str, object]] = {}
    parity_errors: dict[str, str] = {}
    for milestone in PARITY_MILESTONES:
        try:
            parity_reports[milestone] = check_unity_parity.build_report(ROOT / "docs" / "research" / "unity_grill_parity.yaml", milestone)
        except Exception as exc:
            parity_errors[milestone] = str(exc)
    install_matrix_reports = install_smoke_matrix_reports(report_dir)
    runtime_status = str(runtime_report.get("overall_status")) if runtime_report else "not_run"
    bridge_status = str(bridge_probe.get("overall_status")) if bridge_probe else "not_run"
    orientation_status = str(orientation_report.get("status")) if orientation_report else "not_run"
    startup_probe_status = str(startup_probe_report.get("status")) if startup_probe_report else "not_run"
    install_status = str(install_smoke_report.get("status")) if install_smoke_report else "not_run"
    install_matrix_hosts = [host for host in INSTALL_MATRIX_HOSTS if host in install_matrix_reports and str(install_matrix_reports[host].get("status")) == "pass"]
    if install_matrix_report:
        raw_install_matrix_status = str(install_matrix_report.get("overall_status") or "not_run")
        install_matrix_status = {
            "cross-host-ready": "pass",
            "cross-host-incomplete": "incomplete",
            "cross-host-failed": "fail",
            "no-host-reports": "not_run",
        }.get(raw_install_matrix_status, "fail")
    else:
        if all(host in install_matrix_hosts for host in INSTALL_MATRIX_HOSTS):
            install_matrix_status = "pass"
        elif install_matrix_hosts:
            install_matrix_status = "incomplete"
        elif install_matrix_reports:
            install_matrix_status = "fail"
        else:
            install_matrix_status = "not_run"
    if host_matrix_report:
        raw_host_matrix_status = str(host_matrix_report.get("overall_status") or "not_run")
        host_matrix_status = {
            "cross-host-ready": "pass",
            "cross-host-incomplete": "incomplete",
            "cross-host-failed": "fail",
            "no-host-reports": "not_run",
        }.get(raw_host_matrix_status, "fail")
    else:
        host_matrix_status = "not_run"
    if signoff_report:
        raw_signoff_status = str(signoff_report.get("overall_status") or "not_run")
        signoff_status = {
            "ready": "pass",
            "not-fully-signed-off": "incomplete",
        }.get(raw_signoff_status, "fail")
    else:
        signoff_status = "not_run"
    if cross_engine_report:
        raw_cross_engine_status = str(cross_engine_report.get("status") or "not_run")
        cross_engine_status = {
            "complete": "pass",
            "incomplete": "incomplete",
        }.get(raw_cross_engine_status, "fail")
    else:
        cross_engine_status = "not_run"
    if head_to_head_report:
        raw_head_to_head_status = str(head_to_head_report.get("status") or "not_run")
        head_to_head_status = {
            "complete": "pass",
            "incomplete": "incomplete",
        }.get(raw_head_to_head_status, "fail")
    else:
        head_to_head_status = "not_run"
    demo_status = "pass" if runtime_status == "pass" and orientation_status == "pass" and install_status == "pass" else (runtime_status if runtime_report else "not_run")
    if runtime_report:
        first_lane = (runtime_report.get("lanes") or [{}])[0]
        runtime_detail = f"{runtime_status}; {first_lane.get('platform', 'unknown')} via {first_lane.get('launch', 'unknown')}"
    else:
        runtime_detail = "no build/reports/unity_runtime_verification.json yet"
    add_check("runtime:last-report", runtime_status == "pass", runtime_detail, warn=True)
    if orientation_report:
        orientation_detail = f"{orientation_status}; scene={orientation_report.get('scene', 'unknown')}"
    else:
        orientation_detail = "no build/reports/unity_orientation_verification.json yet"
    add_check("runtime:orientation-scene", orientation_status == "pass", orientation_detail, warn=True)
    if startup_probe_report:
        startup_detail = (
            f"{startup_probe_report.get('status', 'unknown')}; "
            f"launch={startup_probe_report.get('launch', 'unknown')}; "
            f"library_exists={(startup_probe_report.get('project_state') or {}).get('library_exists', False)}"
        )
        add_check("runtime:startup-probe", startup_probe_report.get("status") == "pass", startup_detail, warn=True)
    else:
        add_check("runtime:startup-probe", False, "no build/reports/unity_startup_probe.json yet", warn=True)
    if install_smoke_report:
        install_failure_stage, install_failure_reason = install_smoke_failure_fields(install_smoke_report)
        add_check(
            "runtime:install-host-health",
            install_failure_stage in {"none", "runtime-proof", "package-install"},
            (
                f"stage={install_failure_stage}; reason={install_failure_reason}; "
                f"log={install_smoke_report.get('log', report_dir / 'unity_install_smoke.log')}"
            ),
            warn=True,
        )
        install_detail = (
            f"{install_status}; host={install_smoke_report.get('host_platform', 'unknown')}; "
            f"stage={install_failure_stage}; "
            f"reason={install_failure_reason}; "
            f"repo={install_smoke_report.get('repo_root', 'unknown')}"
        )
    else:
        add_check(
            "runtime:install-host-health",
            False,
            f"stage=missing; reason=no build/reports/unity_install_smoke.json yet; log={report_dir / 'unity_install_smoke.log'}",
            warn=True,
        )
        install_detail = "no build/reports/unity_install_smoke.json yet"
    add_check("runtime:install-smoke", install_status == "pass", install_detail, warn=True)
    matrix_missing = [host for host in INSTALL_MATRIX_HOSTS if host not in install_matrix_hosts]
    matrix_detail = f"{install_matrix_status}; passed={','.join(install_matrix_hosts) or 'none'}; missing={','.join(matrix_missing) or 'none'}"
    add_check("runtime:install-smoke-matrix", install_matrix_status == "pass", matrix_detail, warn=True)
    if install_matrix_report:
        add_check(
            "runtime:install-signoff",
            install_matrix_status == "pass",
            f"{install_matrix_report.get('overall_status', 'unknown')}; report={report_dir / 'unity_install_matrix.json'}",
            warn=True,
        )
    if host_matrix_report:
        ready_platforms = host_matrix_report.get("ready_platforms") or []
        if not isinstance(ready_platforms, list):
            ready_platforms = []
        add_check(
            "runtime:host-bundle-matrix",
            host_matrix_status == "pass",
            f"{host_matrix_report.get('overall_status', 'unknown')}; ready={','.join(str(item) for item in ready_platforms) or 'none'}; report={report_dir / 'unity_host_matrix.json'}",
            warn=True,
        )
    else:
        add_check("runtime:host-bundle-matrix", False, "no build/reports/unity_host_matrix.json yet", warn=True)
    if signoff_report:
        add_check(
            "runtime:signoff",
            signoff_status == "pass",
            f"{signoff_report.get('overall_status', 'unknown')}; report={report_dir / 'unity_signoff_report.json'}",
            warn=True,
        )
    else:
        add_check("runtime:signoff", False, "no build/reports/unity_signoff_report.json yet", warn=True)
    if bridge_probe:
        bridge_detail = f"{bridge_status}; native={bridge_probe.get('native_library', 'unknown')}"
    else:
        bridge_detail = "no build/reports/unity_csharp_bridge_probe.json yet"
    add_check("runtime:bridge-probe", bridge_status == "pass", bridge_detail, warn=True)
    if cross_engine_report:
        cross_engine_detail = f"{cross_engine_report.get('status', 'unknown')}; report={report_dir / 'unity_cross_engine_equivalence.json'}"
    else:
        cross_engine_detail = "no build/reports/unity_cross_engine_equivalence.json yet"
    add_check("runtime:cross-engine-equivalence", cross_engine_status == "pass", cross_engine_detail, warn=True)
    if head_to_head_report:
        head_to_head_grill_errors = _report_error_list(head_to_head_report, "grill_errors")
        head_to_head_fastdis_errors = _report_error_list(head_to_head_report, "fastdis_errors")
        detail_parts = [str(head_to_head_report.get("status", "unknown"))]
        if head_to_head_grill_errors:
            detail_parts.append(f"grill_errors={','.join(head_to_head_grill_errors)}")
        if head_to_head_fastdis_errors:
            detail_parts.append(f"fastdis_errors={','.join(head_to_head_fastdis_errors)}")
        detail_parts.append(f"report={report_dir / 'unity_head_to_head_benchmark.json'}")
        head_to_head_detail = "; ".join(detail_parts)
    else:
        head_to_head_detail = "no build/reports/unity_head_to_head_benchmark.json yet"
    add_check("runtime:head-to-head-benchmark", head_to_head_status == "pass", head_to_head_detail, warn=True)
    beta1_report = parity_reports.get("beta1")
    if beta1_report is not None:
        beta1_blockers = [str(row.get("name")) for row in (beta1_report.get("failures") or [])]
        beta1_detail = (
            f"{beta1_report.get('status', 'unknown')}; "
            f"verified={beta1_report.get('verified', 0)}/{beta1_report.get('required', 0)}; "
            f"blockers={','.join(beta1_blockers) or 'none'}"
        )
        add_check("parity:beta1", beta1_report.get("status") == "PASS", beta1_detail, warn=True)
    else:
        add_check(
            "parity:beta1",
            False,
            f"could not build parity report: {parity_errors.get('beta1', 'unknown error')}",
            warn=True,
        )

    hard_fail = any(check["status"] == "fail" for check in checks)
    workflow_status = "pass" if install is not None and install.editor_path is not None and all(package.values()) else "fail"
    native_status = "pass" if current_native_ok else "not_verified"
    if runtime_status == "pass" and orientation_status == "pass" and install_status == "pass" and install_matrix_status == "pass" and native_matrix_status == "pass":
        passed_scope = "workflow/package/native-matrix/native-staging/runtime/orientation/install matrix parity"
        next_scope = "Release polish"
    elif runtime_status == "pass" and orientation_status == "pass" and install_status == "pass" and install_matrix_status == "pass":
        passed_scope = "workflow/package/native-staging/runtime/orientation/install matrix parity"
        next_scope = "Release polish"
    elif runtime_status == "pass" and orientation_status == "pass" and install_status == "pass":
        passed_scope = "workflow/package/native-staging/runtime/orientation/install parity"
        next_scope = "Release polish"
    elif runtime_status == "pass" and orientation_status == "pass":
        passed_scope = "workflow/package/native-staging/runtime/orientation parity"
        next_scope = "Unity Git/UPM install smoke"
    elif runtime_status == "pass":
        passed_scope = "workflow/package/native-staging/runtime parity"
        next_scope = "Unity orientation verification scene"
    else:
        passed_scope = "workflow/package/native-staging parity"
        next_scope = "Unity Editor runtime verification"
    return {
        "requested_version": version,
        "status": "ok" if not hard_fail else "needs-attention",
        "unity_alpha5_result": "pass" if workflow_status == "pass" else "fail",
        "passed_scope": passed_scope,
        "next_scope": next_scope,
        "unity_workflow_status": workflow_status,
        "unity_native_status": native_status,
        "unity_native_matrix_status": native_matrix_status,
        "unity_native_matrix_targets": native_matrix_targets,
        "unity_demo_status": demo_status,
        "unity_runtime_status": runtime_status,
        "unity_orientation_status": orientation_status,
        "unity_startup_probe_status": startup_probe_status,
        "unity_install_status": install_status,
        "unity_install_host": str(install_smoke_report.get("host_platform") or host_install_label()) if install_smoke_report else host_install_label(),
        "unity_install_matrix_status": install_matrix_status,
        "unity_install_matrix_hosts": install_matrix_hosts,
        "unity_host_matrix_status": host_matrix_status,
        "unity_signoff_status": signoff_status,
        "unity_csharp_bridge_status": bridge_status,
        "unity_cross_engine_equivalence_status": cross_engine_status,
        "unity_head_to_head_benchmark_status": head_to_head_status,
        "unity_runtime_launcher": launcher_mode,
        "unity_parity": {
            milestone: {
                "status": report.get("status"),
                "required": report.get("required"),
                "verified": report.get("verified"),
                "implemented": report.get("implemented"),
                "scaffolded": report.get("scaffolded"),
                "missing": report.get("missing"),
                "blockers": [str(row.get("name")) for row in (report.get("failures") or [])],
            }
            for milestone, report in parity_reports.items()
        },
        "native_current_platform": host_native_key(),
        "install": install.to_dict() if install else None,
        "package_root": str(PACKAGE_ROOT),
        "work_root": str(unity_env.work_root()),
        "work_root_has_spaces": " " in str(unity_env.work_root()),
        "checks": checks,
        "runtime_notes": [
            "Unity 6000 Personal on macOS may report com.unity.editor.headless missing when launched with -batchmode/-nographics or Unity Test Runner.",
            "The default runtime verifier uses an Editor executeMethod harness through a login shell so the signed-in Unity Hub license is visible.",
            "Use FASTDIS_UNITY_BATCHMODE=1 or FASTDIS_UNITY_FORCE_NOGRAPHICS=1 only on machines with a valid headless/batchmode entitlement.",
            "The Mac-native payload lane writes build/reports/unity_native_matrix.json and build/reports/unity_native_matrix.md when invoked through fastdis engine unity build --all-native.",
            "If a run fails, inspect build/reports/unity_runtime_verification.json and build/reports/unity_editor_method.log for diagnostic_code/remediation.",
            "Orientation scene automation writes build/reports/unity_orientation_verification.json and .md from the example project runner.",
            "Install smoke automation writes build/reports/unity_install_smoke.json plus host-specific unity_install_smoke_<host>.json/.md artifacts from a temporary git-backed Unity project.",
            "If install smoke reports stage=host-startup or reason=project-import-never-started, treat that host as a Unity/OS startup problem before blaming the package.",
            "The Unity C# bridge probe is credential-free and compiles the package's native/scanner bridge under dotnet against the current libfastdis host build.",
        ],
        "next_steps": [
            "Run package checks: python tools/unity_workflow.py verify",
            "Stage host native library: python tools/unity_workflow.py build --all-native",
            "Run the replay/UDP demo proof: python tools/unity_workflow.py demo --unity-version 6000.5",
            "Run the credential-free bridge proof: python tools/unity_workflow.py bridge-probe",
            "Run the orientation example scene: python tools/unity_workflow.py orientation-verify --unity-version 6000.5",
            "Run the Unity startup probe: python tools/unity_workflow.py startup-probe --unity-version 6000.5",
            "Run the Git/UPM install smoke: python tools/unity_workflow.py install-smoke --unity-version 6000.5",
            "Run the canonical Unity replay matrix: python tools/unity_workflow.py replay-matrix --unity-version 6000.5",
            "Refresh the optional Unity install signoff matrix: python tools/unity_workflow.py install-matrix",
            "Refresh the optional staged host-bundle matrix: python tools/unity_workflow.py host-matrix",
            "Refresh the optional Unity Phase 1 signoff summary: python tools/unity_workflow.py signoff",
            "Refresh the Unity cross-engine equivalence report: python tools/unity_workflow.py cross-engine-equivalence",
            "Scaffold the Unity swap baseline JSON: python tools/unity_workflow.py swap-baseline-init --unity-version 6000.5.0f1 --scene LoopbackBench --traffic-mix \"100% Entity State\" --overwrite",
            "Probe the GRILL Unity source route on this host: python tools/unity_workflow.py swap-import-smoke --unity-version 6000.5",
            "Refresh the Unity swap benchmark readiness report: python tools/unity_workflow.py swap-benchmark",
            "Check the milestone gate: python tools/unity_workflow.py parity-check --milestone beta1",
            "Capture and export this host proof bundle: python tools/unity_workflow.py capture-host-report --host-label <host-label> --host-platform windows --unity-version 6000.5",
            "Run a Unity lane report: python tools/unity_workflow.py report",
            "Run Unity Editor runtime tests: python tools/unity_workflow.py runtime-verify --unity-version 6000.5",
            "Install in Unity Package Manager from the Git URL with ?path=packages/unity/com.sheepfling.fastdis",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    print("Unity doctor")
    print(f"status: {payload['status']}")
    print(f"unity_workflow_status: {payload['unity_workflow_status']}")
    print(f"unity_native_status: {payload['unity_native_status']}")
    print(f"unity_native_matrix_status: {payload['unity_native_matrix_status']}")
    print(f"unity_native_matrix_targets: {','.join(payload['unity_native_matrix_targets']) or 'none'}")
    print(f"unity_runtime_status: {payload['unity_runtime_status']}")
    print(f"unity_orientation_status: {payload['unity_orientation_status']}")
    print(f"unity_startup_probe_status: {payload['unity_startup_probe_status']}")
    print(f"unity_install_status: {payload['unity_install_status']}")
    print(f"unity_install_host: {payload['unity_install_host']}")
    print(f"unity_install_matrix_status: {payload['unity_install_matrix_status']}")
    print(f"unity_install_matrix_hosts: {','.join(payload['unity_install_matrix_hosts']) or 'none'}")
    print(f"unity_host_matrix_status: {payload['unity_host_matrix_status']}")
    print(f"unity_signoff_status: {payload['unity_signoff_status']}")
    print(f"unity_csharp_bridge_status: {payload['unity_csharp_bridge_status']}")
    print(f"unity_cross_engine_equivalence_status: {payload['unity_cross_engine_equivalence_status']}")
    print(f"unity_head_to_head_benchmark_status: {payload['unity_head_to_head_benchmark_status']}")
    print(f"unity_runtime_launcher: {payload['unity_runtime_launcher']}")
    print(f"unity_demo_status: {payload['unity_demo_status']}")
    print("unity_parity:")
    for milestone, report in payload["unity_parity"].items():
        blockers = ",".join(report["blockers"]) or "none"
        print(f"  - {milestone}: {report['status']} verified={report['verified']}/{report['required']} blockers={blockers}")
    print(f"requested_version: {payload['requested_version'] or 'default'}")
    install = payload["install"]
    if install:
        print(f"resolved_version: {install['version']}")
        print(f"install_root: {install['install_root']}")
        print(f"editor: {install['editor_path'] or 'missing'}")
    else:
        print("resolved_version: none")
    print(f"package_root: {payload['package_root']}")
    print(f"work_root: {payload['work_root']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")
    print("runtime notes:")
    for note in payload["runtime_notes"]:
        print(f"  - {note}")


def write_report(payload: dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "unity_workflow_report.json"
    md_path = out_dir / "unity_workflow_report.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Unity Workflow Report",
        "",
        f"- status: `{payload['status']}`",
        f"- unity_workflow_status: `{payload['unity_workflow_status']}`",
        f"- unity_native_status: `{payload['unity_native_status']}`",
        f"- unity_native_matrix_status: `{payload['unity_native_matrix_status']}`",
        f"- unity_native_matrix_targets: `{','.join(payload['unity_native_matrix_targets']) or 'none'}`",
        f"- unity_runtime_status: `{payload['unity_runtime_status']}`",
        f"- unity_orientation_status: `{payload['unity_orientation_status']}`",
        f"- unity_startup_probe_status: `{payload['unity_startup_probe_status']}`",
        f"- unity_install_status: `{payload['unity_install_status']}`",
        f"- unity_install_host: `{payload['unity_install_host']}`",
        f"- unity_install_matrix_status: `{payload['unity_install_matrix_status']}`",
        f"- unity_install_matrix_hosts: `{','.join(payload['unity_install_matrix_hosts']) or 'none'}`",
        f"- unity_host_matrix_status: `{payload['unity_host_matrix_status']}`",
        f"- unity_signoff_status: `{payload['unity_signoff_status']}`",
        f"- unity_csharp_bridge_status: `{payload['unity_csharp_bridge_status']}`",
        f"- unity_cross_engine_equivalence_status: `{payload['unity_cross_engine_equivalence_status']}`",
        f"- unity_head_to_head_benchmark_status: `{payload['unity_head_to_head_benchmark_status']}`",
        f"- unity_runtime_launcher: `{payload['unity_runtime_launcher']}`",
        f"- unity_demo_status: `{payload['unity_demo_status']}`",
        f"- passed_scope: `{payload['passed_scope']}`",
        f"- next_scope: `{payload['next_scope']}`",
        f"- package_root: `{payload['package_root']}`",
        "",
        "## Parity",
        "",
    ]
    for milestone, report in payload["unity_parity"].items():
        lines.append(
            f"- `{milestone}` status=`{report['status']}` verified=`{report['verified']}/{report['required']}` blockers=`{','.join(report['blockers']) or 'none'}`"
        )
    lines.extend([
        "",
        "## Checks",
        "",
    ])
    for check in payload["checks"]:
        lines.append(f"- `{check['status']}` {check['name']}: {check['detail']}")
    lines.extend(["", "## Runtime Notes", ""])
    for note in payload["runtime_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Unity installs")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Check Unity install and package prerequisites")
    doctor.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    verify = subparsers.add_parser("verify", help="Run Unity package structure tests")
    verify.add_argument("--unity-version", help="Accepted for workflow parity; package checks do not launch Unity")

    runtime_verify = subparsers.add_parser("runtime-verify", help="Run Unity package tests in a scratch Unity project")
    runtime_verify.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    runtime_verify.add_argument("--platform", action="append", choices=("EditMode", "PlayMode"), help="Test platform to run; defaults to both")
    runtime_verify.add_argument("--project-dir", help="Scratch Unity project directory")
    runtime_verify.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    runtime_verify.add_argument("--timeout", type=int, default=600)
    runtime_verify.add_argument("--dry-run", action="store_true")

    demo = subparsers.add_parser("demo", help="Run the Unity replay/UDP demo proof lane")
    demo.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    demo.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    demo.add_argument("--timeout", type=int, default=600)
    demo.add_argument("--dry-run", action="store_true")

    build = subparsers.add_parser("build", help="Build native FastDIS and stage Unity native plug-ins")
    build.add_argument("--unity-version", help="Accepted for workflow parity")
    build.add_argument("--skip-native-build", action="store_true", help="Only stage an existing build/libfastdis artifact")
    build.add_argument("--all-native", action="store_true", help="Build/stage macOS, Windows, and Linux native plug-ins when toolchains are available")

    report = subparsers.add_parser("report", help="Write Unity workflow report")
    report.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    report.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    parity_check = subparsers.add_parser("parity-check", help="Check the Unity GRILL parity matrix for a milestone gate")
    parity_check.add_argument("--matrix", default=str(ROOT / "docs" / "research" / "unity_grill_parity.yaml"))
    parity_check.add_argument("--milestone", required=True, choices=("alpha6", "alpha7", "alpha8", "beta1"))
    parity_check.add_argument("--format", choices=("text", "json"), default="text")

    bridge_probe = subparsers.add_parser("bridge-probe", help="Compile and run the Unity package C# native bridge under dotnet")
    bridge_probe.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    orientation_verify = subparsers.add_parser("orientation-verify", help="Run the Unity orientation verification example scene")
    orientation_verify.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    orientation_verify.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    orientation_verify.add_argument("--timeout", type=int, default=600)

    startup_probe = subparsers.add_parser("startup-probe", help="Launch a minimal scratch Unity project and verify that import begins on this host")
    startup_probe.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    startup_probe.add_argument("--project-dir", help="Scratch Unity project directory")
    startup_probe.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    startup_probe.add_argument("--timeout", type=int, default=120)

    install_smoke = subparsers.add_parser("install-smoke", help="Install the package from a temporary git repo into a clean Unity project and smoke native load/runtime")
    install_smoke.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    install_smoke.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    install_smoke.add_argument("--timeout", type=int, default=600)

    replay_matrix = subparsers.add_parser("replay-matrix", help="Run the canonical Unity replay runtime matrix")
    replay_matrix.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    replay_matrix.add_argument("--project-dir")
    replay_matrix.add_argument("--out-dir", default=str(ROOT / "build" / "reports" / "unity_replay_matrix"))
    replay_matrix.add_argument("--packet-budget", type=int, default=128)
    replay_matrix.add_argument("--timeout", type=int, default=600)
    replay_matrix.add_argument("--if-available", action="store_true")

    install_matrix = subparsers.add_parser("install-matrix", help="Aggregate Unity Git/UPM install-smoke reports into a cross-host signoff matrix")
    install_matrix.add_argument("--report-dir", default=str(ROOT / "build" / "reports"))
    install_matrix.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    adopt_install_smoke = subparsers.add_parser("adopt-install-smoke", help="Adopt a Unity install-smoke report from another host into the local report set")
    adopt_install_smoke.add_argument("--host", required=True, choices=("macos", "windows", "linux"))
    adopt_install_smoke.add_argument("--report", required=True)
    adopt_install_smoke.add_argument("--log")
    adopt_install_smoke.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    stage_host_report = subparsers.add_parser("stage-host-report", help="Stage this host's Unity proof reports into a reusable host bundle")
    stage_host_report.add_argument("--source-dir", default=str(ROOT / "build" / "reports"))
    stage_host_report.add_argument("--dest-root", default=str(ROOT / "verification_reports" / "unity_hosts"))
    stage_host_report.add_argument("--host-label")
    stage_host_report.add_argument("--host-platform", choices=("macos", "windows", "linux"))
    stage_host_report.add_argument("--overwrite", action="store_true")

    export_host_report = subparsers.add_parser("export-host-report", help="Export one staged Unity host bundle as a portable archive")
    export_host_report.add_argument("host_label")
    export_host_report.add_argument("--host-root", default=str(ROOT / "verification_reports" / "unity_hosts"))
    export_host_report.add_argument("--out-dir", default=str(ROOT / "dist" / "unity_host_reports"))

    export_host_handoff = subparsers.add_parser("export-host-handoff", help="Export a self-contained Unity host-proof handoff archive for Windows/Linux/macOS proof machines")
    export_host_handoff.add_argument("--out-dir", default=str(ROOT / "dist" / "unity_host_handoff"))

    import_host_report = subparsers.add_parser("import-host-report", help="Import a portable Unity host bundle archive and adopt its install evidence")
    import_host_report.add_argument("archive")
    import_host_report.add_argument("--host-root", default=str(ROOT / "verification_reports" / "unity_hosts"))
    import_host_report.add_argument("--report-dir", default=str(ROOT / "build" / "reports"))
    import_host_report.add_argument("--overwrite", action="store_true")
    import_host_report.add_argument("--checksum")

    sync_host_reports = subparsers.add_parser("sync-host-reports", help="Sync all staged Unity host bundles into the local report directory and refresh aggregates")
    sync_host_reports.add_argument("--host-root", default=str(ROOT / "verification_reports" / "unity_hosts"))
    sync_host_reports.add_argument("--report-dir", default=str(ROOT / "build" / "reports"))

    host_matrix = subparsers.add_parser("host-matrix", help="Aggregate staged Unity host bundles into a cross-host host matrix report")
    host_matrix.add_argument("--host-root", default=str(ROOT / "verification_reports" / "unity_hosts"))
    host_matrix.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    signoff = subparsers.add_parser("signoff", help="Generate the Unity Phase 1 signoff summary")
    signoff.add_argument("--report-dir", default=str(ROOT / "build" / "reports"))
    signoff.add_argument("--host-root", default=str(ROOT / "verification_reports" / "unity_hosts"))
    signoff.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    cross_engine_equivalence = subparsers.add_parser("cross-engine-equivalence", help="Generate the Unity cross-engine equivalence report")
    cross_engine_equivalence.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))

    head_to_head_benchmark = subparsers.add_parser(
        "head-to-head-benchmark",
        aliases=["swap-benchmark"],
        help="Generate the Unity swap/head-to-head benchmark readiness report",
    )
    head_to_head_benchmark.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    head_to_head_benchmark.add_argument("--fastdis", default=str(ROOT / "build" / "benchmark_results" / "current" / "current.json"))
    head_to_head_benchmark.add_argument("--grill", default=str(ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"))

    grill_baseline_init = subparsers.add_parser(
        "grill-baseline-init",
        aliases=["swap-baseline-init"],
        help="Scaffold a Unity swap benchmark baseline JSON from the tracked GRILL template",
    )
    grill_baseline_init.add_argument("--out", default=str(ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"))
    grill_baseline_init.add_argument("--fastdis", default=str(ROOT / "build" / "benchmark_results" / "current" / "current.json"))
    grill_baseline_init.add_argument("--unity-version", default="REPLACE_ME_UNITY_VERSION")
    grill_baseline_init.add_argument("--scene", default="REPLACE_ME_SCENE_NAME")
    grill_baseline_init.add_argument("--traffic-mix", default="REPLACE_ME_TRAFFIC_MIX")
    grill_baseline_init.add_argument("--scripting-backend", default="REPLACE_ME_SCRIPTING_BACKEND")
    grill_baseline_init.add_argument("--commit", default="REPLACE_ME_COMMIT")
    grill_baseline_init.add_argument("--limit-cases", type=int, default=12)
    grill_baseline_init.add_argument("--overwrite", action="store_true")

    grill_import_smoke = subparsers.add_parser(
        "grill-import-smoke",
        aliases=["swap-import-smoke"],
        help="Import the GRILL Unity plugin into a scratch project and record swap-route startup evidence",
    )
    grill_import_smoke.add_argument("--plugin-root", default=str(grill_paths.UNITY_PLUGIN))
    grill_import_smoke.add_argument("--unity-version", default="6000.5")
    grill_import_smoke.add_argument("--project-dir")
    grill_import_smoke.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    grill_import_smoke.add_argument("--timeout", type=int, default=120)

    capture_host_report = subparsers.add_parser("capture-host-report", help="Run the local Unity proof flow and stage/export one host bundle")
    capture_host_report.add_argument("--source-dir", default=str(ROOT / "build" / "reports"))
    capture_host_report.add_argument("--host-label")
    capture_host_report.add_argument("--host-platform", choices=("macos", "windows", "linux"))
    capture_host_report.add_argument("--dest-root")
    capture_host_report.add_argument("--archive-out-dir")
    capture_host_report.add_argument("--unity-version")
    capture_host_report.add_argument("--skip-startup-probe", action="store_true")
    capture_host_report.add_argument("--skip-full", action="store_true")
    capture_host_report.add_argument("--skip-stage", action="store_true")
    capture_host_report.add_argument("--skip-export", action="store_true")
    capture_host_report.add_argument("--skip-install-matrix", action="store_true")

    full = subparsers.add_parser("full", help="Doctor, build, run the Unity demo proof, run the orientation scene, and write a report")
    full.add_argument("--unity-version", help="Unity editor version prefix, for example 6000.5")
    full.add_argument("--skip-native-build", action="store_true", help="Reuse the staged Unity native plug-ins instead of compiling a host native library first")
    full.add_argument("--skip-runtime", action="store_true", help="Skip the Unity demo/runtime proof lane")
    full.add_argument("--skip-orientation", action="store_true", help="Skip the Unity orientation verification scene")
    full.add_argument("--skip-startup-probe", action="store_true", help="Skip the Unity startup probe preflight before install smoke")
    full.add_argument("--skip-install-smoke", action="store_true", help="Skip the Unity Git/UPM install smoke lane")
    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = unity_env.describe_host()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        installs = payload["installs"]
        if not installs:
            print("No Unity installs discovered.")
            return 1
        for install in installs:
            print(f"{install['version']}: {install['install_root']}")
            print(f"  editor: {install['editor_path'] or 'missing'}")
            print(f"  source: {install['source']}")
            quirks = ", ".join(install["quirks"]) if install["quirks"] else "none"
            print(f"  quirks: {quirks}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    report_dir = Path(getattr(args, "report_dir", DEFAULT_REPORT_DIR))
    payload = doctor_payload(args.unity_version, report_dir)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_verify(_args: argparse.Namespace) -> int:
    return run_step(unity_env.python_command() + ["-m", "pytest", "tests/test_unity_upm_package.py"])


def command_runtime_verify(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_editor_tests.py"]
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if args.project_dir:
        cmd.extend(["--project-dir", args.project_dir])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    for platform_name in args.platform or []:
        cmd.extend(["--platform", platform_name])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd, preserve_unity_login=True)


def command_demo(args: argparse.Namespace) -> int:
    runtime_args = argparse.Namespace(
        unity_version=args.unity_version,
        platform=None,
        project_dir=None,
        out_dir=args.out_dir,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )
    return command_runtime_verify(runtime_args)


def command_build(args: argparse.Namespace) -> int:
    if args.all_native:
        matrix_report_dir = str(DEFAULT_REPORT_DIR)
        matrix_code = run_step(
            unity_env.python_command()
            + ["tools/build_unity_native_matrix.py", "build", "--keep-going", "--out-dir", matrix_report_dir]
        )
        verify_code = command_verify(args)
        report_code = command_report(argparse.Namespace(unity_version=args.unity_version, out_dir=matrix_report_dir))
        for code in (matrix_code, verify_code, report_code):
            if code != 0:
                return code
        return 0
    if not args.skip_native_build:
        native_code = run_step(unity_env.python_command() + ["tools/build_native.py"])
        if native_code != 0:
            return native_code
    stage_code = run_step(unity_env.python_command() + ["tools/stage_unity_native.py"])
    if stage_code != 0:
        return stage_code
    return command_verify(args)


def command_bridge_probe(args: argparse.Namespace) -> int:
    return run_step(unity_env.python_command() + ["tools/probe_unity_csharp_bridge.py", "--out-dir", args.out_dir])


def command_orientation_verify(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_orientation_verification.py"]
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    return run_step(cmd, preserve_unity_login=True)


def command_startup_probe(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_startup_probe.py"]
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if args.project_dir:
        cmd.extend(["--project-dir", args.project_dir])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    return run_step(cmd, preserve_unity_login=True)


def command_install_smoke(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_install_smoke.py"]
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    return run_step(cmd, preserve_unity_login=True)


def command_replay_matrix(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_replay_matrix.py"]
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if args.project_dir:
        cmd.extend(["--project-dir", args.project_dir])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    if args.packet_budget:
        cmd.extend(["--packet-budget", str(args.packet_budget)])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    if args.if_available:
        cmd.append("--if-available")
    return run_step(cmd, preserve_unity_login=True)


def command_install_matrix(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_install_matrix.py", "--report-dir", args.report_dir, "--out-dir", args.out_dir]
    return run_step(cmd)


def command_adopt_install_smoke(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/adopt_unity_install_smoke.py", "--host", args.host, "--report", args.report]
    if args.log:
        cmd.extend(["--log", args.log])
    if args.out_dir:
        cmd.extend(["--out-dir", args.out_dir])
    return run_step(cmd)


def command_stage_host_report(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/stage_unity_host_report.py", "--source-dir", args.source_dir, "--dest-root", args.dest_root]
    if args.host_label:
        cmd.extend(["--host-label", args.host_label])
    if args.host_platform:
        cmd.extend(["--host-platform", args.host_platform])
    if args.overwrite:
        cmd.append("--overwrite")
    return run_step(cmd)


def command_export_host_report(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/export_unity_host_report.py", args.host_label, "--host-root", args.host_root, "--out-dir", args.out_dir]
    return run_step(cmd)


def command_export_host_handoff(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/export_unity_host_handoff.py", "--out-dir", args.out_dir]
    return run_step(cmd)


def command_import_host_report(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/import_unity_host_report.py", args.archive, "--host-root", args.host_root, "--report-dir", args.report_dir]
    if args.overwrite:
        cmd.append("--overwrite")
    if args.checksum:
        cmd.extend(["--checksum", args.checksum])
    return run_step(cmd)


def command_sync_host_reports(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/sync_unity_host_reports.py", "--host-root", args.host_root, "--report-dir", args.report_dir]
    return run_step(cmd)


def command_host_matrix(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_host_matrix.py", "--host-root", args.host_root, "--out-dir", args.out_dir]
    return run_step(cmd)


def command_signoff(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/run_unity_signoff.py", "--report-dir", args.report_dir, "--host-root", args.host_root, "--out-dir", args.out_dir]
    return run_step(cmd)


def command_cross_engine_equivalence(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    cmd = unity_env.python_command() + [
        "tools/build_unity_cross_engine_equivalence_report.py",
        "--json-out",
        str(out_dir / "unity_cross_engine_equivalence.json"),
        "--md-out",
        str(out_dir / "unity_cross_engine_equivalence.md"),
    ]
    return run_step(cmd)


def command_head_to_head_benchmark(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    cmd = unity_env.python_command() + [
        "tools/build_unity_head_to_head_benchmark_report.py",
        "--fastdis",
        args.fastdis,
        "--grill",
        args.grill,
        "--json-out",
        str(out_dir / "unity_head_to_head_benchmark.json"),
        "--md-out",
        str(out_dir / "unity_head_to_head_benchmark.md"),
    ]
    return run_step(cmd)


def command_grill_baseline_init(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + [
        "tools/init_unity_grill_benchmark_baseline.py",
        "--out",
        args.out,
        "--fastdis",
        args.fastdis,
        "--unity-version",
        args.unity_version,
        "--scene",
        args.scene,
        "--traffic-mix",
        args.traffic_mix,
        "--scripting-backend",
        args.scripting_backend,
        "--commit",
        args.commit,
        "--limit-cases",
        str(args.limit_cases),
    ]
    if args.overwrite:
        cmd.append("--overwrite")
    return run_step(cmd)


def command_grill_import_smoke(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + [
        "tools/run_grill_unity_import_smoke.py",
        "--plugin-root",
        args.plugin_root,
        "--unity-version",
        args.unity_version,
        "--out-dir",
        args.out_dir,
        "--timeout",
        str(args.timeout),
    ]
    if args.project_dir:
        cmd.extend(["--project-dir", args.project_dir])
    return run_step(cmd, preserve_unity_login=True)


def command_capture_host_report(args: argparse.Namespace) -> int:
    cmd = unity_env.python_command() + ["tools/capture_unity_host_report.py", "--source-dir", args.source_dir]
    if args.host_label:
        cmd.extend(["--host-label", args.host_label])
    if args.host_platform:
        cmd.extend(["--host-platform", args.host_platform])
    if args.dest_root:
        cmd.extend(["--dest-root", args.dest_root])
    if args.archive_out_dir:
        cmd.extend(["--archive-out-dir", args.archive_out_dir])
    if args.unity_version:
        cmd.extend(["--unity-version", args.unity_version])
    if getattr(args, "skip_startup_probe", False):
        cmd.append("--skip-startup-probe")
    if args.skip_full:
        cmd.append("--skip-full")
    if args.skip_stage:
        cmd.append("--skip-stage")
    if args.skip_export:
        cmd.append("--skip-export")
    if args.skip_install_matrix:
        cmd.append("--skip-install-matrix")
    return run_step(cmd)


def command_report(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.unity_version, Path(args.out_dir))
    write_report(payload, Path(args.out_dir))
    return 0 if payload["status"] == "ok" else 2


def command_parity_check(args: argparse.Namespace) -> int:
    return check_unity_parity.main(
        [
            "--matrix",
            args.matrix,
            "--milestone",
            args.milestone,
            "--format",
            args.format,
        ]
    )


def command_full(args: argparse.Namespace) -> int:
    doctor_args = argparse.Namespace(unity_version=args.unity_version, format="text")
    doctor_code = command_doctor(doctor_args)
    build_args = argparse.Namespace(unity_version=args.unity_version, skip_native_build=args.skip_native_build, all_native=False)
    build_code = command_build(build_args)
    bridge_code = command_bridge_probe(argparse.Namespace(out_dir=str(ROOT / "build" / "reports")))
    demo_code = 0
    orientation_code = 0
    startup_probe_code = 0
    install_code = 0
    install_matrix_code = 0
    host_matrix_code = 0
    signoff_code = 0
    cross_engine_code = 0
    head_to_head_code = 0
    if not args.skip_runtime:
        demo_args = argparse.Namespace(
            unity_version=args.unity_version,
            out_dir=str(ROOT / "build" / "reports"),
            timeout=600,
            dry_run=False,
        )
        demo_code = command_demo(demo_args)
    if not args.skip_orientation:
        orientation_args = argparse.Namespace(
            unity_version=args.unity_version,
            out_dir=str(ROOT / "build" / "reports"),
            timeout=600,
        )
        orientation_code = command_orientation_verify(orientation_args)
    if not args.skip_startup_probe:
        startup_args = argparse.Namespace(
            unity_version=args.unity_version,
            project_dir=None,
            out_dir=str(ROOT / "build" / "reports"),
            timeout=120,
        )
        startup_probe_code = command_startup_probe(startup_args)
    if not args.skip_install_smoke:
        if startup_probe_code == 0 or args.skip_startup_probe:
            install_args = argparse.Namespace(
                unity_version=args.unity_version,
                out_dir=str(ROOT / "build" / "reports"),
                timeout=600,
            )
            install_code = command_install_smoke(install_args)
        else:
            startup_probe_report = latest_startup_probe_report(ROOT / "build" / "reports")
            if startup_probe_report is not None:
                synthetic = run_unity_install_smoke.build_startup_blocked_report(startup_probe_report, ROOT / "build" / "reports")
                synthetic_json = ROOT / "build" / "reports" / "unity_install_smoke.json"
                synthetic_host_json = ROOT / "build" / "reports" / f"unity_install_smoke_{host_install_label()}.json"
                synthetic_md = ROOT / "build" / "reports" / "unity_install_smoke.md"
                synthetic_host_md = ROOT / "build" / "reports" / f"unity_install_smoke_{host_install_label()}.md"
                for path in (synthetic_json, synthetic_host_json):
                    path.write_text(json.dumps(synthetic, indent=2) + "\n", encoding="utf-8")
                for path in (synthetic_md, synthetic_host_md):
                    path.write_text(run_unity_install_smoke.render_markdown(synthetic), encoding="utf-8")
            install_code = startup_probe_code
    install_matrix_args = argparse.Namespace(
        report_dir=str(ROOT / "build" / "reports"),
        out_dir=str(ROOT / "build" / "reports"),
    )
    install_matrix_code = command_install_matrix(install_matrix_args)
    host_matrix_args = argparse.Namespace(
        host_root=str(ROOT / "verification_reports" / "unity_hosts"),
        out_dir=str(ROOT / "build" / "reports"),
    )
    host_matrix_code = command_host_matrix(host_matrix_args)
    report_args = argparse.Namespace(unity_version=args.unity_version, out_dir=str(ROOT / "build" / "reports"))
    pre_signoff_report_code = command_report(report_args)
    signoff_args = argparse.Namespace(
        report_dir=str(ROOT / "build" / "reports"),
        host_root=str(ROOT / "verification_reports" / "unity_hosts"),
        out_dir=str(ROOT / "build" / "reports"),
    )
    signoff_code = command_signoff(signoff_args)
    cross_engine_code = command_cross_engine_equivalence(argparse.Namespace(out_dir=str(ROOT / "build" / "reports")))
    head_to_head_code = command_head_to_head_benchmark(
        argparse.Namespace(
            out_dir=str(ROOT / "build" / "reports"),
            fastdis=str(ROOT / "build" / "benchmark_results" / "current" / "current.json"),
            grill=str(ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"),
        )
    )
    report_code = command_report(report_args)
    hard_failure = doctor_code or build_code or bridge_code or demo_code or orientation_code or startup_probe_code or install_code or pre_signoff_report_code or cross_engine_code or report_code
    if hard_failure:
        return hard_failure
    # The install matrix, staged host matrix, and signoff summary are cross-host gates,
    # not single-host workflow gates. Preserve their warning/fail status in generated
    # reports, but keep `full` successful when the local proof lanes pass and only the
    # external host bundle is incomplete.
    if install_matrix_code not in {0, 1}:
        return install_matrix_code
    if host_matrix_code not in {0, 1}:
        return host_matrix_code
    if signoff_code not in {0, 2}:
        return signoff_code
    if head_to_head_code not in {0, 1}:
        return head_to_head_code
    return 0


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command == "runtime-verify":
        return command_runtime_verify(args)
    if args.command == "demo":
        return command_demo(args)
    if args.command == "build":
        return command_build(args)
    if args.command == "bridge-probe":
        return command_bridge_probe(args)
    if args.command == "orientation-verify":
        return command_orientation_verify(args)
    if args.command == "startup-probe":
        return command_startup_probe(args)
    if args.command == "install-smoke":
        return command_install_smoke(args)
    if args.command == "replay-matrix":
        return command_replay_matrix(args)
    if args.command == "install-matrix":
        return command_install_matrix(args)
    if args.command == "adopt-install-smoke":
        return command_adopt_install_smoke(args)
    if args.command == "stage-host-report":
        return command_stage_host_report(args)
    if args.command == "export-host-report":
        return command_export_host_report(args)
    if args.command == "export-host-handoff":
        return command_export_host_handoff(args)
    if args.command == "import-host-report":
        return command_import_host_report(args)
    if args.command == "sync-host-reports":
        return command_sync_host_reports(args)
    if args.command == "host-matrix":
        return command_host_matrix(args)
    if args.command == "signoff":
        return command_signoff(args)
    if args.command == "cross-engine-equivalence":
        return command_cross_engine_equivalence(args)
    if args.command in {"head-to-head-benchmark", "swap-benchmark"}:
        return command_head_to_head_benchmark(args)
    if args.command in {"grill-baseline-init", "swap-baseline-init"}:
        return command_grill_baseline_init(args)
    if args.command in {"grill-import-smoke", "swap-import-smoke"}:
        return command_grill_import_smoke(args)
    if args.command == "capture-host-report":
        return command_capture_host_report(args)
    if args.command == "report":
        return command_report(args)
    if args.command == "parity-check":
        return command_parity_check(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
