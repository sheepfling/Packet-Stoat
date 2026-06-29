#!/usr/bin/env python3
"""Operator-facing Unreal workflow wrapper for discovery, packaging, and verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

import grill_paths
import load_local_env
import unreal_env


ROOT = Path(__file__).resolve().parents[1]
ORIENTATION_PROJECT_PATH = ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "FastDisOrientationVerification.uproject"
DEFAULT_SUPPORTED_VERSIONS = ["5.7", "5.8"]
DEFAULT_LINUX_PROFILE = ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue57.env"


def _version_label(version: str | None) -> str:
    return version or "default"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def run_steps(commands: list[list[str]]) -> int:
    for cmd in commands:
        code = run_step(cmd)
        if code != 0:
            return code
    return 0


def install_for_version(version: str | None) -> unreal_env.UnrealInstall | None:
    installs = unreal_env.discover_installs()
    if version is not None:
        for install in installs:
            if unreal_env.version_matches(version, install.version):
                return install
        return None
    if installs:
        return installs[-1]
    return None


def doctor_payload(version: str | None) -> dict[str, object]:
    install = install_for_version(version)
    payload: dict[str, object] = {
        "requested_version": version,
        "resolved_version": None,
        "status": "ok",
        "install": None,
        "checks": [],
        "next_steps": [],
    }

    if install is None:
        payload["status"] = "missing-install"
        payload["checks"] = [
            {
                "name": "engine install",
                "status": "fail",
                "detail": f"no Unreal install discovered for {_version_label(version)}",
            }
        ]
        payload["next_steps"] = [
            "Set FASTDIS_UNREAL_ENGINE_DIR or FASTDIS_UNREAL_ENGINE_DIR_5_8 style variables in .env.local.",
            "Run `python tools/list_unreal_installs.py` to inspect what this machine can see.",
        ]
        return payload

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    add_check("engine root", "ok", install.install_root)
    add_check("editor", "ok" if install.editor_path is not None else "fail", install.editor_path or "missing editor executable")
    add_check("automation tool", "ok" if install.uat_path is not None else "fail", install.uat_path or "missing RunUAT")
    add_check("build tool", "ok" if install.ubt_path is not None else "fail", install.ubt_path or "missing UnrealBuildTool.dll")
    add_check("bundled dotnet", "ok" if install.dotnet_path is not None else "fail", install.dotnet_path or "missing bundled dotnet")

    rider = shutil.which("rider")
    add_check("rider", "ok" if rider else "warn", rider or "optional; set FASTDIS_RIDER or put rider on PATH")

    permissions = unreal_env.permission_probe(install)
    for check in permissions["checks"]:
        add_check(f"permission:{check['name']}", str(check["status"]), str(check["detail"]))

    if install.dotnet_path and install.ubt_path:
        probe = unreal_env.probe_host_platform_support(install, ORIENTATION_PROJECT_PATH)
        add_check("host platform probe", str(probe["status"]), str(probe["detail"]))
    else:
        probe = None

    has_failures = any(check["status"] == "fail" for check in checks[:5])
    if probe is not None and probe["status"] == "fail":
        has_failures = True
    payload["resolved_version"] = install.version
    payload["status"] = "ok" if not has_failures else "needs-attention"
    payload["install"] = install.to_dict()
    payload["permissions"] = permissions
    if probe is not None:
        payload["platform_probe"] = probe
    payload["checks"] = checks
    if probe is not None and probe["status"] == "fail":
        payload["next_steps"] = [
            f"Resolve the host/engine compatibility issue for {install.version or 'this lane'} before packaging or automation runs.",
            "Use a passing lane such as 5.7 or 5.8 on this machine, or adjust the host SDK/engine install.",
            "If the issue is permission-related, rerun from a shell that can write Unreal Engine intermediates or prebuild the target outside the sandbox.",
            "Run the full matrix for a cross-version view: python tools/unreal_workflow.py matrix",
        ]
    else:
        payload["next_steps"] = [
            f"Package plugin: python tools/unreal_workflow.py build --engine-version {install.version or '5.8'}",
            f"Run orientation harness: python tools/unreal_workflow.py verify --engine-version {install.version or '5.8'}",
            f"Run replay demo smoke: python tools/unreal_workflow.py demo --engine-version {install.version or '5.8'}",
            "Run the full swap lane: python tools/unreal_workflow.py swap-smoke --engine-version 5.8",
            "Export the GRILL mapping asset from Unreal: python tools/unreal_workflow.py swap-mapping-export --engine-version 5.8",
            "Import/audit a GRILL mapping export: python tools/unreal_workflow.py swap-mapping-import --input path/to/grill_mapping_export.json",
            "Materialize a FastDIS mapping asset in a GRILL-shaped temp project: python tools/unreal_workflow.py swap-mapping-materialize --engine-version 5.8 --input-manifest build/reports/unreal_grill_swap/fastdis_mapping_manifest.json",
            "Scaffold the swap baseline JSON: python tools/unreal_workflow.py swap-baseline-init --engine-version 5.8 --map LoopbackBench --traffic-mix \"100% Entity State\" --overwrite",
            "Run the Unreal swap comparison lane: python tools/unreal_workflow.py swap-benchmark",
            "Run the full matrix: python tools/unreal_workflow.py matrix",
        ]
        if any(check["name"] == "permission:engine_intermediate" and check["status"] != "ok" for check in checks):
            payload["next_steps"].insert(
                0,
                "Engine intermediates are not writable in this environment; live Unreal build/verify lanes may need a normal terminal or approved sandbox escalation.",
            )
    return payload


def print_doctor(payload: dict[str, object]) -> None:
    requested = payload["requested_version"] or "default"
    resolved = payload["resolved_version"] or "none"
    print(f"Unreal doctor for {requested}")
    print(f"status: {payload['status']}")
    print(f"resolved_version: {resolved}")
    install = payload["install"]
    if install:
        print(f"install_root: {install['install_root']}")
        if install["quirks"]:
            print("quirks:")
            for quirk in install["quirks"]:
                print(f"  - {quirk}")
        permissions = payload.get("permissions")
        if permissions:
            print(f"work_root: {permissions['work_root']}")
    else:
        print("install_root: missing")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def add_engine_version(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")


def linux_profile_for_version(version: str | None) -> Path:
    if version:
        candidate = ROOT / "tools" / "unreal_linux_profiles" / f"ubuntu_24_04_ue{version.replace('.', '')}.env"
        if candidate.is_file():
            return candidate
    return DEFAULT_LINUX_PROFILE


def resolve_linux_profile(raw_profile: str | None, engine_version: str | None) -> str:
    if raw_profile:
        return str(Path(raw_profile).expanduser())
    return str(linux_profile_for_version(engine_version))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Unreal installs")
    discover.add_argument("--format", choices=("table", "json"), default="table")

    doctor = subparsers.add_parser("doctor", help="Check the current machine for Unreal build prerequisites")
    add_engine_version(doctor)
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Build and package the FastDis Unreal plugin")
    add_engine_version(build)
    build.add_argument("--open-rider", action="store_true", help="Open the generated host project in Rider")
    build.add_argument("--no-clean-package", action="store_true", help="Keep the existing package directory")

    verify = subparsers.add_parser("verify", help="Run the Unreal orientation verification harness")
    add_engine_version(verify)
    verify.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")

    demo = subparsers.add_parser("demo", help="Run the Unreal replay/demo smoke harness")
    add_engine_version(demo)
    demo.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")

    install_smoke = subparsers.add_parser("install-smoke", help="Install the packaged plugin into a clean scratch project and smoke the packaged demo map")
    add_engine_version(install_smoke)
    install_smoke.add_argument("--dry-run", action="store_true", help="Print the editor command without executing it")

    grill_baseline_init = subparsers.add_parser(
        "grill-baseline-init",
        aliases=["swap-baseline-init"],
        help="Scaffold the Unreal swap benchmark baseline JSON from the tracked GRILL-route template",
    )
    grill_baseline_init.add_argument("--out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json"))
    grill_baseline_init.add_argument("--fastdis", default=str(ROOT / "build" / "benchmark_results" / "current" / "current.json"))
    grill_baseline_init.add_argument("--engine-version", default="REPLACE_ME_ENGINE_VERSION")
    grill_baseline_init.add_argument("--map", default="REPLACE_ME_MAP_NAME")
    grill_baseline_init.add_argument("--traffic-mix", default="REPLACE_ME_TRAFFIC_MIX")
    grill_baseline_init.add_argument("--commit", default="REPLACE_ME_COMMIT")
    grill_baseline_init.add_argument("--limit-cases", type=int, default=12)
    grill_baseline_init.add_argument("--overwrite", action="store_true")

    grill_mapping_export = subparsers.add_parser(
        "grill-mapping-export",
        aliases=["swap-mapping-export"],
        help="Export the GRILL Unreal mapping asset to normalized JSON via Unreal Python",
    )
    add_engine_version(grill_mapping_export)
    grill_mapping_export.add_argument("--example-root", default=str(grill_paths.UNREAL_EXAMPLE))
    grill_mapping_export.add_argument("--asset-path", default="/Game/DISEnumerationMappings")
    grill_mapping_export.add_argument("--export-json", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export.json"))
    grill_mapping_export.add_argument("--json-out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.json"))
    grill_mapping_export.add_argument("--markdown-out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.md"))
    grill_mapping_export.add_argument("--dry-run", action="store_true")

    grill_mapping_import = subparsers.add_parser(
        "grill-mapping-import",
        aliases=["swap-mapping-import"],
        help="Import an exported GRILL Unreal mapping manifest into a FastDIS-ready intermediate manifest",
    )
    grill_mapping_import.add_argument("--input", required=True, help="Exported GRILL Unreal mapping manifest JSON")
    grill_mapping_import.add_argument("--fastdis-out", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "fastdis_mapping_manifest.json"))
    grill_mapping_import.add_argument("--json-out", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "grill_mapping_import_report.json"))
    grill_mapping_import.add_argument("--md-out", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "grill_mapping_import_report.md"))
    grill_mapping_import.add_argument("--source-route", default="AF-GRILL/DISPluginForUnreal@ue5")
    grill_mapping_import.add_argument("--search-root", dest="search_roots", action="append", help="Host project or plugin root used to validate actor-class paths")

    grill_mapping_materialize = subparsers.add_parser(
        "grill-mapping-materialize",
        aliases=["swap-mapping-materialize"],
        help="Create a real FastDIS enumeration mapping asset from an imported GRILL Unreal manifest",
    )
    add_engine_version(grill_mapping_materialize)
    grill_mapping_materialize.add_argument("--example-root", default=str(grill_paths.UNREAL_EXAMPLE))
    grill_mapping_materialize.add_argument("--input-manifest", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "fastdis_mapping_manifest.json"))
    grill_mapping_materialize.add_argument("--asset-path", default="/Game/FastDis/DA_ImportedGRILLMappings")
    grill_mapping_materialize.add_argument("--result-json", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize.json"))
    grill_mapping_materialize.add_argument("--json-out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.json"))
    grill_mapping_materialize.add_argument("--markdown-out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.md"))
    grill_mapping_materialize.add_argument("--dry-run", action="store_true")

    grill_swap_smoke = subparsers.add_parser(
        "grill-swap-smoke",
        aliases=["swap-smoke"],
        help="Run the full GRILL-shaped Unreal swap lane: export, import, and materialize the mapping asset",
    )
    add_engine_version(grill_swap_smoke)
    grill_swap_smoke.add_argument("--example-root", default=str(grill_paths.UNREAL_EXAMPLE))
    grill_swap_smoke.add_argument("--asset-path", default="/Game/DISEnumerationMappings")
    grill_swap_smoke.add_argument("--export-json", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export.json"))
    grill_swap_smoke.add_argument("--export-report-json", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.json"))
    grill_swap_smoke.add_argument("--export-report-md", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.md"))
    grill_swap_smoke.add_argument("--fastdis-out", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "fastdis_mapping_manifest.json"))
    grill_swap_smoke.add_argument("--import-report-json", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "grill_mapping_import_report.json"))
    grill_swap_smoke.add_argument("--import-report-md", default=str(ROOT / "build" / "reports" / "unreal_grill_swap" / "grill_mapping_import_report.md"))
    grill_swap_smoke.add_argument("--source-route", default="AF-GRILL/DISPluginForUnreal@ue5")
    grill_swap_smoke.add_argument("--search-root", dest="search_roots", action="append", help="Host project or plugin root used to validate actor-class paths during import")
    grill_swap_smoke.add_argument("--materialized-asset-path", default="/Game/FastDis/DA_ImportedGRILLMappings")
    grill_swap_smoke.add_argument("--materialize-result-json", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize.json"))
    grill_swap_smoke.add_argument("--materialize-report-json", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.json"))
    grill_swap_smoke.add_argument("--materialize-report-md", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.md"))
    grill_swap_smoke.add_argument("--dry-run", action="store_true")

    grill_benchmark = subparsers.add_parser(
        "grill-benchmark",
        aliases=["swap-benchmark"],
        help="Run the Unreal swap head-to-head comparator when a GRILL shared report is present",
    )
    grill_benchmark.add_argument("--fastdis", default=str(ROOT / "build" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json"))
    grill_benchmark.add_argument("--grill-report", dest="grill_reports", action="append", help="Candidate GRILL Unreal shared benchmark report path")
    grill_benchmark.add_argument("--allow-sample-grill", action="store_true", help="Allow a sample GRILL report when no current report exists")
    grill_benchmark.add_argument("--out-dir", default=str(ROOT / "build" / "reports" / "engine_head_to_head"))

    grill_linux_proof = subparsers.add_parser(
        "grill-linux-proof",
        help="Capture the pinned GRILL Unreal Linux Docker packaging proof into FastDIS verification reports",
    )
    grill_linux_proof.add_argument("--plugin-root", default=str(grill_paths.UNREAL_PLUGIN))
    grill_linux_proof.add_argument("--profile", default=str(grill_paths.UNREAL_PLUGIN / "Scripts" / "linux_proof_profiles" / "ubuntu_24_04_ue57.env"))
    grill_linux_proof.add_argument("--package-dir", default=str(grill_paths.UNREAL_PLUGIN / ".build" / "grill_buildplugin_linux" / "ue5.7.4-linux_ubuntu-24.04" / "package"))
    grill_linux_proof.add_argument("--json-out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_linux_build_proof.json"))
    grill_linux_proof.add_argument("--md-out", default=str(ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_linux_build_proof.md"))

    fastdis_linux_proof = subparsers.add_parser(
        "linux-proof",
        help="Capture the current FastDIS Unreal Linux portability proof into verification reports",
    )
    fastdis_linux_proof.add_argument("--plugin-dir", default=str(ROOT / "examples" / "unreal" / "FastDis"))
    fastdis_linux_proof.add_argument("--linux-build-dir", default=str(ROOT / "build" / "cmake" / "linux-x86_64"))
    fastdis_linux_proof.add_argument("--build-cs", default=str(ROOT / "examples" / "unreal" / "FastDis" / "Source" / "FastDisUnreal" / "FastDisUnreal.Build.cs"))
    fastdis_linux_proof.add_argument("--mac-install-smoke", default=str(ROOT / "build" / "reports" / "unreal_packaged_install_smoke.json"))
    fastdis_linux_proof.add_argument("--linux-package-dir", default=str(ROOT / "build" / "linux_unreal_package" / "ue5.7.4-linux_ubuntu-24.04" / "package"))
    fastdis_linux_proof.add_argument("--json-out", default=str(ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_proof.json"))
    fastdis_linux_proof.add_argument("--md-out", default=str(ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_proof.md"))

    linux_verify = subparsers.add_parser(
        "linux-verify",
        help="Run or classify the Unreal Linux orientation harness lane",
    )
    add_engine_version(linux_verify)
    linux_verify.add_argument("--unreal", help="Explicit Unreal editor executable path")
    linux_verify.add_argument("--json-out", help="Override the JSON report path")
    linux_verify.add_argument("--md-out", help="Override the Markdown report path")
    linux_verify.add_argument("--dry-run", action="store_true", help="Emit the delegated command and report without executing")
    linux_verify.add_argument("--docker", action="store_true", help="Execute the Linux harness lane inside Docker")
    linux_verify.add_argument("--profile", help="Override the Linux proof profile; defaults to the engine-version matched profile")
    linux_verify.add_argument("--engine-archive", help="Override the Linux Unreal engine zip archive")
    linux_verify.add_argument("--engine-path", help="Override the unpacked Linux Unreal engine directory")
    linux_verify.add_argument("--image", help="Override the Docker image")
    linux_verify.add_argument("--engine-stage-dir", help="Override the staged engine directory")
    linux_verify.add_argument("--force-reextract", action="store_true")
    linux_verify.add_argument("--timeout-seconds", type=int, default=600)

    linux_demo = subparsers.add_parser(
        "linux-demo",
        help="Run or classify the Unreal Linux replay/demo harness lane",
    )
    add_engine_version(linux_demo)
    linux_demo.add_argument("--unreal", help="Explicit Unreal editor executable path")
    linux_demo.add_argument("--json-out", help="Override the JSON report path")
    linux_demo.add_argument("--md-out", help="Override the Markdown report path")
    linux_demo.add_argument("--dry-run", action="store_true", help="Emit the delegated command and report without executing")
    linux_demo.add_argument("--docker", action="store_true", help="Execute the Linux harness lane inside Docker")
    linux_demo.add_argument("--profile", help="Override the Linux proof profile; defaults to the engine-version matched profile")
    linux_demo.add_argument("--engine-archive", help="Override the Linux Unreal engine zip archive")
    linux_demo.add_argument("--engine-path", help="Override the unpacked Linux Unreal engine directory")
    linux_demo.add_argument("--image", help="Override the Docker image")
    linux_demo.add_argument("--engine-stage-dir", help="Override the staged engine directory")
    linux_demo.add_argument("--force-reextract", action="store_true")
    linux_demo.add_argument("--timeout-seconds", type=int, default=600)

    linux_package = subparsers.add_parser(
        "linux-package",
        help="Build and package the FastDIS Unreal plugin for Linux via Docker",
    )
    add_engine_version(linux_package)
    linux_package.add_argument("--profile", help="Override the Linux proof profile; defaults to the engine-version matched profile")
    linux_package.add_argument("--engine-archive", help="Override the Linux Unreal engine zip archive")
    linux_package.add_argument("--engine-path", help="Override the unpacked Linux Unreal engine directory")
    linux_package.add_argument("--image", help="Override the Docker image")
    linux_package.add_argument("--package-dir", help="Override the output package directory")
    linux_package.add_argument("--engine-stage-dir", help="Override the staged engine directory")
    linux_package.add_argument("--force-reextract", action="store_true")

    matrix = subparsers.add_parser("matrix", help="Run the configured Unreal version matrix")
    matrix.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS, help="Versions to run")
    matrix.add_argument("--skip-plugin-build", action="store_true", help="Skip the plugin packaging lane")
    matrix.add_argument("--skip-orientation", action="store_true", help="Skip the orientation harness lane")
    matrix.add_argument("--skip-demo", action="store_true", help="Skip the replay/demo smoke lane")

    full = subparsers.add_parser("full", help="Doctor, package, verify orientation, and run the replay demo smoke for one Unreal lane")
    add_engine_version(full)
    full.add_argument("--open-rider", action="store_true", help="Open the generated host project in Rider after packaging")

    host_lane_matrix = subparsers.add_parser(
        "host-lane-matrix",
        help="Summarize current Unreal macOS and Linux evidence lanes into one host-lane report",
    )
    host_lane_matrix.add_argument("--out-dir", default=str(ROOT / "build" / "reports"))
    host_lane_matrix.add_argument("--unreal-matrix", default=str(ROOT / "build" / "reports" / "unreal_version_matrix.json"))
    host_lane_matrix.add_argument("--linux-proof", default=str(ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_proof.json"))
    host_lane_matrix.add_argument("--linux-verify", default=str(ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_verify.json"))
    host_lane_matrix.add_argument("--linux-demo", default=str(ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_demo.json"))

    return parser.parse_args(argv)


def command_discover(args: argparse.Namespace) -> int:
    installs = [install.to_dict() for install in unreal_env.discover_installs()]
    if args.format == "json":
        print(json.dumps(installs, indent=2))
        return 0 if installs else 1
    if not installs:
        print("No Unreal installs discovered.")
        return 1
    for install in installs:
        version = install["version"] or "unknown"
        quirks = ", ".join(install["quirks"]) if install["quirks"] else "none"
        print(f"{version}: {install['install_root']}")
        print(f"  editor: {install['editor_path'] or 'missing'}")
        print(f"  uat:    {install['uat_path'] or 'missing'}")
        print(f"  ubt:    {install['ubt_path'] or 'missing'}")
        print(f"  dotnet: {install['dotnet_path'] or 'missing'}")
        print(f"  source: {install['source']}")
        print(f"  quirks: {quirks}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.engine_version)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/build_unreal_plugin.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if not args.no_clean_package:
        cmd.append("--clean-package")
    if args.open_rider:
        cmd.append("--open-rider")
    return run_step(cmd)


def command_verify(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_orientation_verification.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_demo(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_demo_smoke.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_install_smoke(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_packaged_install_smoke.py"]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_grill_baseline_init(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/init_unreal_grill_benchmark_baseline.py",
        "--out",
        args.out,
        "--fastdis",
        args.fastdis,
        "--engine-version",
        args.engine_version,
        "--map",
        args.map,
        "--traffic-mix",
        args.traffic_mix,
        "--commit",
        args.commit,
        "--limit-cases",
        str(args.limit_cases),
    ]
    if args.overwrite:
        cmd.append("--overwrite")
    return run_step(cmd)


def command_grill_mapping_export(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/run_grill_unreal_mapping_export.py",
        "--example-root",
        args.example_root,
        "--asset-path",
        args.asset_path,
        "--export-json",
        args.export_json,
        "--json-out",
        args.json_out,
        "--markdown-out",
        args.markdown_out,
    ]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_grill_mapping_import(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/import_unreal_grill_mapping_manifest.py",
        "--input",
        args.input,
        "--fastdis-out",
        args.fastdis_out,
        "--json-out",
        args.json_out,
        "--md-out",
        args.md_out,
        "--source-route",
        args.source_route,
    ]
    if args.search_roots:
        for root in args.search_roots:
            cmd.extend(["--search-root", root])
    return run_step(cmd)


def command_grill_mapping_materialize(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/run_unreal_grill_mapping_materialize.py",
        "--example-root",
        args.example_root,
        "--input-manifest",
        args.input_manifest,
        "--asset-path",
        args.asset_path,
        "--result-json",
        args.result_json,
        "--json-out",
        args.json_out,
        "--markdown-out",
        args.markdown_out,
    ]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_grill_swap_smoke(args: argparse.Namespace) -> int:
    commands: list[list[str]] = []

    export_cmd = unreal_env.python_command() + [
        "tools/run_grill_unreal_mapping_export.py",
        "--example-root",
        args.example_root,
        "--asset-path",
        args.asset_path,
        "--export-json",
        args.export_json,
        "--json-out",
        args.export_report_json,
        "--markdown-out",
        args.export_report_md,
    ]
    if args.engine_version:
        export_cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        export_cmd.append("--dry-run")
    commands.append(export_cmd)

    import_cmd = unreal_env.python_command() + [
        "tools/import_unreal_grill_mapping_manifest.py",
        "--input",
        args.export_json,
        "--fastdis-out",
        args.fastdis_out,
        "--json-out",
        args.import_report_json,
        "--md-out",
        args.import_report_md,
        "--source-route",
        args.source_route,
    ]
    if args.search_roots:
        for root in args.search_roots:
            import_cmd.extend(["--search-root", root])
    commands.append(import_cmd)

    materialize_cmd = unreal_env.python_command() + [
        "tools/run_unreal_grill_mapping_materialize.py",
        "--example-root",
        args.example_root,
        "--input-manifest",
        args.fastdis_out,
        "--asset-path",
        args.materialized_asset_path,
        "--result-json",
        args.materialize_result_json,
        "--json-out",
        args.materialize_report_json,
        "--markdown-out",
        args.materialize_report_md,
    ]
    if args.engine_version:
        materialize_cmd.extend(["--engine-version", args.engine_version])
    if args.dry_run:
        materialize_cmd.append("--dry-run")
    commands.append(materialize_cmd)

    return run_steps(commands)


def command_grill_benchmark(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    cmd = unreal_env.python_command() + [
        "tools/run_unreal_grill_benchmark.py",
        "--fastdis",
        args.fastdis,
        "--json-out",
        str(out_dir / "unreal_vs_grill.json"),
        "--md-out",
        str(out_dir / "unreal_vs_grill.md"),
    ]
    if args.grill_reports:
        for report in args.grill_reports:
            cmd.extend(["--grill-report", report])
    if args.allow_sample_grill:
        cmd.append("--allow-sample-grill")
    return run_step(cmd)


def command_grill_linux_proof(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/capture_grill_unreal_linux_build_proof.py",
        "--plugin-root",
        args.plugin_root,
        "--profile",
        args.profile,
        "--package-dir",
        args.package_dir,
        "--json-out",
        args.json_out,
        "--md-out",
        args.md_out,
    ]
    return run_step(cmd)


def command_fastdis_linux_proof(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/capture_fastdis_unreal_linux_proof.py",
        "--plugin-dir",
        args.plugin_dir,
        "--linux-build-dir",
        args.linux_build_dir,
        "--build-cs",
        args.build_cs,
        "--mac-install-smoke",
        args.mac_install_smoke,
        "--linux-package-dir",
        args.linux_package_dir,
        "--json-out",
        args.json_out,
        "--md-out",
        args.md_out,
    ]
    return run_step(cmd)


def command_linux_package(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/build_unreal_linux_package_docker.py",
        "--profile",
        resolve_linux_profile(args.profile, args.engine_version),
    ]
    if args.engine_archive:
        cmd.extend(["--engine-archive", args.engine_archive])
    if args.engine_path:
        cmd.extend(["--engine-path", args.engine_path])
    if args.image:
        cmd.extend(["--image", args.image])
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    if args.engine_stage_dir:
        cmd.extend(["--engine-stage-dir", args.engine_stage_dir])
    if args.force_reextract:
        cmd.append("--force-reextract")
    return run_step(cmd)


def command_linux_verify(args: argparse.Namespace) -> int:
    runner = "tools/run_unreal_linux_harness_docker.py" if args.docker else "tools/run_unreal_linux_harness.py"
    cmd = unreal_env.python_command() + [
        runner,
        "--mode",
        "verify",
    ]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.unreal:
        cmd.extend(["--unreal", args.unreal])
    if args.json_out:
        cmd.extend(["--json-out", args.json_out])
    if args.md_out:
        cmd.extend(["--md-out", args.md_out])
    if args.docker:
        cmd.extend(["--profile", resolve_linux_profile(args.profile, args.engine_version)])
        if args.engine_archive:
            cmd.extend(["--engine-archive", args.engine_archive])
        if args.engine_path:
            cmd.extend(["--engine-path", args.engine_path])
        if args.image:
            cmd.extend(["--image", args.image])
        if args.engine_stage_dir:
            cmd.extend(["--engine-stage-dir", args.engine_stage_dir])
        if args.force_reextract:
            cmd.append("--force-reextract")
        cmd.extend(["--timeout-seconds", str(args.timeout_seconds)])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_linux_demo(args: argparse.Namespace) -> int:
    runner = "tools/run_unreal_linux_harness_docker.py" if args.docker else "tools/run_unreal_linux_harness.py"
    cmd = unreal_env.python_command() + [
        runner,
        "--mode",
        "demo",
    ]
    if args.engine_version:
        cmd.extend(["--engine-version", args.engine_version])
    if args.unreal:
        cmd.extend(["--unreal", args.unreal])
    if args.json_out:
        cmd.extend(["--json-out", args.json_out])
    if args.md_out:
        cmd.extend(["--md-out", args.md_out])
    if args.docker:
        cmd.extend(["--profile", resolve_linux_profile(args.profile, args.engine_version)])
        if args.engine_archive:
            cmd.extend(["--engine-archive", args.engine_archive])
        if args.engine_path:
            cmd.extend(["--engine-path", args.engine_path])
        if args.image:
            cmd.extend(["--image", args.image])
        if args.engine_stage_dir:
            cmd.extend(["--engine-stage-dir", args.engine_stage_dir])
        if args.force_reextract:
            cmd.append("--force-reextract")
        cmd.extend(["--timeout-seconds", str(args.timeout_seconds)])
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def command_matrix(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + ["tools/run_unreal_matrix.py", "--versions", *args.versions]
    if args.skip_plugin_build:
        cmd.append("--skip-plugin-build")
    if args.skip_orientation:
        cmd.append("--skip-orientation")
    if args.skip_demo:
        cmd.append("--skip-demo")
    return run_step(cmd)


def command_host_lane_matrix(args: argparse.Namespace) -> int:
    cmd = unreal_env.python_command() + [
        "tools/run_unreal_host_lane_matrix.py",
        "--out-dir",
        args.out_dir,
        "--unreal-matrix",
        args.unreal_matrix,
        "--linux-proof",
        args.linux_proof,
        "--linux-verify",
        args.linux_verify,
        "--linux-demo",
        args.linux_demo,
    ]
    return run_step(cmd)


def command_full(args: argparse.Namespace) -> int:
    doctor_args = argparse.Namespace(engine_version=args.engine_version, format="text")
    if command_doctor(doctor_args) != 0:
        return 2

    build_args = argparse.Namespace(
        engine_version=args.engine_version,
        open_rider=args.open_rider,
        no_clean_package=False,
    )
    build_code = command_build(build_args)
    if build_code != 0:
        return build_code

    verify_args = argparse.Namespace(engine_version=args.engine_version, dry_run=False)
    verify_code = command_verify(verify_args)
    if verify_code != 0:
        return verify_code

    demo_args = argparse.Namespace(engine_version=args.engine_version, dry_run=False)
    demo_code = command_demo(demo_args)
    if demo_code != 0:
        return demo_code

    install_smoke_args = argparse.Namespace(engine_version=args.engine_version, dry_run=False)
    return command_install_smoke(install_smoke_args)


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "build":
        return command_build(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command == "demo":
        return command_demo(args)
    if args.command == "install-smoke":
        return command_install_smoke(args)
    if args.command in {"grill-baseline-init", "swap-baseline-init"}:
        return command_grill_baseline_init(args)
    if args.command in {"grill-mapping-export", "swap-mapping-export"}:
        return command_grill_mapping_export(args)
    if args.command in {"grill-mapping-import", "swap-mapping-import"}:
        return command_grill_mapping_import(args)
    if args.command in {"grill-mapping-materialize", "swap-mapping-materialize"}:
        return command_grill_mapping_materialize(args)
    if args.command in {"grill-swap-smoke", "swap-smoke"}:
        return command_grill_swap_smoke(args)
    if args.command in {"grill-benchmark", "swap-benchmark"}:
        return command_grill_benchmark(args)
    if args.command == "grill-linux-proof":
        return command_grill_linux_proof(args)
    if args.command == "linux-proof":
        return command_fastdis_linux_proof(args)
    if args.command == "linux-verify":
        return command_linux_verify(args)
    if args.command == "linux-demo":
        return command_linux_demo(args)
    if args.command == "linux-package":
        return command_linux_package(args)
    if args.command == "matrix":
        return command_matrix(args)
    if args.command == "host-lane-matrix":
        return command_host_lane_matrix(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
