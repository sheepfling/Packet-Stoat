from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_build_unity_cross_engine_equivalence_report(tmp_path: Path) -> None:
    json_out = tmp_path / "cross_engine.json"
    md_out = tmp_path / "cross_engine.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unity_cross_engine_equivalence_report.py"),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "complete"
    assert payload["metrics"]["language_rows"]["unity"]["deep_rows"] == 141
    assert "Unity Cross-Engine Equivalence" in md_out.read_text(encoding="utf-8")


def test_build_unity_head_to_head_benchmark_report_without_grill_baseline(tmp_path: Path) -> None:
    json_out = tmp_path / "benchmark.json"
    md_out = tmp_path / "benchmark.md"
    missing_grill = tmp_path / "missing_grill.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unity_head_to_head_benchmark_report.py"),
            "--grill",
            str(missing_grill),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1, result.stdout
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "incomplete"
    assert payload["inputs"]["fastdis_exists"] is True
    assert payload["inputs"]["fastdis_valid"] is True
    assert payload["inputs"]["grill_exists"] is False
    assert payload["inputs"]["grill_valid"] is False
    assert payload["inputs"]["grill_template_exists"] is True
    assert "capture contract" in payload["note"]
    assert "Unity Head-to-Head Benchmark Readiness" in md_out.read_text(encoding="utf-8")


def test_build_unity_head_to_head_benchmark_report_rejects_invalid_grill_baseline(tmp_path: Path) -> None:
    json_out = tmp_path / "benchmark.json"
    md_out = tmp_path / "benchmark.md"
    invalid_grill = tmp_path / "grill.json"
    invalid_grill.write_text('{"schema":"wrong","product":"GRILL DIS for Unity","results":[]}\n', encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unity_head_to_head_benchmark_report.py"),
            "--grill",
            str(invalid_grill),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1, result.stdout
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "incomplete"
    assert payload["inputs"]["grill_exists"] is True
    assert payload["inputs"]["grill_valid"] is False
    assert payload["validation"]["grill_errors"]
    assert "schema" in payload["validation"]["grill_errors"][0]
    assert "grill_error" in md_out.read_text(encoding="utf-8")


def test_build_unity_head_to_head_benchmark_report_accepts_valid_grill_baseline(tmp_path: Path) -> None:
    json_out = tmp_path / "benchmark.json"
    md_out = tmp_path / "benchmark.md"
    grill = tmp_path / "grill.json"
    grill.write_text(
        json.dumps(
            {
                "schema": "fastdis.unity_grill_benchmark_baseline.v1",
                "product": "GRILL DIS for Unity",
                "captured_at_utc": "2026-06-25T00:00:00Z",
                "repository": {
                    "url": "https://github.com/AF-GRILL/DISPluginForUnity",
                    "commit": "abc123",
                },
                "unity": {
                    "version": "6000.5.0f1",
                    "render_pipeline": "builtin",
                    "scripting_backend": "Mono",
                },
                "host": {
                    "system": "Windows",
                    "release": "11",
                    "machine": "x86_64",
                },
                "scenario": {
                    "scene": "LoopbackBench",
                    "traffic_mix": "100% Entity State",
                    "entity_counts": [1000],
                    "update_hz": [60],
                },
                "results": [
                    {
                        "case": "header_all_no_callback",
                        "entity_count": 1000,
                        "update_hz": 60,
                        "packets_per_sec": 100000,
                        "main_thread_ms_avg": 2.5,
                        "gc_alloc_bytes_per_frame": 0,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unity_head_to_head_benchmark_report.py"),
            "--grill",
            str(grill),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "complete"
    assert payload["inputs"]["grill_valid"] is True
    assert payload["grill_summary"]["result_count"] == 1
    assert payload["validation"]["grill_errors"] == []
    assert payload["comparison"]["matched_cases"] == 1
    assert payload["comparison"]["rows"][0]["case"] == "header_all_no_callback"
    assert payload["comparison"]["rows"][0]["ratios"]["packets_per_sec"] is not None
    assert "Matched Cases" in md_out.read_text(encoding="utf-8")
