from __future__ import annotations

import importlib.util
import json
import platform
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unity_runtime_sample_fixtures_are_stable() -> None:
    runtime = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_runtime_verification.sample.json").read_text(encoding="utf-8"))
    workflow = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_workflow_report.sample.json").read_text(encoding="utf-8"))
    equivalence = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_cross_engine_equivalence.sample.json").read_text(encoding="utf-8"))

    assert runtime["overall_status"] == "pass"
    assert runtime["lanes"][0]["tests"]["passed"] == 35
    assert workflow["unity_workflow_status"] == "pass"
    assert equivalence["status"] == "complete"


def test_normalize_unity_runtime_verification_builds_shared_report(tmp_path: Path) -> None:
    module = _load_module("normalize_unity_runtime_verification", ROOT / "tools" / "normalize_unity_runtime_verification.py")
    runtime = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_runtime_verification.sample.json").read_text(encoding="utf-8"))
    workflow = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_workflow_report.sample.json").read_text(encoding="utf-8"))
    equivalence = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_cross_engine_equivalence.sample.json").read_text(encoding="utf-8"))
    install_smoke = {"status": "pass", "elapsed_seconds": 9.111, "checks": [{"name": "native_abi_loads", "status": "pass"}]}

    normalized = module.normalize_payload(
        runtime,
        workflow_payload=workflow,
        equivalence_payload=equivalence,
        install_smoke_payload=install_smoke,
        replay_matrix_payload=None,
        scenario="unity_runtime_verification",
        source_payload="artifacts/reports/unity_runtime_verification.json",
    )

    assert normalized["schema"] == "fastdis.engine_benchmark_report.v1"
    assert normalized["surface"] == "unity"
    assert normalized["surface_kind"] == "engine"
    assert normalized["rows"][0]["scenario"] == "unity_runtime_verification"
    assert normalized["rows"][1]["scenario"] == "entity_state_1x10hz"
    assert normalized["rows"][2]["scenario"] == "unity_replay_latest_state_apply"
    assert normalized["rows"][3]["scenario"] == "unity_install_smoke_runtime"
    assert normalized["rows"][0]["metrics"]["packets_received"] is None
    assert normalized["rows"][1]["metrics"]["packets_received"] == 10
    assert normalized["rows"][1]["metrics"]["packets_parsed"] == 10
    assert normalized["rows"][1]["metrics"]["packets_accepted"] == 10
    assert normalized["rows"][1]["metrics"]["main_thread_apply_ms"] == 0.42
    assert normalized["rows"][1]["metrics"]["packets_per_sec"] == 2380.95
    assert normalized["rows"][1]["metrics"]["steady_state_gc_bytes"] == 96
    assert normalized["rows"][0]["truth"]["final_truth_match"] is True
    assert normalized["rows"][1]["truth"]["canonical_alias_of"] == "unity_runtime_verification"
    assert normalized["rows"][1]["truth"]["benchmark_source"] == "unity_editor_method_verification"
    assert normalized["rows"][1]["truth"]["source_truth_schema"] == "fastdis.unity_editor_method_verification.v1"
    assert normalized["rows"][1]["truth"]["source_truth_file"] == "artifacts/reports/unity_runtime_verification.json"
    assert normalized["rows"][1]["truth"]["final_truth_match"] is True
    assert normalized["rows"][1]["truth"]["suite_overall_status"] == "pass"
    assert normalized["rows"][1]["truth"]["scenario_truth_basis"] == [
        "Native library stages and loads in Unity",
        "UDP demo receives live Entity State traffic",
        "Entity mapper applies transforms to spawned GameObjects",
    ]
    assert [row["name"] for row in normalized["rows"][1]["truth"]["benchmark_required_criteria"]] == [
        "Native library stages and loads in Unity",
        "UDP demo receives live Entity State traffic",
        "Entity mapper applies transforms to spawned GameObjects",
    ]
    assert normalized["rows"][1]["truth"]["benchmark_required_checks"] == []
    assert normalized["rows"][1]["truth"]["failed_checks_outside_benchmark_scope"] == []
    assert normalized["rows"][2]["truth"]["final_truth_match"] is True
    assert normalized["rows"][2]["truth"]["phase1_requirement_status"] == "complete"
    assert normalized["rows"][3]["metrics"]["runtime_elapsed_seconds"] == 9.111
    assert normalized["rows"][0]["truth"]["runtime_overall_status"] == "pass"
    assert normalized["rows"][0]["truth"]["workflow_status"] == "pass"
    assert normalized["rows"][0]["truth"]["cross_engine_equivalence_status"] == "complete"
    assert normalized["summary"]["truth_rows"] == 4
    assert normalized["summary"]["latency_rows"] == 1
    assert normalized["summary"]["runtime_metric_rows"] == 1
    assert normalized["host"]["system"] == platform.system()
    assert normalized["host"]["machine"] == platform.machine()
    assert normalized["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert normalized["proof_context"]["evidence_class"] == "truth_backed_bridge"
    assert normalized["proof_context"]["comparison_axis"] == "engine_adapter"
    assert normalized["proof_context"]["platform"]["engine_family"] == "unity"

    runtime_path = tmp_path / "unity_runtime_verification.json"
    workflow_path = tmp_path / "unity_workflow_report.json"
    equivalence_path = tmp_path / "unity_cross_engine_equivalence.json"
    install_smoke_path = tmp_path / "unity_install_smoke.json"
    replay_matrix_path = tmp_path / "missing_replay_matrix.json"
    runtime_path.write_text(json.dumps(runtime) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow) + "\n", encoding="utf-8")
    equivalence_path.write_text(json.dumps(equivalence) + "\n", encoding="utf-8")
    install_smoke_path.write_text(json.dumps(install_smoke) + "\n", encoding="utf-8")
    out_dir = tmp_path / "reports"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_unity_runtime_verification.py"),
            "--runtime",
            str(runtime_path),
            "--workflow",
            str(workflow_path),
            "--equivalence",
            str(equivalence_path),
            "--install-smoke",
            str(install_smoke_path),
            "--replay-matrix",
            str(replay_matrix_path),
            "--out-dir",
            str(out_dir),
            "--scenario",
            "unity_runtime_verification",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    json_path = out_dir / "unity_engine_benchmark_report.json"
    md_path = out_dir / "unity_engine_benchmark_report.md"
    assert json_path.is_file()
    assert md_path.is_file()

    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["rows"][0]["truth"]["final_truth_match"] is True
    canonical_row = next(row for row in written["rows"] if row["scenario"] == "entity_state_1x10hz")
    assert canonical_row["truth"]["final_truth_match"] is True
    assert canonical_row["truth"]["source_truth_schema"] == "fastdis.unity_editor_method_verification.v1"
    assert written["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert any(row["scenario"] == "entity_state_1x10hz" for row in written["rows"])
    assert any(row["scenario"] == "unity_replay_latest_state_apply" for row in written["rows"])
    assert any(row["scenario"] == "unity_install_smoke_runtime" for row in written["rows"])
    assert "canonical Unity runtime benchmark row(s) are available" in "\n".join(written["rows"][0]["metrics"]["notes"])


def test_normalize_unity_runtime_verification_preserves_multiple_canonical_rows() -> None:
    module = _load_module("normalize_unity_runtime_verification", ROOT / "tools" / "normalize_unity_runtime_verification.py")
    runtime = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_runtime_verification.sample.json").read_text(encoding="utf-8"))
    workflow = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_workflow_report.sample.json").read_text(encoding="utf-8"))
    equivalence = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_cross_engine_equivalence.sample.json").read_text(encoding="utf-8"))
    install_smoke = {"status": "pass", "elapsed_seconds": 9.111}
    runtime["lanes"][0]["details"]["benchmark_rows"].append(
        {
            "scenario": "entity_state_100x30hz",
            "entity_count": 100,
            "update_hz": 30,
            "packets_received": 300,
            "packets_parsed": 300,
            "packets_accepted": 300,
            "packets_rejected": 0,
            "malformed": 0,
            "main_thread_apply_ms": 0.11,
            "packets_per_sec": 9000.0,
            "steady_state_gc_bytes": 0,
            "notes": "Measured from the Unity editor-method runtime lane by injecting three hundred Entity State updates across one hundred entities through FastDisNetworkReceiver into FastDisWorld on the main thread.",
        }
    )

    normalized = module.normalize_payload(
        runtime,
        workflow_payload=workflow,
        equivalence_payload=equivalence,
        install_smoke_payload=install_smoke,
        replay_matrix_payload=None,
        scenario="unity_runtime_verification",
        source_payload="artifacts/reports/unity_runtime_verification.json",
    )

    assert any(row["scenario"] == "entity_state_1x10hz" for row in normalized["rows"])
    assert any(row["scenario"] == "entity_state_100x30hz" for row in normalized["rows"])


def test_normalize_unity_runtime_verification_prefers_replay_matrix_rows_for_canonical_scenarios() -> None:
    module = _load_module("normalize_unity_runtime_verification", ROOT / "tools" / "normalize_unity_runtime_verification.py")
    runtime = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_runtime_verification.sample.json").read_text(encoding="utf-8"))
    workflow = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_workflow_report.sample.json").read_text(encoding="utf-8"))
    equivalence = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unity_cross_engine_equivalence.sample.json").read_text(encoding="utf-8"))
    install_smoke = {"status": "pass", "elapsed_seconds": 9.111}
    replay_route = {
        "surface": "unity",
        "mode": "replay",
        "scenario": "entity_state_100x30hz",
        "status": "passed",
        "report": {
            "loaded_packets": 300,
            "known_entities": 100,
            "moved_entity_count": 100,
        },
        "errors": [],
        "truth": {
            "schema": "fastdis.network_truth.v1",
            "packet_count": 300,
            "packets_parsed": 300,
            "malformed": 0,
            "entity_state": 300,
            "unique_entities": 100,
            "latest_entities": [],
            "errors": [],
        },
        "truth_file": "artifacts/reports/unity_replay_matrix/entity_state_100x30hz.truth.json",
    }

    runtime["lanes"][0]["details"]["benchmark_rows"].append(
        {
            "scenario": "entity_state_100x30hz",
            "entity_count": 100,
            "update_hz": 30,
            "packets_received": 999,
            "packets_parsed": 999,
            "packets_accepted": 999,
            "packets_rejected": 0,
            "malformed": 0,
            "main_thread_apply_ms": 0.99,
            "packets_per_sec": 9999.0,
            "steady_state_gc_bytes": 999,
            "notes": "stale editor-method row should be suppressed when replay-matrix evidence exists",
        }
    )

    normalized = module.normalize_payload(
        runtime,
        workflow_payload=workflow,
        equivalence_payload=equivalence,
        install_smoke_payload=install_smoke,
        replay_matrix_payload={"routes": [replay_route]},
        scenario="unity_runtime_verification",
        source_payload="artifacts/reports/unity_runtime_verification.json",
    )

    matching_rows = [row for row in normalized["rows"] if row["scenario"] == "entity_state_100x30hz"]
    assert len(matching_rows) == 1
    assert matching_rows[0]["metrics"]["packets_received"] == 300
    assert matching_rows[0]["truth"]["final_truth_match"] is True
    assert matching_rows[0]["truth"]["source_truth_schema"] == "fastdis.network_truth.v1"
    assert matching_rows[0]["truth"]["network_ingest_mode"] == "replay"
