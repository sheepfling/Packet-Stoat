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


def test_normalize_unity_grill_baseline_payload() -> None:
    module = _load_module("normalize_unity_grill_baseline", ROOT / "tools" / "normalize_unity_grill_baseline.py")
    payload = {
        "schema": "fastdis.unity_grill_benchmark_baseline.v1",
        "product": "GRILL DIS for Unity",
        "captured_at_utc": "2026-06-26T00:00:00Z",
        "repository": {"url": "https://github.com/AF-GRILL/DISPluginForUnity", "commit": "abc123"},
        "unity": {"version": "6000.5.0f1"},
        "host": {"system": "Windows", "release": "11", "machine": "x86_64"},
        "scenario": {"scene": "LoopbackBench", "traffic_mix": "100% Entity State"},
        "results": [
            {
                "case": "entity_state_100x30hz",
                "entity_count": 100,
                "update_hz": 30,
                "packets_per_sec": 95000,
                "main_thread_ms_avg": 1.2,
                "gc_alloc_bytes_per_frame": 0,
            }
        ],
    }

    report = module.normalize_payload(payload, source_payload="verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json")

    assert report["surface"] == "grill_unity"
    assert report["surface_kind"] == "competitor"
    assert report["summary"]["row_count"] == 1
    assert report["rows"][0]["scenario"] == "entity_state_100x30hz"
    assert report["rows"][0]["metrics"]["main_thread_apply_ms"] == 1.2
    assert report["rows"][0]["truth"]["final_truth_match"] is None


def test_normalize_unreal_grill_baseline_payload() -> None:
    module = _load_module("normalize_unreal_grill_baseline", ROOT / "tools" / "normalize_unreal_grill_baseline.py")
    payload = {
        "schema": "fastdis.unreal_grill_benchmark_baseline.v1",
        "product": "GRILL DIS for Unreal",
        "captured_at_utc": "2026-06-26T00:00:00Z",
        "repository": {"url": "https://github.com/AF-GRILL/DISPluginForUnreal", "commit": "def456"},
        "engine": {"version": "5.8"},
        "host": {"system": "Windows", "release": "11", "machine": "x86_64"},
        "scenario": {"map": "LoopbackBench", "traffic_mix": "100% Entity State"},
        "results": [
            {
                "scenario": "entity_state_100x30hz",
                "packets_received": 3000,
                "packets_parsed": 3000,
                "packets_accepted": 3000,
                "packets_rejected": 0,
                "malformed": 0,
                "socket_drops": 0,
                "queue_drops": 0,
                "p50_ingest_ms": 0.9,
                "p95_ingest_ms": 1.2,
                "p99_ingest_ms": 1.4,
                "steady_state_gc_bytes": 0,
                "main_thread_apply_ms": 0.4,
                "packets_per_sec": 98000,
            }
        ],
    }

    report = module.normalize_payload(payload, source_payload="verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json")

    assert report["surface"] == "grill_unreal"
    assert report["surface_kind"] == "competitor"
    assert report["summary"]["row_count"] == 1
    assert report["rows"][0]["scenario"] == "entity_state_100x30hz"
    assert report["rows"][0]["metrics"]["p95_ingest_ms"] == 1.2
    assert report["rows"][0]["truth"]["final_truth_match"] is None


def test_unity_grill_baseline_normalizer_cli_skips_missing_input(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_unity_grill_baseline.py"),
            "--input",
            str(tmp_path / "missing.json"),
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert "skip: missing" in result.stdout


def test_unreal_grill_baseline_normalizer_cli_writes_outputs(tmp_path: Path) -> None:
    input_path = tmp_path / "grill_unreal_benchmark_baseline.json"
    input_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.unreal_grill_benchmark_baseline.v1",
                "product": "GRILL DIS for Unreal",
                "captured_at_utc": "2026-06-26T00:00:00Z",
                "repository": {"url": "https://github.com/AF-GRILL/DISPluginForUnreal", "commit": "def456"},
                "engine": {"version": "5.8"},
                "host": {"system": "Windows", "release": "11", "machine": "x86_64"},
                "scenario": {"map": "LoopbackBench", "traffic_mix": "100% Entity State"},
                "results": [{"scenario": "entity_state_1x10hz", "p95_ingest_ms": 0.4, "main_thread_apply_ms": 0.1, "packets_per_sec": 1000}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_unreal_grill_baseline.py"),
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    json_path = out_dir / "grill_unreal_engine_benchmark_report.json"
    assert json_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["surface"] == "grill_unreal"
