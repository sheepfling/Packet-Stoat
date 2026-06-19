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


def _sample_native() -> dict:
    return {
        "abi": 8,
        "version": "0.13.0-alpha3",
        "results": [
            {
                "case": "header_all_no_callback",
                "packets": 1000,
                "rounds": 3,
                "best_ms": 1.0,
                "avg_ms": 1.1,
                "p50_ms": 1.1,
                "p95_ms": 1.19,
                "p99_ms": 1.198,
                "worst_ms": 1.2,
                "best_mpps": 1.0,
                "avg_mpps": 0.91,
                "seen": 1000,
                "malformed": 0,
                "accepted": 1000,
                "emitted": 1000,
                "round_ms": [1.0, 1.1, 1.2],
                "notes": "header baseline",
            },
            {
                "case": "entity_transform_to_batch",
                "packets": 1000,
                "rounds": 3,
                "best_ms": 2.0,
                "avg_ms": 2.1,
                "p50_ms": 2.1,
                "p95_ms": 2.19,
                "p99_ms": 2.198,
                "worst_ms": 2.2,
                "best_mpps": 0.5,
                "avg_mpps": 0.48,
                "seen": 1000,
                "malformed": 0,
                "accepted": 1000,
                "emitted": 1000,
                "round_ms": [2.0, 2.1, 2.2],
                "notes": "transform batch",
            },
            {
                "case": "frame_transform_off",
                "packets": 1000,
                "rounds": 3,
                "best_ms": 3.0,
                "avg_ms": 3.1,
                "p50_ms": 3.1,
                "p95_ms": 3.19,
                "p99_ms": 3.198,
                "worst_ms": 3.2,
                "best_mpps": 0.33,
                "avg_mpps": 0.32,
                "seen": 1000,
                "malformed": 0,
                "accepted": 1000,
                "emitted": 1000,
                "round_ms": [3.0, 3.1, 3.2],
                "notes": "frame off",
            },
            {
                "case": "frame_transform_on",
                "packets": 1000,
                "rounds": 3,
                "best_ms": 4.0,
                "avg_ms": 4.1,
                "p50_ms": 4.1,
                "p95_ms": 4.19,
                "p99_ms": 4.198,
                "worst_ms": 4.2,
                "best_mpps": 0.25,
                "avg_mpps": 0.24,
                "seen": 1000,
                "malformed": 0,
                "accepted": 1000,
                "emitted": 1000,
                "round_ms": [4.0, 4.1, 4.2],
                "notes": "frame on",
            },
        ],
    }


def _sample_ctypes() -> dict:
    return {
        "abi_version": 8,
        "library_version": "0.13.0-alpha3",
        "results": [
            {
                "case": "ctypes_header_no_callback",
                "packets": 1000,
                "repeats": 3,
                "best_ms": 10.0,
                "avg_ms": 11.0,
                "p50_ms": 11.0,
                "p95_ms": 11.9,
                "p99_ms": 11.98,
                "worst_ms": 12.0,
                "best_mpps": 0.10,
                "avg_mpps": 0.09,
                "mega_packets_per_sec": 0.09,
                "seen": 3000,
                "malformed": 0,
                "accepted": 3000,
                "emitted": 3000,
                "callbacks": 0,
                "round_ms": [10.0, 11.0, 12.0],
                "notes": "ctypes header baseline",
            },
            {
                "case": "ctypes_entity_transform_to_batch",
                "packets": 1000,
                "repeats": 3,
                "best_ms": 20.0,
                "avg_ms": 21.0,
                "p50_ms": 21.0,
                "p95_ms": 21.9,
                "p99_ms": 21.98,
                "worst_ms": 22.0,
                "best_mpps": 0.05,
                "avg_mpps": 0.048,
                "mega_packets_per_sec": 0.048,
                "seen": 3000,
                "malformed": 0,
                "accepted": 3000,
                "emitted": 3000,
                "callbacks": 0,
                "round_ms": [20.0, 21.0, 22.0],
                "notes": "ctypes transform batch",
            },
        ],
    }


def test_summarize_benchmarks_renders_latency_and_qualification(tmp_path: Path) -> None:
    module = _load_module("summarize_benchmarks", ROOT / "tools" / "summarize_benchmarks.py")
    native = _sample_native()
    ctypes = _sample_ctypes()

    text = module.render(native, ctypes)
    qualification = module.build_qualification(native, ctypes)

    assert "Qualification summary" in text
    assert "p95 ms" in text
    assert "Allocation expectations" in text
    assert qualification["summary"]["native_has_latency_quantiles"] is True
    assert qualification["summary"]["ctypes_has_latency_quantiles"] is True
    assert "frame_transform_on_vs_off" in qualification["native"]["ratios"]
    assert qualification["native"]["core_cases"]["header_scan"]["best_mpps"] == 1.0

    native_path = tmp_path / "native.json"
    ctypes_path = tmp_path / "ctypes.json"
    summary_path = tmp_path / "summary.md"
    qualification_path = tmp_path / "qualification.json"
    native_path.write_text(json.dumps(native) + "\n")
    ctypes_path.write_text(json.dumps(ctypes) + "\n")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "summarize_benchmarks.py"),
            "--native",
            str(native_path),
            "--ctypes",
            str(ctypes_path),
            "--out",
            str(summary_path),
            "--json-out",
            str(qualification_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Qualification summary" in summary_path.read_text()
    qualification_written = json.loads(qualification_path.read_text())
    assert qualification_written["summary"]["native_case_count"] == 4


def test_check_benchmark_regression_handles_combined_payloads(tmp_path: Path) -> None:
    baseline = {
        "native": _sample_native(),
        "ctypes": _sample_ctypes(),
    }
    current = json.loads(json.dumps(baseline))
    current["native"]["results"][0]["best_mpps"] = 0.70
    current["ctypes"]["results"][0]["best_mpps"] = 0.05
    current["ctypes"]["results"][0]["mega_packets_per_sec"] = 0.05

    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    baseline_path.write_text(json.dumps(baseline) + "\n")
    current_path.write_text(json.dumps(current) + "\n")

    failure = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "check_benchmark_regression.py"),
            str(baseline_path),
            str(current_path),
            "--max-regression-percent",
            "10",
        ],
        capture_output=True,
        text=True,
    )
    assert failure.returncode == 1
    assert "native:header_all_no_callback" in failure.stdout
    assert "ctypes:ctypes_header_no_callback" in failure.stdout

    success = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "check_benchmark_regression.py"),
            str(baseline_path),
            str(current_path),
            "--max-regression-percent",
            "40",
            "--only-case",
            "entity_transform_to_batch",
        ],
        capture_output=True,
        text=True,
    )
    assert success.returncode == 0
    assert "passed" in success.stdout
