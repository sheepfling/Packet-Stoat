#!/usr/bin/env python3
"""Operator-facing workflow wrapper for the FastDIS Lattice backend lanes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts import VERIFICATION_REPORTS_DIR
import load_local_env
from fastdis.lattice_backend import backend_status, load_lattice_backend_config
from fastdis.native import find_native_library

DEFAULT_OUT_ROOT = VERIFICATION_REPORTS_DIR / "alpha4" / "lattice"
DEFAULT_DIS_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "dis_entity_fixture.json"
DEFAULT_TRACK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "lattice_track_fixture.json"
DEFAULT_OBJECT_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "object_fixture.json"
DEFAULT_TASK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "task_fixture.json"
DEFAULT_EVENT_LOG = "shim_event_log.jsonl"
DEFAULT_SUMMARY_BASENAME = "alpha4_lattice_report"
DEFAULT_AUDIT_SCRIPT = ROOT / "tools" / "run_alpha4_release_audit.py"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    return completed.returncode


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_payload() -> dict[str, object]:
    backend = backend_status()
    return {
        "python": sys.executable,
        "repo_root": str(ROOT),
        "integration_src": str(ROOT / "integrations" / "lattice" / "src"),
        "backend": backend,
        "default_out_root": str(DEFAULT_OUT_ROOT),
        "dis_fixture": str(DEFAULT_DIS_FIXTURE),
        "track_fixture": str(DEFAULT_TRACK_FIXTURE),
        "object_fixture": str(DEFAULT_OBJECT_FIXTURE),
        "task_fixture": str(DEFAULT_TASK_FIXTURE),
        "tools": {
            "lattice_publish_module": "fastdis.tools.lattice_publish",
            "lattice_backend_doctor": "tools/lattice_backend.py doctor",
        },
    }


def readiness_matrix(native_ready: bool) -> list[dict[str, str]]:
    backend = backend_status()
    mock_backend = str(backend["backend"])
    return [
        {"capability": "canonical entity mapping", "no_credentials": "yes", "real_sandbox_required": "no"},
        {"capability": f"{mock_backend} publish/store/stream", "no_credentials": "yes", "real_sandbox_required": "no"},
        {"capability": f"{mock_backend} object/task lab seams", "no_credentials": "yes", "real_sandbox_required": "no"},
        {"capability": f"{mock_backend} movement reflected back to DIS Entity State", "no_credentials": "yes", "real_sandbox_required": "no"},
        {
            "capability": "native DIS fixture to explicit backend entity endpoint",
            "no_credentials": "yes" if native_ready else "partial",
            "real_sandbox_required": "no",
        },
        {"capability": "real Lattice sandbox transport", "no_credentials": "no", "real_sandbox_required": "yes"},
    ]


def doctor_payload() -> dict[str, object]:
    checks: list[dict[str, str]] = []
    backend = backend_status()

    def add_check(name: str, ok: bool, detail: str, *, warn: bool = False) -> None:
        checks.append(
            {
                "name": name,
                "status": "warn" if warn and not ok else ("ok" if ok else "fail"),
                "detail": detail,
            }
        )

    python_path = Path(sys.executable)
    add_check("python", python_path.is_file() and os.access(python_path, os.X_OK), sys.executable)
    add_check("src package", (ROOT / "src" / "fastdis").is_dir(), str(ROOT / "src" / "fastdis"))
    add_check("lattice backend config", Path(str(backend["config_path"])).is_file(), str(backend["config_path"]))
    add_check("backend transport", str(backend["transport"]).strip() != "", str(backend["transport"]))
    add_check("backend tag pin", bool(backend["tag_is_pinned"]) or str(backend["transport"]) == "live", str(backend["tag"]), warn=True)
    add_check("backend checkout", bool(backend["checkout_present"]) or str(backend["transport"]) == "live", str(backend["checkout_path"]), warn=True)
    add_check("backend git checkout", bool(backend["git_checkout"]) or str(backend["transport"]) == "live", str(backend["checkout_path"]), warn=True)
    add_check(
        "backend command templates",
        bool(backend["configured_commands"]),
        ", ".join(str(item) for item in backend["configured_commands"]) or "no external commands configured",
        warn=True,
    )
    add_check(
        "backend swappable contract",
        bool(backend["swappable_to_real_lattice"]),
        ", ".join(str(item) for item in backend["contract_surfaces"]) or "no contract surfaces declared",
        warn=True,
    )
    add_check(
        "backend cheat surfaces documented",
        isinstance(backend["cheat_surfaces"], list),
        str(len(backend["cheat_surfaces"])),
        warn=True,
    )
    add_check("native fastdis library", find_native_library() is not None, str(find_native_library() or "native library not found"), warn=True)
    add_check("dis fixture", DEFAULT_DIS_FIXTURE.is_file(), str(DEFAULT_DIS_FIXTURE))
    add_check("track fixture", DEFAULT_TRACK_FIXTURE.is_file(), str(DEFAULT_TRACK_FIXTURE))
    add_check("object fixture", DEFAULT_OBJECT_FIXTURE.is_file(), str(DEFAULT_OBJECT_FIXTURE))
    add_check("task fixture", DEFAULT_TASK_FIXTURE.is_file(), str(DEFAULT_TASK_FIXTURE))
    add_check("verification root", DEFAULT_OUT_ROOT.parent.exists(), str(DEFAULT_OUT_ROOT.parent), warn=True)

    hard_failures = [check for check in checks if check["status"] == "fail"]
    if hard_failures:
        status = "missing-prereqs"
    elif any(check["status"] == "warn" for check in checks):
        status = "ready-with-gaps"
    else:
        status = "ready"

    return {
        "status": status,
        "checks": checks,
        "native_ready": find_native_library() is not None,
        "backend": backend,
        "backend_cheat_surfaces": backend["cheat_surfaces"],
        "next_steps": [
            "Inspect backend contract: python tools/lattice_backend.py doctor",
            "Inspect the lane: python tools/lattice_workflow.py discover",
            "Run DIS to shim: python tools/lattice_workflow.py dis-to-shim",
            "Run shim to DIS: python tools/lattice_workflow.py shim-to-dis",
            "Exercise bounded objects/tasks: python tools/lattice_workflow.py lab-state",
            "Summarize current evidence: python tools/lattice_workflow.py report",
            "Run the release audit: python tools/lattice_workflow.py verify",
            "Run the end-to-end lane: python tools/lattice_workflow.py full",
        ],
    }


def print_doctor(payload: dict[str, object]) -> None:
    print("Lattice workflow doctor")
    print(f"status: {payload['status']}")
    backend = payload["backend"]
    print(f"backend: {backend['backend']} @ {backend['tag']}")
    print(f"backend_checkout: {backend['checkout_path']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    if payload["backend_cheat_surfaces"]:
        print("backend_cheats:")
        for cheat in payload["backend_cheat_surfaces"]:
            print(f"  - {cheat}")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List discovered Alpha 4 lattice workflow inputs")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Check the current machine and repo for Alpha 4 lattice prerequisites")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    dis_to_shim = subparsers.add_parser("dis-to-shim", help="Run canonical/DIS fixture entities into the shim lane")
    dis_to_shim.add_argument("--fixture", default=str(DEFAULT_DIS_FIXTURE))
    dis_to_shim.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT / "dis_to_shim"))

    shim_to_dis = subparsers.add_parser("shim-to-dis", help="Run shim export back into DIS Entity State replay output")
    shim_to_dis.add_argument("--fixture", default=str(DEFAULT_TRACK_FIXTURE))
    shim_to_dis.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT / "shim_to_dis"))

    lab_state = subparsers.add_parser("lab-state", help="Exercise bounded object/task seam and emit local lab-state reports")
    lab_state.add_argument("--object-fixture", default=str(DEFAULT_OBJECT_FIXTURE))
    lab_state.add_argument("--task-fixture", default=str(DEFAULT_TASK_FIXTURE))
    lab_state.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT / "lab_state"))

    report = subparsers.add_parser("report", help="Summarize Alpha 4 lattice proof artifacts into one report")
    report.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))

    verify = subparsers.add_parser("verify", help="Run the Alpha 4 release audit against generated lattice artifacts")
    verify.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))

    full = subparsers.add_parser("full", help="Doctor, then run dis-to-shim, shim-to-dis, lab-state, report, and verify")
    full.add_argument("--dis-fixture", default=str(DEFAULT_DIS_FIXTURE))
    full.add_argument("--track-fixture", default=str(DEFAULT_TRACK_FIXTURE))
    full.add_argument("--object-fixture", default=str(DEFAULT_OBJECT_FIXTURE))
    full.add_argument("--task-fixture", default=str(DEFAULT_TASK_FIXTURE))
    full.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))

    return parser.parse_args()


def command_discover(args: argparse.Namespace) -> int:
    payload = discover_payload()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] in {"ready", "ready-with-gaps"} else 2


def command_dis_to_shim(args: argparse.Namespace) -> int:
    return run_step(_external_command("dis_to_shim", fixture=str(Path(args.fixture)), out_dir=str(Path(args.out_dir))))


def command_shim_to_dis(args: argparse.Namespace) -> int:
    return run_step(_external_command("shim_to_dis", fixture=str(Path(args.fixture)), out_dir=str(Path(args.out_dir))))


def command_lab_state(args: argparse.Namespace) -> int:
    return run_step(
        _external_command(
            "lab_state",
            object_fixture=str(Path(args.object_fixture)),
            task_fixture=str(Path(args.task_fixture)),
            out_dir=str(Path(args.out_dir)),
        )
    )


def render_report_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Alpha 4 Lattice Lab Report",
        "",
        f"- overall_status: `{payload['overall_status']}`",
        f"- operator_ready: `{payload['operator_ready']}`",
        f"- native_replay_ready: `{payload['native_replay_ready']}`",
        "",
        "## Lanes",
        "",
    ]
    for lane in payload["lanes"]:
        lines.append(f"- `{lane['name']}`: `{lane['status']}`")
        lines.append(f"  artifact: `{lane['report_path']}`")
    lines.extend(["", "## Mocked Vs Real", ""])
    for item in payload["mocked_today"]:
        lines.append(f"- mocked: {item}")
    for item in payload["requires_real_sandbox"]:
        lines.append(f"- real sandbox required: {item}")
    lines.extend(["", "## Readiness Matrix", "", "| Capability | No Credentials | Real Sandbox Required |", "| --- | --- | --- |"])
    for row in payload["readiness_matrix"]:
        lines.append(f"| {row['capability']} | {row['no_credentials']} | {row['real_sandbox_required']} |")
    lines.append("")
    return "\n".join(lines)


def command_report(args: argparse.Namespace) -> int:
    out_root = Path(args.out_root).resolve()
    lanes = [
        ("dis-to-shim", out_root / "dis_to_shim" / "dis_to_shim_report.json"),
        ("shim-to-dis", out_root / "shim_to_dis" / "shim_to_dis_report.json"),
        ("lab-state", out_root / "lab_state" / "lab_state_report.json"),
    ]
    lane_payloads: list[dict[str, object]] = []
    missing = False
    for name, report_path in lanes:
        exists = report_path.is_file()
        status = "ready" if exists else "missing"
        if not exists:
            missing = True
        lane_payloads.append({"name": name, "status": status, "report_path": str(report_path)})

    doctor = doctor_payload()
    payload = {
        "overall_status": "ready" if not missing else "missing-artifacts",
        "operator_ready": not missing,
        "native_replay_ready": bool(doctor["native_ready"]),
        "backend": doctor["backend"],
        "lanes": lane_payloads,
        "mocked_today": [
            "external zorn-owned entity publish/store/stream",
            "external zorn-owned heartbeats",
            "external zorn-owned object/report storage",
            "external zorn-owned task mailbox create/status/stream",
            "FastDIS loop suppression and replay-safe DIS return-lane logic",
        ],
        "requires_real_sandbox": [
            "vendor auth/session setup",
            "real sandbox transport",
            "full inbound live Lattice stream semantics",
            "real object and task API parity",
        ],
        "readiness_matrix": readiness_matrix(bool(doctor["native_ready"])),
    }
    out_root.mkdir(parents=True, exist_ok=True)
    json_path = out_root / f"{DEFAULT_SUMMARY_BASENAME}.json"
    md_path = out_root / f"{DEFAULT_SUMMARY_BASENAME}.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_report_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["overall_status"] == "ready" else 2


def _external_command(name: str, **context: str) -> list[str]:
    config = load_lattice_backend_config()
    command_context = {
        "repo_root": str(ROOT),
        "checkout_path": str(config.checkout_path),
        "tag": config.tag,
        "python": sys.executable,
        **context,
    }
    command = config.command(name, command_context)
    if command is not None:
        return command
    raise RuntimeError(f"lattice backend contract is missing command template: {name}")


def command_verify(args: argparse.Namespace) -> int:
    return run_step(
        [
            sys.executable,
            str(DEFAULT_AUDIT_SCRIPT),
            "--out-dir",
            str(Path(args.out_root)),
        ]
    )


def command_full(args: argparse.Namespace) -> int:
    if command_doctor(argparse.Namespace(format="text")) == 2:
        return 2
    out_root = Path(args.out_root)
    dis_code = command_dis_to_shim(argparse.Namespace(fixture=args.dis_fixture, out_dir=str(out_root / "dis_to_shim")))
    if dis_code != 0:
        return dis_code
    shim_code = command_shim_to_dis(argparse.Namespace(fixture=args.track_fixture, out_dir=str(out_root / "shim_to_dis")))
    if shim_code != 0:
        return shim_code
    lab_code = command_lab_state(
        argparse.Namespace(
            object_fixture=args.object_fixture,
            task_fixture=args.task_fixture,
            out_dir=str(out_root / "lab_state"),
        )
    )
    if lab_code != 0:
        return lab_code
    report_code = command_report(argparse.Namespace(out_root=str(out_root)))
    if report_code != 0:
        return report_code
    return command_verify(argparse.Namespace(out_root=str(out_root)))


def main() -> int:
    load_local_env.load()
    args = parse_args()
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "dis-to-shim":
        return command_dis_to_shim(args)
    if args.command == "shim-to-dis":
        return command_shim_to_dis(args)
    if args.command == "lab-state":
        return command_lab_state(args)
    if args.command == "report":
        return command_report(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
