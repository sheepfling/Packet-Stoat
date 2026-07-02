"""FastDIS engine workflow CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from packet_stoat.runtime import ROOT, run as _runtime_run


def _run(cmd: Sequence[str]) -> int:
    return _runtime_run(cmd)


def _run_tool(tool: str, args: Sequence[str]) -> int:
    return _run([sys.executable, str(ROOT / "tools" / tool), *args])


def command_doctor(_args: argparse.Namespace) -> int:
    print("FastDIS Engine doctor")
    print(f"repo_root: {ROOT}")
    print(f"python: {sys.executable}")
    print("lanes:")
    print("  - unreal: fastdis-engine unreal doctor|build|verify|demo|install-smoke|grill-baseline-init|grill-benchmark|matrix|full")
    print("  - godot: fastdis-engine godot discover|doctor|bootstrap|build|verify|demo|report|full")
    print("  - unity: fastdis-engine unity discover|doctor|build[ --all-native]|verify|demo|bridge-probe|orientation-verify|startup-probe|install-smoke|install-matrix|adopt-install-smoke|stage-host-report|export-host-report|export-host-handoff|import-host-report|sync-host-reports|host-matrix|capture-host-report|runtime-verify|report|parity-check|signoff|cross-engine-equivalence|head-to-head-benchmark|grill-baseline-init|grill-import-smoke|full")
    print("  - fastdis core: fastdis doctor|support|recv|send-entity|capture|replay-send|net-smoke|bench|pdu|replay|simtest|enums|logging|standards|orient|lattice")
    print("  - packet-stoat meta: packet-stoat doctor|host|workspace|bootstrap|release")
    return 0


def command_engine(args: argparse.Namespace) -> int:
    if args.engine == "unreal":
        return _run_tool("unreal_workflow.py", [args.workflow_command, *args.args])
    if args.engine == "godot":
        return _run_tool("godot_workflow.py", [args.workflow_command, *args.args])
    if args.engine == "unity":
        return _run_tool("unity_workflow.py", [args.workflow_command, *args.args])
    raise SystemExit(f"Unknown engine: {args.engine}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["unreal"], ["godot"], ["unity"]) and len(argv) >= 2:
        return argparse.Namespace(command="engine", engine=argv[0], workflow_command=argv[1], args=argv[2:])
    parser = argparse.ArgumentParser(
        prog="fastdis-engine",
        description="FastDIS engine CLI for plugin builds, engine proofs, and benchmarking workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Print engine workflow entry points")

    for name in ("unreal", "godot", "unity"):
        engine = subparsers.add_parser(name, help=f"Run {name} workflow commands")
        engine.add_argument("workflow_command")
        engine.add_argument("args", nargs=argparse.REMAINDER)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command in {"unreal", "godot", "unity"}:
        args.engine = args.command
        return command_engine(args)
    if args.command == "engine":
        return command_engine(args)
    raise SystemExit(f"Unknown command: {args.command}")
