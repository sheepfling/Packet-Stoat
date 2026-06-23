from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import generate_lattice_dis_mapping_plan as mapping_plan


def test_lattice_dis_mapping_plan_covers_all_141_rows() -> None:
    plan = mapping_plan.build_plan()

    assert plan["summary"]["records"] == 141
    assert len(plan["records"]) == 141
    assert all(row["strict_lattice_bucket"] in {"Entity", "Task", "Object"} for row in plan["records"])
    assert all(row["lattice_subtype"] for row in plan["records"])
    assert all(row["ingress_mapping"] for row in plan["records"])
    assert all(row["egress_mapping"] for row in plan["records"])
    assert all(row["loss_policy"] for row in plan["records"])
    assert all(row["rest_surface_kinds"] for row in plan["records"])
    assert all(row["grpc_surface_kind"] for row in plan["records"])
    assert all(row["egress_conformance"] for row in plan["records"])


def test_lattice_dis_mapping_plan_has_core_strict_buckets_and_targets() -> None:
    plan = mapping_plan.build_plan()
    buckets = plan["summary"]["strict_lattice_buckets"]
    subtypes = plan["summary"]["lattice_subtypes"]
    targets = plan["summary"]["observation_reduction_targets"]
    loss_policies = plan["summary"]["loss_policies"]

    assert buckets == {"Entity": 42, "Object": 21, "Task": 78}
    assert subtypes["Entity"] == 2
    assert subtypes["ObjectArtifact"] == 2
    assert subtypes["TaskOrControlEvent"] >= 20
    assert subtypes["SimulationEvent"] >= 10
    assert targets == []
    assert loss_policies["preserve_raw_required_for_lossless_egress"] == 72
    assert "lossy_without_raw" not in loss_policies


def test_lattice_dis_mapping_plan_validates_bucket_conformance() -> None:
    plan = mapping_plan.build_plan()
    issues = mapping_plan.validate_plan(plan)
    conformance = plan["summary"]["bucket_conformance"]

    assert issues == []
    assert conformance["Entity"]["rows"] == 42
    assert conformance["Task"]["rows"] == 78
    assert conformance["Object"]["rows"] == 21
    assert conformance["Entity"]["grpc_surface_kind_counts"] == {"entities": 16, "generic": 26}
    assert conformance["Task"]["grpc_surface_kind_counts"] == {"generic": 28, "tasks": 50}
    assert conformance["Object"]["grpc_surface_kind_counts"] == {"generic": 21}


def test_lattice_dis_mapping_outputs_are_current() -> None:
    plan = mapping_plan.build_plan()
    expected_json = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    expected_md = mapping_plan.render_markdown(plan)

    assert mapping_plan.JSON_OUT.read_text(encoding="utf-8") == expected_json
    assert mapping_plan.MD_OUT.read_text(encoding="utf-8") == expected_md
