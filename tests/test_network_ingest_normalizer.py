from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_normalize_network_ingest_matrix_emits_c_and_cpp_reports(tmp_path: Path) -> None:
    payload = {
        "generated_at": "2026-06-26T00:00:00Z",
        "routes": [
            {
                "surface": "c",
                "mode": "localhost_udp",
                "scenario": "entity_state_1x10hz",
                "status": "passed",
                "elapsed_seconds": 0.25,
                "errors": [],
                "report": {
                    "schema": "fastdis.c_udp_burst_report.v1",
                    "packets_received": 24,
                    "packets_parsed": 24,
                    "malformed": 0,
                    "entity_state": 24,
                },
            },
            {
                "surface": "c",
                "mode": "localhost_udp",
                "scenario": "entity_state_100x30hz",
                "status": "passed",
                "elapsed_seconds": 1.25,
                "errors": [],
                "report": {
                    "schema": "fastdis.c_udp_burst_report.v1",
                    "packets_received": 300,
                    "packets_parsed": 300,
                    "malformed": 0,
                    "entity_state": 300,
                },
            },
            {
                "surface": "c",
                "mode": "localhost_udp",
                "scenario": "entity_state_1000x60hz",
                "status": "passed",
                "elapsed_seconds": 4.25,
                "errors": [],
                "report": {
                    "schema": "fastdis.c_udp_burst_report.v1",
                    "packets_received": 1000,
                    "packets_parsed": 1000,
                    "malformed": 0,
                    "entity_state": 1000,
                },
            },
            {
                "surface": "cpp",
                "mode": "localhost_udp",
                "scenario": "entity_state_1x10hz",
                "status": "passed",
                "elapsed_seconds": 0.2,
                "errors": [],
                "report": {
                    "schema": "fastdis.cpp_udp_burst_report.v1",
                    "packets_received": 24,
                    "packets_parsed": 24,
                    "malformed": 0,
                    "entity_state": 24,
                },
            },
            {
                "surface": "cpp",
                "mode": "localhost_udp",
                "scenario": "entity_state_100x30hz",
                "status": "passed",
                "elapsed_seconds": 1.0,
                "errors": [],
                "report": {
                    "schema": "fastdis.cpp_udp_burst_report.v1",
                    "packets_received": 300,
                    "packets_parsed": 300,
                    "malformed": 0,
                    "entity_state": 300,
                },
            },
            {
                "surface": "cpp",
                "mode": "localhost_udp",
                "scenario": "entity_state_1000x60hz",
                "status": "passed",
                "elapsed_seconds": 4.0,
                "errors": [],
                "report": {
                    "schema": "fastdis.cpp_udp_burst_report.v1",
                    "packets_received": 1000,
                    "packets_parsed": 1000,
                    "malformed": 0,
                    "entity_state": 1000,
                },
            },
        ],
    }
    input_path = tmp_path / "network_ingest_matrix.json"
    out_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_network_ingest_matrix.py"),
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    c_report = json.loads((out_dir / "c_engine_benchmark_report.json").read_text(encoding="utf-8"))
    cpp_report = json.loads((out_dir / "cpp_engine_benchmark_report.json").read_text(encoding="utf-8"))
    assert c_report["surface"] == "c"
    assert c_report["rows"][0]["scenario"] == "entity_state_1x10hz"
    assert c_report["rows"][1]["scenario"] == "entity_state_100x30hz"
    assert c_report["rows"][2]["scenario"] == "entity_state_1000x60hz"
    assert c_report["rows"][0]["truth"]["final_truth_match"] is True
    assert c_report["rows"][0]["metrics"]["runtime_elapsed_seconds"] == 0.25
    assert c_report["summary"]["row_count"] == 3
    assert c_report["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert c_report["proof_context"]["evidence_class"] == "truth_backed_bridge"
    assert c_report["proof_context"]["comparison_axis"] == "language_surface"
    assert c_report["proof_context"]["platform"]["runtime_kind"] == "c"
    assert cpp_report["surface"] == "cpp"
    assert cpp_report["rows"][0]["scenario"] == "entity_state_1x10hz"
    assert cpp_report["rows"][1]["scenario"] == "entity_state_100x30hz"
    assert cpp_report["rows"][2]["scenario"] == "entity_state_1000x60hz"
    assert cpp_report["rows"][0]["metrics"]["packets_parsed"] == 24
    assert cpp_report["proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert cpp_report["proof_context"]["platform"]["runtime_kind"] == "cpp"
