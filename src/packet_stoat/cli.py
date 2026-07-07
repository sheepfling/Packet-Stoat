"""Packet Stoat workspace/meta CLI."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys
from typing import Any

from .runtime import ROOT, run_tool


def _load_workspace_metadata() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tools_dir = str(ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import workspace_manifest  # type: ignore

    manifest = workspace_manifest.load_manifest()
    return workspace_manifest.workspace_metadata(manifest), workspace_manifest.product_trees(manifest)


def command_doctor(_args: argparse.Namespace) -> int:
    workspace, product_trees = _load_workspace_metadata()
    print("Packet Stoat doctor")
    print(f"repo_root: {ROOT}")
    print(f"workspace_id: {workspace.get('id', 'unknown')}")
    print("product_trees:")
    for tree in product_trees:
        print(f"  - {tree['id']}: {tree['label']}")
    print("meta_commands:")
    print("  - host: packet-stoat host [--format text|json|summary]")
    print("  - workspace: packet-stoat workspace doctor|routes|surfaces|hooks|ci|ci-print|ci-sync|ci-check|run [--format text|json|summary]")
    print("  - fresh-host bootstrap: packet-stoat bootstrap (prepares local dev deps first)")
    print("  - bootstrap: packet-stoat bootstrap [doctor] [--skip-godot] [--skip-unreal] [--unreal-version ...] (prepares local dev deps first)")
    print("  - release: packet-stoat release check|deliverables|evidence-pack|check-evidence|epic2-audit|phase2-evidence|benchmark-refresh|benchmark-matrix|benchmark-coverage|benchmark-scenario-contract|benchmark-surface-claims|benchmark-audit|benchmark-claim-summary|benchmark-competitor-summary|benchmark-contract-check|competitor-handoff|competitor-handoff-check|import-competitor-handoff|clean|audit|alpha4-1-gap|integration-matrix")
    print("policy:")
    print("  - Packet Stoat owns workspace orchestration and route discovery.")
    print("  - Product-specific commands belong to product CLIs such as fastdis.")
    return 0


def command_release(args: argparse.Namespace) -> int:
    if args.release_command == "check":
        return run_tool("dev_check.py", args.args)
    if args.release_command == "deliverables":
        return run_tool("list_deliverables.py", args.args)
    if args.release_command == "evidence-pack":
        return run_tool("generate_evidence_pack.py", args.args)
    if args.release_command == "check-evidence":
        return run_tool("check_evidence_pack.py", args.args)
    if args.release_command == "epic2-audit":
        return run_tool("run_epic2_audit.py", args.args)
    if args.release_command == "phase2-evidence":
        return run_tool("run_phase2_evidence_matrix.py", args.args)
    if args.release_command == "benchmark-refresh":
        return run_tool("refresh_engine_benchmark_artifacts.py", args.args)
    if args.release_command == "benchmark-matrix":
        return run_tool("build_benchmark_matrix_report.py", args.args)
    if args.release_command == "benchmark-coverage":
        return run_tool("build_benchmark_coverage_report.py", args.args)
    if args.release_command == "benchmark-scenario-contract":
        return run_tool("build_scenario_contract_report.py", args.args)
    if args.release_command == "benchmark-surface-claims":
        return run_tool("build_surface_claim_report.py", args.args)
    if args.release_command == "benchmark-audit":
        return run_tool("audit_engine_benchmark_completion.py", args.args)
    if args.release_command == "benchmark-claim-summary":
        return run_tool("build_benchmark_claim_summary.py", args.args)
    if args.release_command == "benchmark-competitor-summary":
        return run_tool("build_competitor_lane_summary.py", args.args)
    if args.release_command == "benchmark-contract-check":
        return run_tool("check_benchmark_contract_stack.py", args.args)
    if args.release_command == "competitor-handoff":
        return run_tool("export_competitor_benchmark_handoff.py", args.args)
    if args.release_command == "competitor-handoff-check":
        return run_tool("check_competitor_handoff_workbench.py", args.args)
    if args.release_command == "import-competitor-handoff":
        return run_tool("import_competitor_benchmark_handoff.py", args.args)
    if args.release_command == "clean":
        return run_tool("clean_artifacts.py", args.args)
    if args.release_command == "audit":
        return run_tool("run_alpha4_release_audit.py", args.args)
    if args.release_command == "alpha4-1-gap":
        return run_tool("run_alpha4_1_sdk_gap_report.py", args.args)
    if args.release_command == "integration-matrix":
        return run_tool("run_alpha5_integration_matrix.py", args.args)
    raise SystemExit(f"Unknown release command: {args.release_command}")


def command_bootstrap(args: argparse.Namespace) -> int:
    prep_rc = run_tool("bootstrap_local_dev.py", ["--prepare-only"])
    if prep_rc != 0:
        return prep_rc
    cmd = ["bootstrap_workflow.py"]
    if getattr(args, "bootstrap_mode", None) == "doctor" or getattr(args, "doctor", False):
        cmd.append("--doctor")
    if getattr(args, "skip_godot", False):
        cmd.append("--skip-godot")
    if getattr(args, "skip_unreal", False):
        cmd.append("--skip-unreal")
    if getattr(args, "unreal_version", None):
        cmd.extend(["--unreal-version", args.unreal_version])
    cmd.extend(getattr(args, "args", []))
    return run_tool(cmd[0], cmd[1:])


def command_host(args: argparse.Namespace) -> int:
    cmd = ["host_capability_matrix.py"]
    if getattr(args, "format", None):
        cmd.extend(["--format", args.format])
    return run_tool(cmd[0], cmd[1:])


def command_workspace(args: argparse.Namespace) -> int:
    if getattr(args, "workspace_command", None) == "ci-print":
        cmd = ["print", "--path", ".github/workflows/generated/workspace-ci-matrix.json"]
        if getattr(args, "section", None):
            cmd.extend(["--section", args.section])
        if getattr(args, "format", None):
            matrix_format = "json" if args.format == "text" else args.format
            cmd.extend(["--format", matrix_format])
        return run_tool("generate_workspace_ci_matrix.py", cmd)
    if getattr(args, "workspace_command", None) == "ci-sync":
        return run_tool(
            "generate_workspace_ci_matrix.py",
            ["write", "--path", ".github/workflows/generated/workspace-ci-matrix.json"],
        )
    if getattr(args, "workspace_command", None) == "ci-check":
        return run_tool(
            "generate_workspace_ci_matrix.py",
            ["check", "--path", ".github/workflows/generated/workspace-ci-matrix.json"],
        )
    if getattr(args, "workspace_command", None) == "run":
        return run_tool("workspace_hook_runner.py", [args.surface, args.hook])
    cmd = ["host_capability_matrix.py"]
    if getattr(args, "workspace_command", None) == "ci":
        cmd.extend(["--view", "ci"])
    if getattr(args, "workspace_command", None) == "routes":
        cmd.extend(["--view", "routes"])
    if getattr(args, "workspace_command", None) == "surfaces":
        cmd.extend(["--view", "surfaces"])
    if getattr(args, "workspace_command", None) == "hooks":
        cmd.extend(["--view", "hooks"])
    if getattr(args, "category", None):
        cmd.extend(["--category", args.category])
    if getattr(args, "host_class", None):
        cmd.extend(["--host-class", args.host_class])
    if getattr(args, "surface_filter", None):
        cmd.extend(["--surface", args.surface_filter])
    if getattr(args, "proof_kind", None):
        cmd.extend(["--proof-kind", args.proof_kind])
    if getattr(args, "bootstrap_only", False):
        cmd.append("--bootstrap-only")
    if getattr(args, "include_compat", False):
        cmd.append("--include-compat")
    if getattr(args, "format", None):
        cmd.extend(["--format", args.format])
    return run_tool(cmd[0], cmd[1:])


def _parse_workspace_shortcut(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="packet-stoat workspace")
    parser.add_argument("workspace_command", choices=("doctor", "routes", "surfaces", "hooks", "ci", "ci-print", "ci-sync", "ci-check", "run"))
    parser.add_argument("surface", nargs="?")
    parser.add_argument("hook", nargs="?")
    parser.add_argument("--category", choices=("lifecycle", "proof", "demo", "packaging", "install"))
    parser.add_argument("--host-class", choices=("windows", "macos", "linux"))
    parser.add_argument("--surface-filter")
    parser.add_argument("--proof-kind")
    parser.add_argument(
        "--section",
        choices=("document", "python_green", "native_green", "workspace_ci", "workspace_ci_host_python", "workspace_ci_declared_engine", "workspace_ci_declared_cross_build"),
        default="document",
    )
    parser.add_argument("--bootstrap-only", action="store_true")
    parser.add_argument("--include-compat", action="store_true")
    parser.add_argument("--format", choices=("text", "json", "summary"), default="text")
    parsed = parser.parse_args(list(argv[1:]))
    return argparse.Namespace(
        command="workspace",
        workspace_command=parsed.workspace_command,
        surface=parsed.surface,
        hook=parsed.hook,
        category=parsed.category,
        host_class=parsed.host_class,
        surface_filter=parsed.surface_filter,
        proof_kind=parsed.proof_kind,
        section=parsed.section,
        bootstrap_only=parsed.bootstrap_only,
        include_compat=parsed.include_compat,
        format=parsed.format,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["workspace"] and len(argv) >= 2:
        return _parse_workspace_shortcut(argv)
    if argv[:1] == ["release"] and len(argv) >= 2:
        return argparse.Namespace(command="release", release_command=argv[1], args=argv[2:])
    if argv[:2] == ["bootstrap", "doctor"]:
        return argparse.Namespace(command="bootstrap", bootstrap_mode="doctor", args=argv[2:])
    parser = argparse.ArgumentParser(
        prog="packet-stoat",
        description="Packet Stoat workspace CLI for repo-level route discovery, host readiness, and bootstrap flows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Print workspace/meta support and entry points")
    bootstrap = subparsers.add_parser("bootstrap", help="Host-smart bootstrap for workspace-managed routes")
    bootstrap.add_argument("--doctor", action="store_true", help="Print a one-screen discovery summary and exit")
    bootstrap.add_argument("--skip-godot", action="store_true", help="Skip the Godot bootstrap lane")
    bootstrap.add_argument("--skip-unreal", action="store_true", help="Skip the Unreal bootstrap lane")
    bootstrap.add_argument("--unreal-version", help="Explicit Unreal version for the Unreal lane")
    host = subparsers.add_parser("host", help="Summarize which workspace routes are workable on this host")
    host.add_argument("--format", choices=("text", "json", "summary"), default="text")
    workspace = subparsers.add_parser("workspace", help="Inspect the manifest-driven workspace routes and host readiness")
    workspace_subparsers = workspace.add_subparsers(dest="workspace_command", required=True)
    workspace_doctor = workspace_subparsers.add_parser("doctor", help="Print the manifest-driven workspace/route readiness view")
    workspace_doctor.add_argument("--format", choices=("text", "json", "summary"), default="text")
    workspace_routes = workspace_subparsers.add_parser("routes", help="List workspace routes tempered by current host installs")
    workspace_routes.add_argument("--format", choices=("text", "json", "summary"), default="text")
    workspace_surfaces = workspace_subparsers.add_parser("surfaces", help="List declarative workspace surfaces and generic hooks")
    workspace_surfaces.add_argument("--format", choices=("text", "json", "summary"), default="text")
    workspace_hooks = workspace_subparsers.add_parser("hooks", help="List declarative workspace hooks, optionally filtered by category")
    workspace_hooks.add_argument("--category", choices=("lifecycle", "proof", "demo", "packaging", "install"))
    workspace_hooks.add_argument("--format", choices=("text", "json", "summary"), default="text")
    workspace_ci = workspace_subparsers.add_parser("ci", help="Emit a manifest-driven CI matrix view")
    workspace_ci.add_argument("--host-class", choices=("windows", "macos", "linux"))
    workspace_ci.add_argument("--surface-filter")
    workspace_ci.add_argument("--proof-kind")
    workspace_ci.add_argument("--bootstrap-only", action="store_true")
    workspace_ci.add_argument("--include-compat", action="store_true")
    workspace_ci.add_argument("--format", choices=("text", "json", "summary"), default="text")
    workspace_ci_print = workspace_subparsers.add_parser("ci-print", help="Print the checked-in GitHub Actions workspace CI matrix")
    workspace_ci_print.add_argument(
        "--section",
        choices=("document", "python_green", "native_green", "workspace_ci", "workspace_ci_host_python", "workspace_ci_declared_engine", "workspace_ci_declared_cross_build"),
        default="document",
    )
    workspace_ci_print.add_argument("--format", choices=("text", "json", "summary"), default="summary")
    workspace_subparsers.add_parser("ci-sync", help="Refresh the checked-in GitHub Actions workspace CI matrix")
    workspace_subparsers.add_parser("ci-check", help="Verify the checked-in GitHub Actions workspace CI matrix matches the manifest")
    workspace_run = workspace_subparsers.add_parser("run", help="Run a manifest-declared hook for a surface")
    workspace_run.add_argument("surface")
    workspace_run.add_argument("hook")
    release = subparsers.add_parser("release", help="Run workspace/release/audit workflows")
    release.add_argument(
        "release_command",
        choices=("check", "deliverables", "evidence-pack", "check-evidence", "epic2-audit", "phase2-evidence", "benchmark-refresh", "benchmark-matrix", "benchmark-coverage", "benchmark-scenario-contract", "benchmark-surface-claims", "benchmark-audit", "benchmark-claim-summary", "benchmark-competitor-summary", "benchmark-contract-check", "competitor-handoff", "competitor-handoff-check", "import-competitor-handoff", "clean", "audit", "alpha4-1-gap", "integration-matrix"),
    )
    release.add_argument("args", nargs=argparse.REMAINDER)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "bootstrap":
        return command_bootstrap(args)
    if args.command == "host":
        return command_host(args)
    if args.command == "workspace":
        return command_workspace(args)
    if args.command == "release":
        return command_release(args)
    raise SystemExit(f"Unknown command: {args.command}")
