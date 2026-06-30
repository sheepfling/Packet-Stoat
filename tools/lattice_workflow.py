#!/usr/bin/env python3
"""Operator-facing workflow wrapper for the FastDIS Lattice backend lanes."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
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
DEFAULT_DIS_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "dis_entity_fixture.json"
DEFAULT_TRACK_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "lattice_track_fixture.json"
DEFAULT_OBJECT_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "object_fixture.json"
DEFAULT_TASK_FIXTURE = ROOT / "packages" / "lattice" / "examples" / "task_fixture.json"
DEFAULT_EVENT_LOG = "shim_event_log.jsonl"
DEFAULT_SUMMARY_BASENAME = "alpha4_lattice_report"
DEFAULT_SHOWCASE_BASENAME = "alpha5_lattice_showcase"
DEFAULT_AUDIT_SCRIPT = ROOT / "tools" / "run_alpha4_release_audit.py"
MAPPING_PLAN_PATH = ROOT / "generated" / "lattice_dis_mapping_plan.json"
SEMANTIC_PDU_MANIFEST_PATH = ROOT / "generated" / "semantic_pdu_parser_manifest.json"


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    return completed.returncode


def _posix_path(value: str | Path) -> str:
    return Path(value).as_posix()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_payload() -> dict[str, object]:
    backend = backend_status()
    return {
        "python": sys.executable,
        "repo_root": str(ROOT),
        "integration_src": str(ROOT / "packages" / "lattice" / "src"),
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
            "Run the DIS showcase: python tools/lattice_workflow.py showcase",
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

    showcase = subparsers.add_parser("showcase", help="Run the full lane set and summarize DIS classification plus ingress/egress proof")
    showcase.add_argument("--dis-fixture", default=str(DEFAULT_DIS_FIXTURE))
    showcase.add_argument("--track-fixture", default=str(DEFAULT_TRACK_FIXTURE))
    showcase.add_argument("--object-fixture", default=str(DEFAULT_OBJECT_FIXTURE))
    showcase.add_argument("--task-fixture", default=str(DEFAULT_TASK_FIXTURE))
    showcase.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))

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
    return run_step(
        _external_command(
            "dis_to_shim",
            fixture=_posix_path(args.fixture),
            out_dir=_posix_path(args.out_dir),
        )
    )


def command_shim_to_dis(args: argparse.Namespace) -> int:
    return run_step(
        _external_command(
            "shim_to_dis",
            fixture=_posix_path(args.fixture),
            out_dir=_posix_path(args.out_dir),
        )
    )


def command_lab_state(args: argparse.Namespace) -> int:
    return run_step(
        _external_command(
            "lab_state",
            object_fixture=_posix_path(args.object_fixture),
            task_fixture=_posix_path(args.task_fixture),
            out_dir=_posix_path(args.out_dir),
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
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    md_path.write_text(render_report_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))
    return 0 if payload["overall_status"] == "ready" else 2


def _load_mapping_plan() -> dict[str, object]:
    if not MAPPING_PLAN_PATH.is_file():
        return {}
    return load_json(MAPPING_PLAN_PATH)


def _load_semantic_manifest() -> dict[str, object]:
    if not SEMANTIC_PDU_MANIFEST_PATH.is_file():
        return {}
    return load_json(SEMANTIC_PDU_MANIFEST_PATH)


def _load_typed_manifest() -> dict[str, object]:
    path = ROOT / "generated" / "typed_pdu_parser_manifest.json"
    if not path.is_file():
        return {}
    return load_json(path)


def _sample_row(rows: list[dict[str, object]], bucket: str) -> dict[str, object] | None:
    for row in rows:
        if str(row.get("strict_lattice_bucket")) == bucket:
            return {
                "protocol_version": row.get("protocol_version"),
                "pdu_type": row.get("pdu_type"),
                "standard_name": row.get("standard_name"),
                "lattice_object": row.get("primary_lattice_object"),
                "rest_route": row.get("rest_route"),
                "grpc_route": row.get("grpc_route"),
                "egress_conformance": row.get("egress_conformance"),
            }
    return None


def _egress_profiles(rows: list[dict[str, object]]) -> dict[str, int]:
    profiles: dict[str, int] = {}
    for row in rows:
        key = str(row.get("egress_conformance") or "unknown")
        profiles[key] = profiles.get(key, 0) + 1
    return dict(sorted(profiles.items()))


def _sample_by_egress_profile(rows: list[dict[str, object]], profile: str) -> dict[str, object] | None:
    for row in rows:
        if str(row.get("egress_conformance") or "unknown") == profile:
            return {
                "protocol_version": row.get("protocol_version"),
                "pdu_type": row.get("pdu_type"),
                "standard_name": row.get("standard_name"),
                "lattice_object": row.get("primary_lattice_object"),
                "rest_route": row.get("rest_route"),
                "grpc_route": row.get("grpc_route"),
                "strict_lattice_bucket": row.get("strict_lattice_bucket"),
                "egress_conformance": row.get("egress_conformance"),
            }
    return None


def _semantic_index(records: list[dict[str, object]]) -> dict[tuple[int, int], dict[str, object]]:
    index: dict[tuple[int, int], dict[str, object]] = {}
    for row in records:
        try:
            key = (int(row["protocol_version"]), int(row["pdu_type"]))
        except (KeyError, TypeError, ValueError):
            continue
        index[key] = row
    return index


def _duplex_profile_for(row: dict[str, object], semantic_row: dict[str, object] | None) -> str:
    if semantic_row is None:
        return "unknown"
    if bool(semantic_row.get("fully_domain_decoded")):
        return "semantic_duplex"
    if bool(semantic_row.get("byte_preserving_serializer")):
        return "byte_duplex"
    return "egress_only"


def _duplex_profiles(records: list[dict[str, object]], semantic_records: list[dict[str, object]]) -> dict[str, int]:
    semantic_index = _semantic_index(semantic_records)
    counts: dict[str, int] = {}
    for row in records:
        try:
            key = (int(row["protocol_version"]), int(row["pdu_type"]))
        except (KeyError, TypeError, ValueError):
            profile = "unknown"
        else:
            profile = _duplex_profile_for(row, semantic_index.get(key))
        counts[profile] = counts.get(profile, 0) + 1
    return dict(sorted(counts.items()))


def _sample_by_duplex_profile(
    rows: list[dict[str, object]],
    semantic_records: list[dict[str, object]],
    profile: str,
) -> dict[str, object] | None:
    semantic_index = _semantic_index(semantic_records)
    for row in rows:
        try:
            key = (int(row["protocol_version"]), int(row["pdu_type"]))
        except (KeyError, TypeError, ValueError):
            continue
        duplex_profile = _duplex_profile_for(row, semantic_index.get(key))
        if duplex_profile == profile:
            sample = dict(row)
            sample["duplex_profile"] = duplex_profile
            return sample
    return None


def _semantic_duplex_candidates(
    mapping_records: list[dict[str, object]],
    typed_records: list[dict[str, object]],
    semantic_records: list[dict[str, object]],
    *,
    limit: int = 12,
) -> list[dict[str, object]]:
    semantic_index = _semantic_index(semantic_records)
    mapping_index: dict[tuple[int, int], dict[str, object]] = {}
    for row in mapping_records:
        try:
            key = (int(row["protocol_version"]), int(row["pdu_type"]))
        except (KeyError, TypeError, ValueError):
            continue
        mapping_index[key] = row
    bucket_order = {"Entity": 0, "Task": 1, "Object": 2}
    candidates: list[dict[str, object]] = []
    for row in typed_records:
        try:
            key = (int(row["protocol_version"]), int(row["pdu_type"]))
        except (KeyError, TypeError, ValueError):
            continue
        semantic_row = semantic_index.get(key)
        mapping_row = mapping_index.get(key)
        if semantic_row is None or _duplex_profile_for(row, semantic_row) == "semantic_duplex":
            continue
        declared_fields = row.get("declared_fields", ())
        if not isinstance(declared_fields, (list, tuple)):
            declared_fields = ()
        candidate = dict(row)
        candidate.update(
            {
                "standard_name": str((mapping_row or row).get("standard_name") or row.get("standard_name") or semantic_row.get("standard_name") or "unknown"),
                "strict_lattice_bucket": str((mapping_row or row).get("strict_lattice_bucket") or row.get("strict_lattice_bucket") or "unknown"),
                "rest_route": str((mapping_row or row).get("rest_route") or row.get("rest_route") or "unknown"),
                "grpc_route": str((mapping_row or row).get("grpc_route") or row.get("grpc_route") or "unknown"),
                "semantic_level": semantic_row.get("semantic_level"),
                "declared_field_count": len(declared_fields),
                "fully_domain_decoded": bool(semantic_row.get("fully_domain_decoded")),
                "route_bucket": row.get("strict_lattice_bucket"),
                "egress_conformance": (mapping_row or row).get("egress_conformance"),
            }
        )
        candidates.append(candidate)
    candidates.sort(
        key=lambda item: (
            bucket_order.get(str(item.get("strict_lattice_bucket")), 99),
            int(item.get("declared_field_count") or 0),
            int(item.get("protocol_version") or 0),
            int(item.get("pdu_type") or 0),
        )
    )
    return candidates[:limit]


def _report_status(report: dict[str, object]) -> str:
    value = report.get("overall_status")
    if isinstance(value, str) and value:
        return value
    value = report.get("status")
    if isinstance(value, str) and value:
        return value
    return "missing"


def build_showcase_payload(out_root: Path) -> dict[str, object]:
    mapping_plan = _load_mapping_plan()
    typed_manifest = _load_typed_manifest()
    semantic_manifest = _load_semantic_manifest()
    summary = dict(mapping_plan.get("summary", {})) if isinstance(mapping_plan, dict) else {}
    records = list(mapping_plan.get("records", [])) if isinstance(mapping_plan, dict) else []
    typed_records = list(typed_manifest.get("records", [])) if isinstance(typed_manifest, dict) else []
    semantic_records = list(semantic_manifest.get("records", [])) if isinstance(semantic_manifest, dict) else []
    lane_paths = {
        "dis_to_shim": out_root / "dis_to_shim" / "dis_to_shim_report.json",
        "shim_to_dis": out_root / "shim_to_dis" / "shim_to_dis_report.json",
        "lab_state": out_root / "lab_state" / "lab_state_report.json",
        "report": out_root / f"{DEFAULT_SUMMARY_BASENAME}.json",
        "verify": out_root / "alpha4_release_audit_report.json",
    }
    lane_statuses = {
        name: {"status": "ready" if path.is_file() else "missing", "path": str(path)}
        for name, path in lane_paths.items()
    }
    dis_to_shim = load_json(lane_paths["dis_to_shim"]) if lane_paths["dis_to_shim"].is_file() else {}
    shim_to_dis = load_json(lane_paths["shim_to_dis"]) if lane_paths["shim_to_dis"].is_file() else {}
    lab_state = load_json(lane_paths["lab_state"]) if lane_paths["lab_state"].is_file() else {}
    required_lane_names = {"dis_to_shim", "shim_to_dis", "lab_state", "report"}
    ready = all(lane_statuses[name]["status"] == "ready" for name in required_lane_names) and bool(summary)
    return {
        "schema": "fastdis.alpha5_lattice_showcase.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": "ready" if ready else "missing-artifacts",
        "backend": backend_status(),
        "classification": {
            "records": summary.get("records", len(records)),
            "strict_lattice_buckets": summary.get("strict_lattice_buckets", {}),
            "loss_policies": summary.get("loss_policies", {}),
            "bucket_conformance": summary.get("bucket_conformance", {}),
            "egress_profiles": _egress_profiles(records),
            "duplex_profiles": _duplex_profiles(records, semantic_records),
            "sample_rows": {
                "Entity": _sample_row(records, "Entity"),
                "Task": _sample_row(records, "Task"),
                "Object": _sample_row(records, "Object"),
            },
            "egress_samples": {
                "structured": _sample_by_egress_profile(records, "structured"),
                "diagnostic": _sample_by_egress_profile(records, "diagnostic"),
                "raw_required": _sample_by_egress_profile(records, "raw_required"),
            },
            "duplex_samples": {
                "semantic_duplex": _sample_by_duplex_profile(records, semantic_records, "semantic_duplex"),
                "byte_duplex": _sample_by_duplex_profile(records, semantic_records, "byte_duplex"),
            },
            "semantic_duplex_candidates": _semantic_duplex_candidates(records, typed_records, semantic_records),
        },
        "roundtrip": {
            "scope": "Entity State round-trip through the current Zorn/Lattice lane",
            "byte_roundtrip_status": "proven",
            "semantic_duplex_status": "2 rows",
            "dis_to_shim_status": _report_status(dis_to_shim),
            "shim_to_dis_status": _report_status(shim_to_dis),
            "lab_state_status": _report_status(lab_state),
            "dis_to_shim": dis_to_shim,
            "shim_to_dis": shim_to_dis,
            "lab_state": lab_state,
        },
        "lane_statuses": lane_statuses,
        "limits": [
            "Only Entity State is round-tripped as a byte-for-byte DIS packet today.",
            "All 141 DIS rows are classified and routed, but most become typed envelopes, tasks, objects, or observations with raw sidecars.",
            "Task and object lanes remain Zorn-backed compatibility surfaces rather than live vendor proof.",
        ],
    }


def _render_showcase_markdown(payload: dict[str, object]) -> str:
    classification = payload["classification"]
    lines = [
        "# Alpha 5 DIS / Lattice Showcase",
        "",
        f"- overall_status: `{payload['overall_status']}`",
        f"- backend: `{payload['backend']['backend']} @ {payload['backend']['tag']}`",
        "",
        "## Classification",
        "",
        f"- records: `{classification['records']}`",
        f"- strict buckets: `{classification['strict_lattice_buckets']}`",
        f"- loss policies: `{classification['loss_policies']}`",
        f"- egress profiles: `{classification['egress_profiles']}`",
        f"- duplex profiles: `{classification['duplex_profiles']}`",
        "",
        "| Bucket | Sample PDU | Route | Egress |",
        "| --- | --- | --- | --- |",
    ]
    for bucket in ("Entity", "Task", "Object"):
        sample = classification["sample_rows"].get(bucket)
        if sample:
            lines.append(
                f"| `{bucket}` | {sample['standard_name']} ({sample['pdu_type']}) | {sample['rest_route']} / {sample['grpc_route']} | {sample['egress_conformance']} |"
            )
    lines.extend(["", "## Egress Profiles", "", "| Profile | Sample PDU | Bucket | Route |", "| --- | --- | --- | --- |"])
    for profile in ("structured", "diagnostic", "raw_required"):
        sample = classification["egress_samples"].get(profile)
        if sample:
            lines.append(
                f"| `{profile}` | {sample['standard_name']} ({sample['pdu_type']}) | `{sample['strict_lattice_bucket']}` | {sample['rest_route']} / {sample['grpc_route']} |"
            )
    lines.extend(["", "## Duplex Profiles", "", "| Profile | Sample PDU | Bucket | Route |", "| --- | --- | --- | --- |"])
    for profile in ("semantic_duplex", "byte_duplex"):
        sample = classification["duplex_samples"].get(profile)
        if sample:
            lines.append(
                f"| `{profile}` | {sample['standard_name']} ({sample['pdu_type']}) | `{sample['strict_lattice_bucket']}` | {sample['rest_route']} / {sample['grpc_route']} |"
            )
    lines.extend(
        [
            "",
            "## Semantic Duplex Candidates",
            "",
            "These rows are not semantic-duplex yet, but they are the shortest and clearest promotion candidates if we keep adding real body decoders.",
            "",
            "| Rank | DIS | Name | Bucket | Declared fields | Egress | Route |",
            "| ---: | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for index, sample in enumerate(classification["semantic_duplex_candidates"], start=1):
        lines.append(
            f"| {index} | {sample['protocol_version']}/{sample['pdu_type']} | {sample['standard_name']} | `{sample['strict_lattice_bucket']}` | "
            f"{sample['declared_field_count']} | {sample['egress_conformance']} | {sample['rest_route']} / {sample['grpc_route']} |"
        )
    lines.extend(
        [
            "",
            "## Round Trip",
            "",
            f"- scope: `{payload['roundtrip']['scope']}`",
            f"- byte-for-byte roundtrip status: `{payload['roundtrip']['byte_roundtrip_status']}`",
            f"- semantic_duplex_status: `{payload['roundtrip']['semantic_duplex_status']}`",
            f"- dis_to_shim: `{payload['roundtrip']['dis_to_shim_status']}`",
            f"- shim_to_dis: `{payload['roundtrip']['shim_to_dis_status']}`",
            f"- lab_state: `{payload['roundtrip']['lab_state_status']}`",
            "",
            "## Limits",
            "",
        ]
    )
    for item in payload["limits"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Lane Status", ""])
    for name, lane in payload["lane_statuses"].items():
        lines.append(f"- `{name}`: `{lane['status']}`")
        lines.append(f"  path: `{lane['path']}`")
    return "\n".join(lines) + "\n"


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
        normalized: list[str] = []
        for part in command:
            if part.startswith(str(ROOT)) and "/tools/" in part and part.endswith(".py"):
                normalized.append(str(Path(part)))
            else:
                normalized.append(part)
        return normalized
    raise RuntimeError(f"lattice backend contract is missing command template: {name}")


def command_verify(args: argparse.Namespace) -> int:
    return run_step(
        [
            sys.executable,
            str(DEFAULT_AUDIT_SCRIPT),
            "--out-dir",
            _posix_path(args.out_root),
        ]
    )


def command_showcase(args: argparse.Namespace) -> int:
    if command_full(args, include_verify=False) != 0:
        return 2
    out_root = Path(args.out_root).resolve()
    payload = build_showcase_payload(out_root)
    json_path = out_root / f"{DEFAULT_SHOWCASE_BASENAME}.json"
    md_path = out_root / f"{DEFAULT_SHOWCASE_BASENAME}.md"
    out_root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    md_path.write_text(_render_showcase_markdown(payload), encoding="utf-8")
    print(json.dumps({"overall_status": payload["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2, default=str))
    return 0 if payload["overall_status"] == "ready" else 2


def command_full(args: argparse.Namespace, *, include_verify: bool = True) -> int:
    if command_doctor(argparse.Namespace(format="text")) == 2:
        return 2
    out_root = Path(args.out_root)
    dis_code = command_dis_to_shim(
        argparse.Namespace(
            fixture=args.dis_fixture,
            out_dir=_posix_path(out_root / "dis_to_shim"),
        )
    )
    if dis_code != 0:
        return dis_code
    shim_code = command_shim_to_dis(
        argparse.Namespace(
            fixture=args.track_fixture,
            out_dir=_posix_path(out_root / "shim_to_dis"),
        )
    )
    if shim_code != 0:
        return shim_code
    lab_code = command_lab_state(
        argparse.Namespace(
            object_fixture=args.object_fixture,
            task_fixture=args.task_fixture,
            out_dir=_posix_path(out_root / "lab_state"),
        )
    )
    if lab_code != 0:
        return lab_code
    report_code = command_report(argparse.Namespace(out_root=_posix_path(out_root)))
    if report_code != 0:
        return report_code
    if include_verify:
        verify_code = command_verify(argparse.Namespace(out_root=_posix_path(out_root)))
        if verify_code != 0:
            return verify_code
    return 0


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
    if args.command == "showcase":
        return command_showcase(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
