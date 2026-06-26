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


def _load_fixture(name: str) -> dict:
    path = ROOT / "tests" / "data" / "engine_benchmark_reports" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_engine_head_to_head_comparable_same_host() -> None:
    module = _load_module("run_engine_head_to_head_matrix", ROOT / "tools" / "run_engine_head_to_head_matrix.py")
    left = _load_fixture("fastdis_unreal.sample.json")
    right = _load_fixture("grill_unreal.sample.json")

    report = module.build_report(
        left,
        right,
        left_path=ROOT / "tests" / "data" / "engine_benchmark_reports" / "fastdis_unreal.sample.json",
        right_path=ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json",
        left_label="FastDIS Unreal",
        right_label="GRILL Unreal",
    )

    assert report["schema"] == "fastdis.engine_head_to_head_report.v1"
    assert report["status"] == "comparable"
    assert report["comparison"]["same_host"] is True
    assert report["comparison"]["matched_scenarios"] == 2
    assert report["comparison"]["comparable_metric_rows"] == 2
    first = report["comparison"]["rows"][0]
    assert first["metrics"]["packets_per_sec"]["ratio"] is not None
    assert first["metrics"]["p95_ingest_ms"]["ratio"] is not None
    assert first["metrics"]["packets_accepted"]["equal"] is True


def test_engine_head_to_head_marks_host_mismatch_directional_only(tmp_path: Path) -> None:
    module = _load_module("run_engine_head_to_head_matrix", ROOT / "tools" / "run_engine_head_to_head_matrix.py")
    left = _load_fixture("fastdis_unreal.sample.json")
    right = _load_fixture("grill_unreal.sample.json")
    right["host"]["machine"] = "x86_64"

    report = module.build_report(
        left,
        right,
        left_path=tmp_path / "left.json",
        right_path=tmp_path / "right.json",
        left_label="FastDIS Unreal",
        right_label="GRILL Unreal",
    )

    assert report["status"] == "directional_only"
    assert report["comparison"]["same_host"] is False
    assert any("same-host" in note or "same-host evidence" in note for note in report["comparison"]["claim_boundaries"])


def test_engine_head_to_head_cli_writes_reports(tmp_path: Path) -> None:
    left_path = ROOT / "tests" / "data" / "engine_benchmark_reports" / "fastdis_unreal.sample.json"
    right_path = ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json"
    json_path = tmp_path / "head_to_head.json"
    md_path = tmp_path / "head_to_head.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "run_engine_head_to_head_matrix.py"),
            "--left",
            str(left_path),
            "--right",
            str(right_path),
            "--json-out",
            str(json_path),
            "--md-out",
            str(md_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "comparable"
    assert payload["comparison"]["matched_scenarios"] == 2
    assert "Claim Boundaries" in md_path.read_text(encoding="utf-8")
