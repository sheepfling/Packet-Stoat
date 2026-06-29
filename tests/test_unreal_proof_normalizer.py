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


def test_unreal_proof_sample_fixtures_are_stable() -> None:
    readiness = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_fab_readiness.sample.json").read_text(encoding="utf-8"))
    packaged = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_packaged_install_smoke.sample.json").read_text(encoding="utf-8"))
    orientation = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_orientation_compare.sample.json").read_text(encoding="utf-8"))

    assert readiness["overall_status"] == "fab_ready"
    assert packaged["status"] == "pass"
    assert orientation["results"][0]["pass"] is True


def test_normalize_unreal_proof_reports_builds_shared_report(tmp_path: Path) -> None:
    module = _load_module("normalize_unreal_proof_reports", ROOT / "tools" / "normalize_unreal_proof_reports.py")
    readiness = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_fab_readiness.sample.json").read_text(encoding="utf-8"))
    packaged = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_packaged_install_smoke.sample.json").read_text(encoding="utf-8"))
    orientation = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_orientation_compare.sample.json").read_text(encoding="utf-8"))
    packaged["elapsed_seconds"] = 12.5

    normalized = module.normalize_payload(
        readiness,
        packaged_payload=packaged,
        orientation_payload=orientation,
        network_ingest_payload=None,
        udp_matrix_payload=None,
        scenario="unreal_proof_verification",
        source_payload="build/reports/unreal_fab_readiness.json",
    )

    assert normalized["schema"] == "fastdis.engine_benchmark_report.v1"
    assert normalized["surface"] == "unreal"
    assert normalized["surface_kind"] == "engine"
    assert normalized["rows"][0]["scenario"] == "unreal_proof_verification"
    assert normalized["rows"][1]["scenario"] == "unreal_packaged_install_runtime"
    assert normalized["rows"][0]["metrics"]["packets_received"] is None
    assert normalized["rows"][0]["truth"]["final_truth_match"] is True
    assert normalized["rows"][1]["metrics"]["runtime_elapsed_seconds"] == 12.5
    assert normalized["rows"][0]["truth"]["fab_readiness_status"] == "fab_ready"
    assert normalized["rows"][0]["truth"]["packaged_install_status"] == "pass"
    assert normalized["rows"][0]["truth"]["orientation_status"] is True
    assert normalized["summary"]["truth_rows"] == 2
    assert normalized["summary"]["runtime_metric_rows"] == 1
    assert normalized["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert normalized["proof_context"]["evidence_class"] == "truth_backed_bridge"
    assert normalized["proof_context"]["comparison_axis"] == "engine_adapter"
    assert normalized["proof_context"]["platform"]["engine_family"] == "unreal"

    readiness_path = tmp_path / "unreal_fab_readiness.json"
    packaged_path = tmp_path / "unreal_packaged_install_smoke.json"
    orientation_path = tmp_path / "unreal_orientation_compare.json"
    readiness_path.write_text(json.dumps(readiness) + "\n", encoding="utf-8")
    packaged_path.write_text(json.dumps(packaged) + "\n", encoding="utf-8")
    orientation_path.write_text(json.dumps(orientation) + "\n", encoding="utf-8")
    out_dir = tmp_path / "reports"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_unreal_proof_reports.py"),
            "--readiness",
            str(readiness_path),
            "--packaged",
            str(packaged_path),
            "--orientation",
            str(orientation_path),
            "--out-dir",
            str(out_dir),
            "--scenario",
            "unreal_proof_verification",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    json_path = out_dir / "unreal_engine_benchmark_report.json"
    md_path = out_dir / "unreal_engine_benchmark_report.md"
    assert json_path.is_file()
    assert md_path.is_file()

    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["rows"][0]["truth"]["final_truth_match"] is True
    assert written["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert any(row["scenario"] == "unreal_packaged_install_runtime" for row in written["rows"])
    assert "Latency, packet-rate, and main-thread apply metrics remain null" in "\n".join(written["rows"][0]["metrics"]["notes"])


def test_normalize_unreal_proof_reports_appends_live_udp_row() -> None:
    module = _load_module("normalize_unreal_proof_reports", ROOT / "tools" / "normalize_unreal_proof_reports.py")
    readiness = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_fab_readiness.sample.json").read_text(encoding="utf-8"))
    packaged = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_packaged_install_smoke.sample.json").read_text(encoding="utf-8"))
    orientation = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_orientation_compare.sample.json").read_text(encoding="utf-8"))
    live_udp = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_udp_smoke.sample.json").read_text(encoding="utf-8"))
    live_udp["scenario"] = "entity_state_1x10hz"

    normalized = module.normalize_payload(
        readiness,
        packaged_payload=packaged,
        orientation_payload=orientation,
        network_ingest_payload={"routes": [live_udp]},
        udp_matrix_payload=None,
        scenario="unreal_proof_verification",
        source_payload="build/reports/unreal_fab_readiness.json",
    )

    assert any(row["scenario"] == "entity_state_1x10hz" for row in normalized["rows"])


def test_normalize_unreal_proof_reports_appends_multiple_live_udp_rows() -> None:
    module = _load_module("normalize_unreal_proof_reports", ROOT / "tools" / "normalize_unreal_proof_reports.py")
    readiness = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_fab_readiness.sample.json").read_text(encoding="utf-8"))
    packaged = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_packaged_install_smoke.sample.json").read_text(encoding="utf-8"))
    orientation = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_orientation_compare.sample.json").read_text(encoding="utf-8"))
    live_udp_a = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_udp_smoke.sample.json").read_text(encoding="utf-8"))
    live_udp_b = json.loads((ROOT / "tests" / "data" / "engine_benchmark_sources" / "unreal_udp_smoke.sample.json").read_text(encoding="utf-8"))
    live_udp_a["scenario"] = "entity_state_1x10hz"
    live_udp_b["scenario"] = "entity_state_100x30hz"
    live_udp_b["truth"] = {
        "schema": "fastdis.network_truth.v1",
        "packet_count": 300,
        "packets_parsed": 300,
        "malformed": 0,
        "entity_state": 300,
        "unique_entities": 100,
        "latest_entities": [],
        "errors": [],
    }

    normalized = module.normalize_payload(
        readiness,
        packaged_payload=packaged,
        orientation_payload=orientation,
        network_ingest_payload=None,
        udp_matrix_payload={"routes": [live_udp_a, live_udp_b]},
        scenario="unreal_proof_verification",
        source_payload="build/reports/unreal_fab_readiness.json",
    )

    assert any(row["scenario"] == "entity_state_1x10hz" for row in normalized["rows"])
    assert any(row["scenario"] == "entity_state_100x30hz" for row in normalized["rows"])


def test_load_truth_from_route_prefers_inline_truth_for_unreal() -> None:
    module = _load_module("normalize_unreal_proof_reports", ROOT / "tools" / "normalize_unreal_proof_reports.py")
    truth, truth_path = module._load_truth_from_route(
        {
            "truth": {"schema": "fastdis.network_truth.v1", "unique_entities": 1},
            "truth_file": "build/reports/network_ingest_matrix/truth/unreal_live_udp_entity_state_1x10hz.truth.json",
        }
    )
    assert truth["unique_entities"] == 1
    assert truth_path.endswith("build/reports/network_ingest_matrix/truth/unreal_live_udp_entity_state_1x10hz.truth.json")
