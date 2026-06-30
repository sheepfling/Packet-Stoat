from __future__ import annotations

import importlib.util
import json
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


def test_godot_udp_smoke_sample_fixture_is_stable() -> None:
    payload_path = ROOT / "tests" / "data" / "engine_benchmark_sources" / "godot_udp_smoke.sample.json"
    truth_path = ROOT / "tests" / "data" / "engine_benchmark_sources" / "godot_udp_smoke.sample.truth.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    truth = json.loads(truth_path.read_text(encoding="utf-8"))

    assert payload["surface"] == "godot"
    assert payload["mode"] == "live_udp"
    assert payload["truth_file"] == "tests/data/engine_benchmark_sources/godot_udp_smoke.sample.truth.json"
    assert truth["schema"] == "fastdis.network_truth.v1"
    assert truth["unique_entities"] == 3


def test_normalize_godot_proof_reports_adds_replay_row() -> None:
    module = _load_module("normalize_godot_proof_reports", ROOT / "tools" / "normalize_godot_proof_reports.py")
    workflow = json.loads((ROOT / "artifacts" / "reports" / "godot_workflow_report.json").read_text(encoding="utf-8"))

    normalized = module.normalize_payload(
        workflow,
        orientation_payload=None,
        network_ingest_payload=None,
        replay_matrix_payload=None,
        scenario="godot_proof_verification",
        source_payload="artifacts/reports/godot_workflow_report.json",
    )

    assert normalized["rows"][0]["scenario"] == "godot_proof_verification"
    assert normalized["rows"][1]["scenario"] == "replay_latest_state_apply"
    assert normalized["rows"][1]["truth"]["final_truth_match"] is True
    assert normalized["rows"][1]["truth"]["demo_status"] == "passed"
    assert any(row["scenario"] == "godot_demo_runtime" for row in normalized["rows"])
    runtime_row = next(row for row in normalized["rows"] if row["scenario"] == "godot_demo_runtime")
    assert runtime_row["metrics"]["runtime_elapsed_seconds"] is not None
    assert normalized["summary"]["truth_rows"] == 3
    assert normalized["summary"]["runtime_metric_rows"] == 1


def test_normalize_godot_udp_smoke_builds_shared_report(tmp_path: Path) -> None:
    module = _load_module("normalize_godot_udp_smoke", ROOT / "tools" / "normalize_godot_udp_smoke.py")

    truth_path = tmp_path / "expected_session.json"
    truth_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.network_truth.v1",
                "packet_count": 24,
                "packets_parsed": 24,
                "malformed": 0,
                "entity_state": 24,
                "unique_entities": 3,
                "latest_entities": [
                    {
                        "site": 1,
                        "application": 1,
                        "entity": 1,
                        "force_id": 1,
                        "location_ecef_m": [1.0, 2.0, 3.0],
                        "orientation_dis_rad": [0.0, 0.0, 0.0]
                    }
                ],
                "errors": []
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = {
        "surface": "godot",
        "mode": "live_udp",
        "status": "passed",
        "report": {
            "packets_received": 24,
            "known_entities": 3,
            "moved_entity_count": 3,
        },
        "errors": [],
        "truth_file": str(truth_path),
    }

    normalized = module.normalize_payload(
        payload,
        scenario="entity_state_1x10hz",
        source_payload="artifacts/verification_reports/godot/live_udp_smoke.json",
    )

    assert normalized["schema"] == "fastdis.engine_benchmark_report.v1"
    assert normalized["surface"] == "godot"
    assert normalized["surface_kind"] == "engine"
    assert normalized["rows"][0]["scenario"] == "entity_state_1x10hz"
    assert normalized["rows"][0]["metrics"]["packets_received"] == 24
    assert normalized["rows"][0]["metrics"]["packets_parsed"] == 24
    assert normalized["rows"][0]["metrics"]["packets_accepted"] == 24
    assert normalized["rows"][0]["metrics"]["packets_rejected"] == 0
    assert normalized["rows"][0]["truth"]["final_truth_match"] is True
    assert normalized["rows"][0]["truth"]["unique_entities_expected"] == 3
    assert normalized["summary"]["truth_rows"] == 1
    assert normalized["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert normalized["proof_context"]["evidence_class"] == "truth_backed_bridge"
    assert normalized["proof_context"]["comparison_axis"] == "engine_adapter"
    assert normalized["proof_context"]["platform"]["engine_family"] == "godot"

    input_path = tmp_path / "godot_udp_smoke.json"
    input_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    out_dir = tmp_path / "reports"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_godot_udp_smoke.py"),
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
            "--scenario",
            "entity_state_1x10hz",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    json_path = out_dir / "godot_engine_benchmark_report.json"
    md_path = out_dir / "godot_engine_benchmark_report.md"
    assert json_path.is_file()
    assert md_path.is_file()

    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["rows"][0]["truth"]["source_truth_schema"] == "fastdis.network_truth.v1"
    assert written["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert "Latency and main-thread timing fields remain null" in "\n".join(written["rows"][0]["metrics"]["notes"])
