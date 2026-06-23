from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import lattice_workflow


def _expected_external_command(*args: str) -> list[str]:
    return [
        sys.executable,
        str(lattice_workflow.ROOT / "tools" / "lattice_zorn_bridge.py"),
        *args,
    ]


def test_doctor_payload_detects_expected_artifacts() -> None:
    payload = lattice_workflow.doctor_payload()

    assert payload["status"] in {"ready", "ready-with-gaps"}
    assert any(check["name"] == "native fastdis library" for check in payload["checks"])
    assert any(check["name"] == "lattice backend config" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "dis fixture" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "track fixture" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "object fixture" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "task fixture" and check["status"] == "ok" for check in payload["checks"])


def test_dis_to_shim_command_forwards_args() -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = lattice_workflow.run_step
    lattice_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(fixture="fixture.json", out_dir="out/dis")
        assert lattice_workflow.command_dis_to_shim(args) == 0
    finally:
        lattice_workflow.run_step = original

    assert recorded == [_expected_external_command("dis-to-shim", "--fixture", "fixture.json", "--out-dir", "out/dis")]


def test_shim_to_dis_command_forwards_args() -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = lattice_workflow.run_step
    lattice_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(fixture="track.json", out_dir="out/replay")
        assert lattice_workflow.command_shim_to_dis(args) == 0
    finally:
        lattice_workflow.run_step = original

    assert recorded == [_expected_external_command("shim-to-dis", "--fixture", "track.json", "--out-dir", "out/replay")]


def test_full_command_runs_both_lanes() -> None:
    steps: list[str] = []

    def fake_doctor(_args: argparse.Namespace) -> int:
        steps.append("doctor")
        return 0

    def fake_dis(args: argparse.Namespace) -> int:
        steps.append(f"dis:{args.fixture}:{args.out_dir}")
        return 0

    def fake_shim(args: argparse.Namespace) -> int:
        steps.append(f"shim:{args.fixture}:{args.out_dir}")
        return 0

    def fake_lab(args: argparse.Namespace) -> int:
        steps.append(f"lab:{args.object_fixture}:{args.task_fixture}:{args.out_dir}")
        return 0

    def fake_report(args: argparse.Namespace) -> int:
        steps.append(f"report:{args.out_root}")
        return 0

    def fake_verify(args: argparse.Namespace) -> int:
        steps.append(f"verify:{args.out_root}")
        return 0

    original_doctor = lattice_workflow.command_doctor
    original_dis = lattice_workflow.command_dis_to_shim
    original_shim = lattice_workflow.command_shim_to_dis
    original_lab = lattice_workflow.command_lab_state
    original_report = lattice_workflow.command_report
    original_verify = lattice_workflow.command_verify
    lattice_workflow.command_doctor = fake_doctor
    lattice_workflow.command_dis_to_shim = fake_dis
    lattice_workflow.command_shim_to_dis = fake_shim
    lattice_workflow.command_lab_state = fake_lab
    lattice_workflow.command_report = fake_report
    lattice_workflow.command_verify = fake_verify
    try:
        args = argparse.Namespace(
            dis_fixture="a.json",
            track_fixture="b.json",
            object_fixture="objects.json",
            task_fixture="tasks.json",
            out_root="reports/lattice",
        )
        assert lattice_workflow.command_full(args) == 0
    finally:
        lattice_workflow.command_doctor = original_doctor
        lattice_workflow.command_dis_to_shim = original_dis
        lattice_workflow.command_shim_to_dis = original_shim
        lattice_workflow.command_lab_state = original_lab
        lattice_workflow.command_report = original_report
        lattice_workflow.command_verify = original_verify

    assert steps == [
        "doctor",
        "dis:a.json:reports/lattice/dis_to_shim",
        "shim:b.json:reports/lattice/shim_to_dis",
        "lab:objects.json:tasks.json:reports/lattice/lab_state",
        "report:reports/lattice",
        "verify:reports/lattice",
    ]


def test_showcase_command_runs_full_and_writes_summary(tmp_path: Path) -> None:
    out_root = tmp_path / "alpha5" / "lattice"
    steps: list[str] = []

    def fake_full(args: argparse.Namespace, *, include_verify: bool = True) -> int:
        steps.append(f"full:{args.out_root}:{include_verify}")
        for rel in (
            "dis_to_shim/dis_to_shim_report.json",
            "shim_to_dis/shim_to_dis_report.json",
            "lab_state/lab_state_report.json",
            "alpha4_lattice_report.json",
        ):
            path = Path(args.out_root) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
        return 0

    original_full = lattice_workflow.command_full
    lattice_workflow.command_full = fake_full
    try:
        args = argparse.Namespace(
            dis_fixture="a.json",
            track_fixture="b.json",
            object_fixture="objects.json",
            task_fixture="tasks.json",
            out_root=str(out_root),
        )
        assert lattice_workflow.command_showcase(args) == 0
    finally:
        lattice_workflow.command_full = original_full

    assert steps == [f"full:{out_root}:False"]
    assert (out_root / "alpha5_lattice_showcase.json").is_file()
    assert (out_root / "alpha5_lattice_showcase.md").is_file()


def test_build_showcase_payload_classifies_egress_profiles(tmp_path: Path) -> None:
    out_root = tmp_path / "alpha5" / "lattice"
    for rel in (
        "dis_to_shim/dis_to_shim_report.json",
        "shim_to_dis/shim_to_dis_report.json",
        "lab_state/lab_state_report.json",
        "alpha4_lattice_report.json",
    ):
        path = out_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"overall_status":"ready"}', encoding="utf-8")

    mapping_plan = {
        "summary": {
            "records": 3,
            "strict_lattice_buckets": {"Entity": 1, "Task": 1, "Object": 1},
            "loss_policies": {"structured": 1, "diagnostic": 1, "raw_required": 1},
            "bucket_conformance": {},
        },
        "records": [
            {
                "protocol_version": 7,
                "pdu_type": 1,
                "standard_name": "Entity State",
                "primary_lattice_object": "Entity",
                "rest_route": "PUT /api/v1/entities",
                "grpc_route": "EntityManagerAPI.PublishEntity/GetEntity/StreamEntityComponents",
                "strict_lattice_bucket": "Entity",
                "egress_conformance": "structured",
            },
            {
                "protocol_version": 7,
                "pdu_type": 2,
                "standard_name": "Fire",
                "primary_lattice_object": "SimulationEvent",
                "rest_route": "POST /api/v1/objects",
                "grpc_route": "generic observation/event stream",
                "strict_lattice_bucket": "Task",
                "egress_conformance": "diagnostic",
            },
            {
                "protocol_version": 7,
                "pdu_type": 70,
                "standard_name": "Information Operations Action",
                "primary_lattice_object": "ObjectArtifact",
                "rest_route": "POST /api/v1/objects",
                "grpc_route": "artifact-correlated generic notification only",
                "strict_lattice_bucket": "Object",
                "egress_conformance": "raw_required",
            },
        ],
    }
    semantic_manifest = {
        "records": [
            {
                "protocol_version": 7,
                "pdu_type": 1,
                "fully_domain_decoded": True,
                "byte_preserving_serializer": True,
            },
            {
                "protocol_version": 7,
                "pdu_type": 2,
                "fully_domain_decoded": False,
                "byte_preserving_serializer": True,
            },
            {
                "protocol_version": 7,
                "pdu_type": 70,
                "fully_domain_decoded": False,
                "byte_preserving_serializer": True,
            },
        ]
    }
    typed_manifest = {
        "records": [
            {
                "protocol_version": 7,
                "pdu_type": 1,
                "strict_lattice_bucket": "Entity",
                "declared_fields": ["entityID", "forceID"],
                "egress_conformance": "structured",
            },
            {
                "protocol_version": 7,
                "pdu_type": 2,
                "strict_lattice_bucket": "Task",
                "declared_fields": ["firingEntityID", "targetEntityID"],
                "egress_conformance": "raw_required",
            },
            {
                "protocol_version": 7,
                "pdu_type": 70,
                "strict_lattice_bucket": "Object",
                "declared_fields": ["observationID"],
                "egress_conformance": "raw_required",
            },
        ]
    }

    original_loader = lattice_workflow._load_mapping_plan
    original_typed_loader = lattice_workflow._load_typed_manifest
    original_semantic_loader = lattice_workflow._load_semantic_manifest
    lattice_workflow._load_mapping_plan = lambda: mapping_plan
    lattice_workflow._load_typed_manifest = lambda: typed_manifest
    lattice_workflow._load_semantic_manifest = lambda: semantic_manifest
    try:
        payload = lattice_workflow.build_showcase_payload(out_root)
    finally:
        lattice_workflow._load_mapping_plan = original_loader
        lattice_workflow._load_typed_manifest = original_typed_loader
        lattice_workflow._load_semantic_manifest = original_semantic_loader

    assert payload["overall_status"] == "ready"
    assert payload["classification"]["egress_profiles"] == {
        "diagnostic": 1,
        "raw_required": 1,
        "structured": 1,
    }
    assert payload["classification"]["duplex_profiles"] == {
        "byte_duplex": 2,
        "semantic_duplex": 1,
    }
    assert [item["standard_name"] for item in payload["classification"]["semantic_duplex_candidates"]] == [
        "Fire",
        "Information Operations Action",
    ]
    assert payload["roundtrip"]["byte_roundtrip_status"] == "proven"
    assert payload["roundtrip"]["semantic_duplex_status"] == "2 rows"
    assert payload["roundtrip"]["dis_to_shim_status"] == "ready"
    assert payload["roundtrip"]["shim_to_dis_status"] == "ready"
    assert payload["roundtrip"]["lab_state_status"] == "ready"


def test_lab_state_command_forwards_args() -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = lattice_workflow.run_step
    lattice_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(object_fixture="objects.json", task_fixture="tasks.json", out_dir="out/lab")
        assert lattice_workflow.command_lab_state(args) == 0
    finally:
        lattice_workflow.run_step = original

    assert recorded == [
        _expected_external_command(
            "lab-state",
            "--object-fixture",
            "objects.json",
            "--task-fixture",
            "tasks.json",
            "--out-dir",
            "out/lab",
        )
    ]


def test_report_command_writes_summary(tmp_path: Path) -> None:
    out_root = tmp_path / "alpha4" / "lattice"
    (out_root / "dis_to_shim").mkdir(parents=True)
    (out_root / "shim_to_dis").mkdir(parents=True)
    (out_root / "lab_state").mkdir(parents=True)
    for rel in (
        "dis_to_shim/dis_to_shim_report.json",
        "shim_to_dis/shim_to_dis_report.json",
        "lab_state/lab_state_report.json",
    ):
        path = out_root / rel
        path.write_text("{}", encoding="utf-8")

    rc = lattice_workflow.command_report(argparse.Namespace(out_root=str(out_root)))

    assert rc == 0
    assert (out_root / "alpha4_lattice_report.json").is_file()
    assert (out_root / "alpha4_lattice_report.md").is_file()


def test_verify_command_forwards_out_root() -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = lattice_workflow.run_step
    lattice_workflow.run_step = fake_run_step
    try:
        args = argparse.Namespace(out_root="reports/lattice")
        assert lattice_workflow.command_verify(args) == 0
    finally:
        lattice_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        str(lattice_workflow.DEFAULT_AUDIT_SCRIPT),
        "--out-dir",
        "reports/lattice",
    ]]
