"""Operator-facing Packet Stoat command line wrapper."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence

from .catalog import supported_pdu_families, supported_protocol_versions
from .native import find_native_library, load_native


ROOT = Path(__file__).resolve().parents[2]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    return env


def _run(cmd: Sequence[str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(list(cmd), cwd=ROOT, env=_env())
    return completed.returncode


def _run_module(module: str, args: Sequence[str]) -> int:
    return _run([sys.executable, "-m", module, *args])


def _run_tool(tool: str, args: Sequence[str]) -> int:
    return _run([sys.executable, str(ROOT / "tools" / tool), *args])


def command_doctor(_args: argparse.Namespace) -> int:
    native_library = find_native_library()
    print("FastDIS doctor")
    print(f"repo_root: {ROOT}")
    print(f"python: {sys.executable}")
    print(f"protocol_versions: {', '.join(str(version) for version in supported_protocol_versions())}")
    print(f"pdu_families: {', '.join(supported_pdu_families())}")
    print(f"native_library: {native_library or 'not found'}")
    if native_library:
        try:
            native = load_native(native_library)
        except Exception as exc:  # pragma: no cover - exercised via CLI lane
            print(f"native_library_load_error: {exc}")
        else:
            abi_status = "unpublished/internal" if native.abi_epoch() == 0 else "public"
            print(f"abi_epoch: {native.abi_epoch()}")
            print(f"abi_revision: {native.abi_revision()}")
            print(f"abi_version_guard: {native.abi_version()}")
            print(f"abi_status: {abi_status}")
    print("lanes:")
    print("  - python: fastdis recv/send-entity/replay-send/net-smoke/pdu/replay")
    print("  - pdu-json: fastdis pdu inspect|to-json|from-json")
    print("  - replay-json: fastdis replay inspect|to-json|from-json|roundtrip|diff")
    print("  - simtest: fastdis simtest compare|bless|inspect")
    print("  - enums: fastdis enums check|lookup|entity-type|describe-header")
    print("  - logging: fastdis logging check")
    print("  - standards: fastdis standards check|refresh")
    print("  - evidence: fastdis release evidence-pack|check-evidence|epic2-audit|benchmark-refresh|benchmark-matrix|benchmark-coverage|benchmark-scenario-contract|benchmark-surface-claims|benchmark-audit|benchmark-claim-summary|benchmark-competitor-summary|benchmark-contract-check|competitor-handoff|competitor-handoff-check|import-competitor-handoff")
    print("  - bootstrap: fastdis bootstrap [doctor] [--skip-godot] [--skip-unreal] [--unreal-version ...]")
    print("  - unreal: fastdis engine unreal doctor|build|verify|demo|install-smoke|grill-baseline-init|grill-benchmark|matrix|full")
    print("  - godot: fastdis engine godot discover|doctor|bootstrap|build|verify|demo|report|full")
    print("  - unity: fastdis engine unity discover|doctor|build[ --all-native]|verify|demo|bridge-probe|orientation-verify|startup-probe|install-smoke|install-matrix|adopt-install-smoke|stage-host-report|export-host-report|export-host-handoff|import-host-report|sync-host-reports|host-matrix|capture-host-report|runtime-verify|report|parity-check|signoff|cross-engine-equivalence|head-to-head-benchmark|grill-baseline-init|grill-import-smoke|full")
    print("  - orient: fastdis orient summary --refresh")
    print("  - lattice: fastdis lattice doctor|dis-to-shim|shim-to-dis|lab-state|report|sdk-check|full")
    print("  - lattice-backend: python tools/lattice_backend.py doctor")
    return 0


def command_support(_args: argparse.Namespace) -> int:
    print("FASTDIS support surface")
    print(f"Protocol versions: {', '.join(str(version) for version in supported_protocol_versions())}")
    print(f"PDU families: {', '.join(supported_pdu_families())}")
    return 0


def command_bench(args: argparse.Namespace) -> int:
    return _run_tool("run_benchmarks.py", args.args)


def command_release(args: argparse.Namespace) -> int:
    if args.release_command == "check":
        return _run_tool("dev_check.py", args.args)
    if args.release_command == "deliverables":
        return _run_tool("list_deliverables.py", args.args)
    if args.release_command == "evidence-pack":
        return _run_tool("generate_evidence_pack.py", args.args)
    if args.release_command == "check-evidence":
        return _run_tool("check_evidence_pack.py", args.args)
    if args.release_command == "epic2-audit":
        return _run_tool("run_epic2_audit.py", args.args)
    if args.release_command == "benchmark-refresh":
        return _run_tool("refresh_engine_benchmark_artifacts.py", args.args)
    if args.release_command == "benchmark-matrix":
        return _run_tool("build_benchmark_matrix_report.py", args.args)
    if args.release_command == "benchmark-coverage":
        return _run_tool("build_benchmark_coverage_report.py", args.args)
    if args.release_command == "benchmark-scenario-contract":
        return _run_tool("build_scenario_contract_report.py", args.args)
    if args.release_command == "benchmark-surface-claims":
        return _run_tool("build_surface_claim_report.py", args.args)
    if args.release_command == "benchmark-audit":
        return _run_tool("audit_engine_benchmark_completion.py", args.args)
    if args.release_command == "benchmark-claim-summary":
        return _run_tool("build_benchmark_claim_summary.py", args.args)
    if args.release_command == "benchmark-competitor-summary":
        return _run_tool("build_competitor_lane_summary.py", args.args)
    if args.release_command == "benchmark-contract-check":
        return _run_tool("check_benchmark_contract_stack.py", args.args)
    if args.release_command == "competitor-handoff":
        return _run_tool("export_competitor_benchmark_handoff.py", args.args)
    if args.release_command == "competitor-handoff-check":
        return _run_tool("check_competitor_handoff_workbench.py", args.args)
    if args.release_command == "import-competitor-handoff":
        return _run_tool("import_competitor_benchmark_handoff.py", args.args)
    if args.release_command == "clean":
        return _run_tool("clean_artifacts.py", args.args)
    if args.release_command == "audit":
        return _run_tool("run_alpha4_release_audit.py", args.args)
    if args.release_command == "alpha4-1-gap":
        return _run_tool("run_alpha4_1_sdk_gap_report.py", args.args)
    if args.release_command == "integration-matrix":
        return _run_tool("run_alpha5_integration_matrix.py", args.args)
    raise SystemExit(f"Unknown release command: {args.release_command}")


def command_engine(args: argparse.Namespace) -> int:
    if args.engine == "unreal":
        return _run_tool("unreal_workflow.py", [args.workflow_command, *args.args])
    if args.engine == "godot":
        return _run_tool("godot_workflow.py", [args.workflow_command, *args.args])
    if args.engine == "unity":
        return _run_tool("unity_workflow.py", [args.workflow_command, *args.args])
    raise SystemExit(f"Unknown engine: {args.engine}")


def command_bootstrap(args: argparse.Namespace) -> int:
    cmd = ["bootstrap_workflow.py"]
    if getattr(args, "bootstrap_mode", None) == "doctor":
        cmd.append("--doctor")
    if getattr(args, "skip_godot", False):
        cmd.append("--skip-godot")
    if getattr(args, "skip_unreal", False):
        cmd.append("--skip-unreal")
    if getattr(args, "unreal_version", None):
        cmd.extend(["--unreal-version", args.unreal_version])
    cmd.extend(getattr(args, "args", []))
    return _run_tool(cmd[0], cmd[1:])


def command_lattice(args: argparse.Namespace) -> int:
    if args.lattice_command == "sdk-check":
        return _run_tool("run_alpha4_1_sdk_gap_report.py", args.args)
    if args.lattice_command == "contract-audit":
        return _run_tool("lattice_contract_audit.py", args.args)
    return _run_tool("lattice_workflow.py", [args.lattice_command, *args.args])


def command_orient(args: argparse.Namespace) -> int:
    if args.orient_command == "summary":
        return _run_tool("run_engine_orientation_summary.py", args.args)
    raise SystemExit(f"Unknown orient command: {args.orient_command}")


def command_pdu(args: argparse.Namespace) -> int:
    return _run_module("fastdis.tools.pdu_json", [args.pdu_command, *args.args])


def command_replay(args: argparse.Namespace) -> int:
    return _run_module("fastdis.tools.replay_json", [args.replay_command, *args.args])


def command_simtest(args: argparse.Namespace) -> int:
    return _run_module("fastdis.tools.simtest", [args.simtest_command, *args.args])


def command_enums(args: argparse.Namespace) -> int:
    from .tools.enums import main as enums_main

    return enums_main([args.enums_command, *args.args])


def command_logging(args: argparse.Namespace) -> int:
    if args.logging_command == "check":
        from .tools.logging_check import main as logging_check_main

        return logging_check_main(args.args)
    raise SystemExit(f"Unknown logging command: {args.logging_command}")


def command_standards(args: argparse.Namespace) -> int:
    if args.standards_command == "check":
        return _run_tool("generate_standards_status.py", ["--check", *args.args])
    if args.standards_command == "refresh":
        return _run_tool("generate_standards_status.py", args.args)
    raise SystemExit(f"Unknown standards command: {args.standards_command}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    passthrough_commands = {"recv", "send-entity", "capture", "replay-send", "net-smoke", "bench"}
    if argv and argv[0] in passthrough_commands:
        return argparse.Namespace(command=argv[0], args=argv[1:])
    if argv[:1] == ["engine"] and len(argv) >= 3:
        return argparse.Namespace(command="engine", engine=argv[1], workflow_command=argv[2], args=argv[3:])
    if argv[:1] == ["lattice"] and len(argv) >= 2:
        return argparse.Namespace(command="lattice", lattice_command=argv[1], args=argv[2:])
    if argv[:1] == ["orient"] and len(argv) >= 2:
        return argparse.Namespace(command="orient", orient_command=argv[1], args=argv[2:])
    if argv[:1] == ["release"] and len(argv) >= 2:
        return argparse.Namespace(command="release", release_command=argv[1], args=argv[2:])
    if argv[:1] == ["pdu"] and len(argv) >= 2:
        return argparse.Namespace(command="pdu", pdu_command=argv[1], args=argv[2:])
    if argv[:1] == ["replay"] and len(argv) >= 2:
        return argparse.Namespace(command="replay", replay_command=argv[1], args=argv[2:])
    if argv[:1] == ["simtest"] and len(argv) >= 2:
        return argparse.Namespace(command="simtest", simtest_command=argv[1], args=argv[2:])
    if argv[:1] == ["enums"] and len(argv) >= 2:
        return argparse.Namespace(command="enums", enums_command=argv[1], args=argv[2:])
    if argv[:1] == ["logging"] and len(argv) >= 2:
        return argparse.Namespace(command="logging", logging_command=argv[1], args=argv[2:])
    if argv[:1] == ["standards"] and len(argv) >= 2:
        return argparse.Namespace(command="standards", standards_command=argv[1], args=argv[2:])
    if argv[:2] == ["bootstrap", "doctor"]:
        return argparse.Namespace(command="bootstrap", bootstrap_mode="doctor", args=argv[2:])

    parser = argparse.ArgumentParser(
        prog="fastdis",
        description="FastDIS operator CLI for DIS scanning, engine workflows, and external-backend Lattice bridge workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Print local support and workflow entry points")
    bootstrap = subparsers.add_parser("bootstrap", help="Host-smart bootstrap for Godot and Unreal routes")
    bootstrap.add_argument("--doctor", action="store_true", help="Print a one-screen discovery summary and exit")
    bootstrap.add_argument("--skip-godot", action="store_true", help="Skip the Godot bootstrap lane")
    bootstrap.add_argument("--skip-unreal", action="store_true", help="Skip the Unreal bootstrap lane")
    bootstrap.add_argument("--unreal-version", help="Explicit Unreal version for the Unreal lane")
    subparsers.add_parser("support", help="Print the low-level fastdis support surface")

    recv = subparsers.add_parser("recv", help="Receive and optionally verify DIS UDP packets")
    recv.add_argument("args", nargs=argparse.REMAINDER)

    send_entity = subparsers.add_parser("send-entity", help="Send synthetic DIS Entity State packets")
    send_entity.add_argument("args", nargs=argparse.REMAINDER)

    capture = subparsers.add_parser("capture", help="Capture UDP packets to replay")
    capture.add_argument("args", nargs=argparse.REMAINDER)

    replay_send = subparsers.add_parser("replay-send", help="Send replay packets over UDP")
    replay_send.add_argument("args", nargs=argparse.REMAINDER)

    net_smoke = subparsers.add_parser("net-smoke", help="Run local UDP/network smoke verification")
    net_smoke.add_argument("args", nargs=argparse.REMAINDER)

    bench = subparsers.add_parser("bench", help="Run native/Python benchmark workflows")
    bench.add_argument("args", nargs=argparse.REMAINDER)

    pdu = subparsers.add_parser("pdu", help="Inspect or convert single DIS PDU packets")
    pdu.add_argument("pdu_command", choices=("inspect", "to-json", "from-json"))
    pdu.add_argument("args", nargs=argparse.REMAINDER)

    replay = subparsers.add_parser("replay", help="Inspect or convert `.fastdispkt` replay files")
    replay.add_argument("replay_command", choices=("inspect", "to-json", "from-json", "roundtrip", "diff"))
    replay.add_argument("args", nargs=argparse.REMAINDER)

    simtest = subparsers.add_parser("simtest", help="Compare deterministic sim metadata and crop baselines")
    simtest.add_argument("simtest_command", choices=("compare", "bless", "inspect"))
    simtest.add_argument("args", nargs=argparse.REMAINDER)

    enums = subparsers.add_parser("enums", help="Inspect SISO-style enum labels and coverage")
    enums.add_argument("enums_command", choices=("check", "lookup", "entity-type", "describe-header"))
    enums.add_argument("args", nargs=argparse.REMAINDER)

    logging = subparsers.add_parser("logging", help="Inspect generated PDU logging coverage")
    logging.add_argument("logging_command", choices=("check",))
    logging.add_argument("args", nargs=argparse.REMAINDER)

    standards = subparsers.add_parser("standards", help="Inspect standards/update readiness")
    standards.add_argument("standards_command", choices=("check", "refresh"))
    standards.add_argument("args", nargs=argparse.REMAINDER)

    engine = subparsers.add_parser("engine", help="Run engine workflow commands")
    engine_subparsers = engine.add_subparsers(dest="engine", required=True)
    for name in ("unreal", "godot", "unity"):
        engine_parser = engine_subparsers.add_parser(name, help=f"Run {name} workflow commands")
        engine_parser.add_argument("workflow_command")
        engine_parser.add_argument("args", nargs=argparse.REMAINDER)

    lattice = subparsers.add_parser("lattice", help="Run Lattice bridge workflow commands")
    lattice.add_argument("lattice_command")
    lattice.add_argument("args", nargs=argparse.REMAINDER)

    orient = subparsers.add_parser("orient", help="Run orientation verification workflows")
    orient.add_argument("orient_command", choices=("summary",))
    orient.add_argument("args", nargs=argparse.REMAINDER)

    release = subparsers.add_parser("release", help="Run release/audit workflows")
    release.add_argument(
        "release_command",
        choices=("check", "deliverables", "evidence-pack", "check-evidence", "epic2-audit", "benchmark-refresh", "benchmark-matrix", "benchmark-coverage", "benchmark-scenario-contract", "benchmark-surface-claims", "benchmark-audit", "benchmark-claim-summary", "benchmark-competitor-summary", "benchmark-contract-check", "competitor-handoff", "competitor-handoff-check", "import-competitor-handoff", "clean", "audit", "alpha4-1-gap", "integration-matrix"),
    )
    release.add_argument("args", nargs=argparse.REMAINDER)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "bootstrap":
        return command_bootstrap(args)
    if args.command == "support":
        return command_support(args)
    if args.command == "recv":
        return _run_module("fastdis.tools.recv", args.args)
    if args.command == "send-entity":
        return _run_module("fastdis.tools.send_entity", args.args)
    if args.command == "capture":
        return _run_module("fastdis.tools.capture", args.args)
    if args.command == "replay-send":
        return _run_module("fastdis.tools.replay_send", args.args)
    if args.command == "net-smoke":
        return _run_module("fastdis.tools.net_smoke", args.args)
    if args.command == "bench":
        return command_bench(args)
    if args.command == "pdu":
        return command_pdu(args)
    if args.command == "replay":
        return command_replay(args)
    if args.command == "simtest":
        return command_simtest(args)
    if args.command == "enums":
        return command_enums(args)
    if args.command == "logging":
        return command_logging(args)
    if args.command == "standards":
        return command_standards(args)
    if args.command == "engine":
        return command_engine(args)
    if args.command == "lattice":
        return command_lattice(args)
    if args.command == "orient":
        return command_orient(args)
    if args.command == "release":
        return command_release(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
