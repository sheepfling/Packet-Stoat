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


def _sample_payload() -> dict:
    return {
        "generated_at_utc": "2026-06-26T00:00:00Z",
        "host": {"system": "Darwin", "machine": "arm64"},
        "native": {
            "results": [
                {
                    "case": "header_all_no_callback",
                    "packets": 1000,
                    "avg_ms": 1.0,
                    "p50_ms": 1.0,
                    "p95_ms": 1.1,
                    "p99_ms": 1.2,
                    "seen": 1000,
                    "accepted": 1000,
                    "emitted": 1000,
                    "malformed": 0,
                    "notes": "native baseline",
                }
            ]
        },
        "cpp": {
            "results": [
                {
                    "case": "cpp_header_no_callback",
                    "packets": 1000,
                    "packets_per_sec": 950000.0,
                    "avg_ms": 1.05,
                    "p50_ms": 1.0,
                    "p95_ms": 1.15,
                    "p99_ms": 1.25,
                    "seen": 1000,
                    "accepted": 1000,
                    "emitted": 1000,
                    "malformed": 0,
                    "notes": "cpp baseline",
                }
            ]
        },
        "ctypes": {
            "results": [
                {
                    "case": "ctypes_header_no_callback",
                    "packets": 1000,
                    "packets_per_sec": 90000.0,
                    "avg_ms": 11.0,
                    "p50_ms": 11.0,
                    "p95_ms": 11.9,
                    "p99_ms": 12.0,
                    "seen": 3000,
                    "accepted": 3000,
                    "emitted": 3000,
                    "malformed": 0,
                    "notes": "ctypes baseline",
                }
            ]
        },
    }


def test_engine_benchmark_scenario_contract_exists() -> None:
    payload = json.loads((ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix.v1.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.engine_benchmark_scenario.v1"
    assert len(payload["scenarios"]) >= 6
    assert any(row["name"] == "entity_state_1000x60hz" for row in payload["scenarios"])


def test_benchmark_claim_summary_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.benchmark_claim_summary.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.benchmark_claim_summary.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.benchmark_claim_summary.v1"
    assert "publishable_today" in payload["required"]
    assert "not_publishable_yet" in payload["required"]
    assert "measured_surfaces" in payload["required"]


def test_proof_context_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.proof_context.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.proof_context.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.proof_context.v1"
    assert "host" in payload["required"]
    assert "platform" in payload["required"]
    assert "qualification" in payload["required"]


def test_grill_harness_capture_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.grill_harness_capture.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.grill_harness_capture.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.grill_harness_capture.v1"
    assert "lane" in payload["required"]
    assert "runtime" in payload["required"]
    assert "results" in payload["required"]


def test_benchmark_coverage_report_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.benchmark_coverage_report.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.benchmark_coverage_report.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.benchmark_coverage_report.v1"
    assert "summary" in payload["required"]
    assert "surfaces" in payload["required"]


def test_surface_claim_report_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.surface_claim_report.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.surface_claim_report.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.surface_claim_report.v1"
    assert "surface_count" in payload["required"]
    assert "surfaces" in payload["required"]


def test_scenario_contract_report_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.scenario_contract_report.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.scenario_contract_report.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.scenario_contract_report.v1"
    assert "canonical_scenarios" in payload["required"]
    assert "surfaces" in payload["required"]


def test_engine_benchmark_matrix_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.engine_benchmark_matrix.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.engine_benchmark_matrix.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.engine_benchmark_matrix.v1"
    assert "surfaces" in payload["required"]
    assert "comparisons" in payload["required"]
    assert "claim_boundaries" in payload["required"]


def test_engine_benchmark_completion_audit_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.engine_benchmark_completion_audit.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.engine_benchmark_completion_audit.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.engine_benchmark_completion_audit.v1"
    assert "requirements" in payload["required"]
    assert "claim_boundaries" in payload["required"]
    assert "next_steps" in payload["required"]


def test_engine_head_to_head_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.engine_head_to_head_report.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.engine_head_to_head_report.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.engine_head_to_head_report.v1"
    assert "inputs" in payload["required"]
    assert "comparison" in payload["required"]


def test_cross_engine_equivalence_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.cross_engine_equivalence_report.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.cross_engine_equivalence_report.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.cross_engine_equivalence_report.v1"
    assert "deep_surfaces" in payload["required"]
    assert "benchmark_surfaces" in payload["required"]


def test_competitor_capture_manifest_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.competitor_capture_manifest.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.competitor_capture_manifest.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.competitor_capture_manifest.v1"
    assert "lanes" in payload["required"]
    assert "common_requirements" in payload["required"]


def test_competitor_lane_summary_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.competitor_lane_summary.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.competitor_lane_summary.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.competitor_lane_summary.v1"
    assert "summary" in payload["required"]
    assert "lanes" in payload["required"]


def test_competitor_capture_validation_schema_contract_exists() -> None:
    payload = json.loads(
        (ROOT / "schemas" / "json" / "fastdis.competitor_capture_validation.v1.schema.json").read_text(encoding="utf-8")
    )
    assert payload["$id"].endswith("/fastdis.competitor_capture_validation.v1.schema.json")
    assert payload["properties"]["schema"]["const"] == "fastdis.competitor_capture_validation.v1"
    assert "lanes" in payload["required"]
    assert "errors" in payload["required"]
    assert "handoff_workbench" in payload["required"]
    assert payload["properties"]["handoff_workbench"]["properties"]["schema"]["const"] == "fastdis.competitor_handoff_workbench_check.v1"
    assert "bundle_kind" in payload["properties"]["handoff_workbench"]["properties"]["summary"]["required"]
    assert "self_describing_bundle" in payload["properties"]["handoff_workbench"]["properties"]["summary"]["required"]


def test_engine_benchmark_truth_contract_matches_scenarios() -> None:
    scenario_payload = json.loads(
        (ROOT / "tests" / "data" / "engine_benchmark_scenarios" / "core_matrix.v1.json").read_text(encoding="utf-8")
    )
    truth_payload = json.loads(
        (ROOT / "tests" / "data" / "engine_benchmark_truth" / "core_matrix.v1.json").read_text(encoding="utf-8")
    )

    assert truth_payload["schema"] == "fastdis.engine_benchmark_truth.v1"
    assert truth_payload["suite"] == scenario_payload["suite"]

    scenario_names = {row["name"] for row in scenario_payload["scenarios"]}
    truth_names = {row["scenario"] for row in truth_payload["truths"]}
    assert truth_names == scenario_names

    entity_truth = next(row for row in truth_payload["truths"] if row["scenario"] == "entity_state_1000x60hz")
    assert entity_truth["expectations"]["final_truth_match_required"] is True
    assert entity_truth["expectations"]["latest_state_required"] is True
    assert entity_truth["expectations"]["unique_entities_expected"] == 1000

    malformed_truth = next(row for row in truth_payload["truths"] if row["scenario"] == "malformed_10pct")
    assert malformed_truth["expectations"]["final_truth_match_required"] is True
    assert malformed_truth["expectations"]["replay_final_transform_required"] is False


def test_normalize_current_benchmarks_builds_shared_reports(tmp_path: Path) -> None:
    module = _load_module("normalize_current_benchmarks", ROOT / "tools" / "normalize_current_benchmarks.py")
    payload = _sample_payload()

    native_report = module.normalize_surface(
        "native",
        "native",
        payload["native"]["results"],
        generated_at_utc=payload["generated_at_utc"],
        host=payload["host"],
        source_payload="artifacts/benchmark_results/current/current.json",
        source_schema="fastdis.native_benchmark.current",
    )

    assert native_report["schema"] == "fastdis.engine_benchmark_report.v1"
    assert native_report["surface"] == "native"
    assert native_report["rows"][0]["scenario"] == "header_all_no_callback"
    assert native_report["rows"][0]["metrics"]["packets_per_sec"] == 1000000.0
    assert native_report["rows"][0]["metrics"]["packets_rejected"] == 0
    assert "native baseline" in native_report["rows"][0]["metrics"]["notes"]

    input_path = tmp_path / "current.json"
    out_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_current_benchmarks.py"),
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
    native_path = out_dir / "native_engine_benchmark_report.json"
    cpp_path = out_dir / "cpp_engine_benchmark_report.json"
    ctypes_path = out_dir / "python_ctypes_engine_benchmark_report.json"
    assert native_path.is_file()
    assert cpp_path.is_file()
    assert ctypes_path.is_file()
    native_written = json.loads(native_path.read_text(encoding="utf-8"))
    cpp_written = json.loads(cpp_path.read_text(encoding="utf-8"))
    ctypes_written = json.loads(ctypes_path.read_text(encoding="utf-8"))
    assert native_written["surface_kind"] == "native"
    assert cpp_written["surface_kind"] == "cpp"
    assert cpp_written["rows"][0]["metrics"]["packets_per_sec"] == 950000.0
    assert ctypes_written["surface_kind"] == "python"
    assert ctypes_written["rows"][0]["metrics"]["packets_per_sec"] == 90000.0


def test_append_optional_python_ctypes_canonical_row_adds_truth_backed_shared_scenarios() -> None:
    module = _load_module("normalize_current_benchmarks", ROOT / "tools" / "normalize_current_benchmarks.py")
    payload = _sample_payload()
    report = module.normalize_surface(
        "python_ctypes",
        "python",
        payload["ctypes"]["results"],
        generated_at_utc=payload["generated_at_utc"],
        host=payload["host"],
        source_payload="artifacts/benchmark_results/current/current.json",
        source_schema="fastdis.ctypes_benchmark.current",
    )

    augmented = module.append_optional_python_ctypes_canonical_row(
        report,
        builder=lambda: [
            {
                "scenario": "entity_state_1x10hz",
                "metrics": {
                    "packets_received": 24,
                    "packets_parsed": 24,
                    "packets_accepted": 24,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.01,
                    "packets_per_sec": 2400.0,
                    "notes": ["truth-backed canonical ctypes row"],
                },
                "truth": {"final_truth_match": True},
            },
            {
                "scenario": "entity_state_100x30hz",
                "metrics": {
                    "packets_received": 300,
                    "packets_parsed": 300,
                    "packets_accepted": 300,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.1,
                    "packets_per_sec": 3000.0,
                    "notes": ["truth-backed canonical ctypes row"],
                },
                "truth": {"final_truth_match": True},
            },
            {
                "scenario": "replay_latest_state_apply",
                "metrics": {
                    "packets_received": 300,
                    "packets_parsed": 300,
                    "packets_accepted": 300,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.1,
                    "packets_per_sec": 3000.0,
                    "notes": ["truth-backed canonical ctypes replay row"],
                },
                "truth": {"final_truth_match": True},
            },
            {
                "scenario": "entity_state_10000_burst",
                "metrics": {
                    "packets_received": 10000,
                    "packets_parsed": 10000,
                    "packets_accepted": 10000,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.5,
                    "packets_per_sec": 20000.0,
                    "notes": ["truth-backed canonical ctypes burst row"],
                },
                "truth": {"final_truth_match": True},
            },
        ],
    )

    assert augmented["summary"]["row_count"] == 5
    assert augmented["summary"]["runtime_metric_rows"] == 4
    assert augmented["summary"]["truth_rows"] == 4
    assert [row["scenario"] for row in augmented["rows"][-4:]] == [
        "entity_state_1x10hz",
        "entity_state_100x30hz",
        "replay_latest_state_apply",
        "entity_state_10000_burst",
    ]
    assert augmented["rows"][-1]["truth"]["final_truth_match"] is True


def test_append_optional_native_canonical_row_adds_truth_backed_shared_scenario() -> None:
    module = _load_module("normalize_current_benchmarks", ROOT / "tools" / "normalize_current_benchmarks.py")
    payload = _sample_payload()
    report = module.normalize_surface(
        "native",
        "native",
        payload["native"]["results"],
        generated_at_utc=payload["generated_at_utc"],
        host=payload["host"],
        source_payload="artifacts/benchmark_results/current/current.json",
        source_schema="fastdis.native_benchmark.current",
    )

    augmented = module.append_optional_native_canonical_row(
        report,
        loader=lambda: {
            "scenario": "entity_state_1x10hz",
            "metrics": {
                "packets_received": 24,
                "packets_parsed": 24,
                "packets_accepted": 24,
                "packets_rejected": 0,
                "malformed": 0,
                "socket_drops": None,
                "queue_drops": None,
                "p50_ingest_ms": None,
                "p95_ingest_ms": None,
                "p99_ingest_ms": None,
                "steady_state_gc_bytes": None,
                "main_thread_apply_ms": None,
                "runtime_elapsed_seconds": 0.005,
                "packets_per_sec": 4800.0,
                "notes": ["truth-backed canonical native row"],
            },
            "truth": {"final_truth_match": True},
        },
    )

    assert augmented["summary"]["row_count"] == 2
    assert augmented["summary"]["runtime_metric_rows"] == 1
    assert augmented["summary"]["truth_rows"] == 1
    assert augmented["rows"][-1]["scenario"] == "entity_state_1x10hz"
    assert augmented["rows"][-1]["truth"]["final_truth_match"] is True


def test_append_optional_native_canonical_row_accepts_multiple_truth_backed_shared_scenarios() -> None:
    module = _load_module("normalize_current_benchmarks", ROOT / "tools" / "normalize_current_benchmarks.py")
    payload = _sample_payload()
    report = module.normalize_surface(
        "native",
        "native",
        payload["native"]["results"],
        generated_at_utc=payload["generated_at_utc"],
        host=payload["host"],
        source_payload="artifacts/benchmark_results/current/current.json",
        source_schema="fastdis.native_benchmark.current",
    )

    augmented = module.append_optional_native_canonical_row(
        report,
        loader=lambda: [
            {
                "scenario": "entity_state_1x10hz",
                "metrics": {
                    "packets_received": 24,
                    "packets_parsed": 24,
                    "packets_accepted": 24,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.005,
                    "packets_per_sec": 4800.0,
                    "notes": ["truth-backed canonical native row"],
                },
                "truth": {"final_truth_match": True},
            },
            {
                "scenario": "entity_state_100x30hz",
                "metrics": {
                    "packets_received": 300,
                    "packets_parsed": 300,
                    "packets_accepted": 300,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.015,
                    "packets_per_sec": 20000.0,
                    "notes": ["truth-backed canonical native row"],
                },
                "truth": {"final_truth_match": True},
            },
            {
                "scenario": "entity_state_10000_burst",
                "metrics": {
                    "packets_received": 10000,
                    "packets_parsed": 10000,
                    "packets_accepted": 10000,
                    "packets_rejected": 0,
                    "malformed": 0,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": None,
                    "main_thread_apply_ms": None,
                    "runtime_elapsed_seconds": 0.25,
                    "packets_per_sec": 40000.0,
                    "notes": ["truth-backed canonical native burst row"],
                },
                "truth": {"final_truth_match": True},
            },
        ],
    )

    assert [row["scenario"] for row in augmented["rows"][-3:]] == [
        "entity_state_1x10hz",
        "entity_state_100x30hz",
        "entity_state_10000_burst",
    ]
    assert augmented["summary"]["row_count"] == 4
    assert augmented["summary"]["runtime_metric_rows"] == 3
    assert augmented["summary"]["truth_rows"] == 3
