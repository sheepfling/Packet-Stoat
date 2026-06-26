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


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_build_surface_claim_report_emits_safe_claims_and_boundaries(tmp_path: Path) -> None:
    module = _load_module("build_surface_claim_report", ROOT / "tools" / "build_surface_claim_report.py")
    matrix = {
        "surfaces": [
            {"surface": "native", "surface_kind": "native", "evidence_kind": "measured", "path": "native.json", "latency_rows": 4, "runtime_metric_rows": 0, "truth_rows": 0},
            {"surface": "unity", "surface_kind": "engine", "evidence_kind": "measured_or_verified", "path": "unity.json", "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 3},
        ]
    }
    coverage = {
        "surfaces": [
            {"surface": "native", "capabilities": {"ingest": {"covered": True}, "filtering": {"covered": True}, "latest_state": {"covered": True}, "replay": {"covered": False}, "engine_runtime": {"covered": False}}},
            {"surface": "unity", "capabilities": {"ingest": {"covered": True}, "filtering": {"covered": False}, "latest_state": {"covered": True}, "replay": {"covered": True}, "engine_runtime": {"covered": True}}},
        ]
    }

    report = module.build_report(tmp_path / "matrix.json", matrix, tmp_path / "coverage.json", coverage)

    assert report["schema"] == "fastdis.surface_claim_report.v1"
    assert report["surface_count"] == 2
    native = next(row for row in report["surfaces"] if row["surface"] == "native")
    unity = next(row for row in report["surfaces"] if row["surface"] == "unity")
    assert any("published filtering" in claim.lower() for claim in native["safe_claims"])
    assert any("do not claim explicit replay benchmark coverage" in boundary.lower() for boundary in native["boundaries"])
    assert any("truth-backed verification" in claim.lower() for claim in unity["safe_claims"])
    assert any("do not claim explicit filtering" in boundary.lower() for boundary in unity["boundaries"])


def test_surface_claim_report_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {
            "surfaces": [
                {"surface": "native", "surface_kind": "native", "evidence_kind": "measured", "path": "native.json", "latency_rows": 1, "runtime_metric_rows": 0, "truth_rows": 0},
            ]
        },
    )
    coverage_path = _write(
        tmp_path / "benchmark_coverage_report.json",
        {
            "surfaces": [
                {"surface": "native", "capabilities": {"ingest": {"covered": True}, "filtering": {"covered": True}, "latest_state": {"covered": False}, "replay": {"covered": False}, "engine_runtime": {"covered": False}}},
            ]
        },
    )
    json_out = tmp_path / "out" / "surface_claim_report.json"
    md_out = tmp_path / "out" / "surface_claim_report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_surface_claim_report.py"),
            "--matrix",
            str(matrix_path),
            "--coverage",
            str(coverage_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.surface_claim_report.v1"
    assert "Surface Claim Report" in md_out.read_text(encoding="utf-8")
