"""FastDIS Lattice adapter CLI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"


def env() -> dict[str, str]:
    payload = os.environ.copy()
    extra_paths = [str(SRC), str(ADAPTER_SRC)]
    pythonpath = payload.get("PYTHONPATH")
    payload["PYTHONPATH"] = os.pathsep.join(extra_paths if not pythonpath else [*extra_paths, pythonpath])
    return payload


def run(cmd: Sequence[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(list(cmd), cwd=ROOT, env=env())
    return completed.returncode


def run_tool(tool: str, args: Sequence[str]) -> int:
    return run([sys.executable, str(ROOT / "tools" / tool), *args])


def command_doctor(_args: argparse.Namespace) -> int:
    print("FastDIS Lattice doctor")
    print(f"repo_root: {ROOT}")
    print(f"python: {sys.executable}")
    print("lanes:")
    print("  - adapter: fastdis-lattice discover|doctor|dis-to-shim|shim-to-dis|lab-state|report|verify|showcase|full")
    print("  - surrogate-zorn: fastdis-lattice zorn-bridge doctor|dis-to-shim|shim-to-dis|lab-state")
    print("  - audits: fastdis-lattice sdk-check|contract-audit|sample-parity-audit|zorn-rest-sdk-probe")
    print("  - package: python -m build packages/lattice")
    print("  - core dependency: fastdis provides the canonical DIS/native inputs; it does not own Lattice workflow commands")
    print("  - live-lattice: packet-stoat-lattice[sdk] remains credential-gated; Zorn-compatible surrogate lanes are the default verification path")
    return 0


def command_workflow(args: argparse.Namespace) -> int:
    return run_tool("lattice_workflow.py", [args.workflow_command, *args.args])


def command_zorn_bridge(args: argparse.Namespace) -> int:
    return run_tool("lattice_zorn_bridge.py", [args.bridge_command, *args.args])


def command_audit(args: argparse.Namespace) -> int:
    if args.command == "sdk-check":
        return run_tool("run_alpha4_1_sdk_gap_report.py", args.args)
    if args.command == "contract-audit":
        return run_tool("lattice_contract_audit.py", args.args)
    if args.command == "sample-parity-audit":
        return run_tool("lattice_sample_parity_audit.py", args.args)
    if args.command == "zorn-rest-sdk-probe":
        return run_tool("lattice_zorn_rest_sdk_probe.py", args.args)
    raise SystemExit(f"Unknown lattice audit command: {args.command}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    workflow_commands = {
        "discover",
        "doctor",
        "dis-to-shim",
        "shim-to-dis",
        "lab-state",
        "report",
        "verify",
        "showcase",
        "full",
    }
    if argv[:1] == ["doctor"] and len(argv) > 1:
        return argparse.Namespace(command="workflow", workflow_command="doctor", args=argv[1:])
    if argv[:1] and argv[0] in workflow_commands - {"doctor"}:
        return argparse.Namespace(command="workflow", workflow_command=argv[0], args=argv[1:])
    if argv[:1] == ["zorn-bridge"] and len(argv) >= 2:
        return argparse.Namespace(command="zorn-bridge", bridge_command=argv[1], args=argv[2:])
    if argv[:1] and argv[0] in {"sdk-check", "contract-audit", "sample-parity-audit", "zorn-rest-sdk-probe"}:
        return argparse.Namespace(command=argv[0], args=argv[1:])

    parser = argparse.ArgumentParser(
        prog="fastdis-lattice",
        description="FastDIS Lattice adapter CLI for packet_stoat_lattice workflows and surrogate verification.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Print the lattice adapter workflow surface")
    for name in sorted(workflow_commands - {"doctor"}):
        workflow = subparsers.add_parser(name, help=f"Run the lattice workflow {name} lane")
        workflow.add_argument("args", nargs=argparse.REMAINDER)

    zorn = subparsers.add_parser("zorn-bridge", help="Run the local Zorn-compatible surrogate bridge")
    zorn.add_argument("bridge_command", choices=("doctor", "dis-to-shim", "shim-to-dis", "lab-state"))
    zorn.add_argument("args", nargs=argparse.REMAINDER)

    for name in ("sdk-check", "contract-audit", "sample-parity-audit", "zorn-rest-sdk-probe"):
        audit = subparsers.add_parser(name, help=f"Run the lattice {name} audit lane")
        audit.add_argument("args", nargs=argparse.REMAINDER)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "workflow":
        return command_workflow(args)
    if args.command in {
        "discover",
        "dis-to-shim",
        "shim-to-dis",
        "lab-state",
        "report",
        "verify",
        "showcase",
        "full",
    }:
        args.workflow_command = args.command
        return command_workflow(args)
    if args.command == "zorn-bridge":
        return command_zorn_bridge(args)
    if args.command in {"sdk-check", "contract-audit", "sample-parity-audit", "zorn-rest-sdk-probe"}:
        return command_audit(args)
    raise SystemExit(f"Unknown command: {args.command}")
