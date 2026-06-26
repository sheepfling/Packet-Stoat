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


def test_build_cross_engine_equivalence_report_cli(tmp_path: Path) -> None:
    json_out = tmp_path / "cross_engine_equivalence.json"
    md_out = tmp_path / "cross_engine_equivalence.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_cross_engine_equivalence_report.py"),
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
    assert payload["summary"]["deep_complete"] is True
    assert payload["summary"]["runtime_truth_complete"] is True
    assert payload["deep_surfaces"]["cpp"]["deep_rows"] == 141
    assert any(row["surface"] == "unity" and row["verified_truth_rows"] >= 1 for row in payload["benchmark_surfaces"])
    assert "Cross-Engine Equivalence" in md_out.read_text(encoding="utf-8")


def test_build_cross_engine_equivalence_report_marks_missing_runtime_truth_partial() -> None:
    module = _load_module("build_cross_engine_equivalence_report", ROOT / "tools" / "build_cross_engine_equivalence_report.py")

    unity_equivalence_payload = {
        "status": "complete",
        "metrics": {
            "language_rows": {
                surface: {"catalog_rows": 141, "deep_rows": 141}
                for surface in ("c", "cpp", "python", "unreal", "godot", "unity")
            }
        },
    }
    engine_payloads = {
        "native": (ROOT / "native.json", {"rows": [{"truth": {"final_truth_match": None}}], "source_schema": "native"}),
        "python": (ROOT / "python.json", {"rows": [{"truth": {"final_truth_match": None}}], "source_schema": "python"}),
        "unreal": (ROOT / "unreal.json", {"rows": [{"truth": {"final_truth_match": True}}], "source_schema": "unreal"}),
        "godot": (ROOT / "godot.json", {"rows": [{"truth": {"final_truth_match": False}}], "source_schema": "godot"}),
        "unity": (ROOT / "unity.json", {"rows": [{"truth": {"final_truth_match": True}}], "source_schema": "unity"}),
    }

    report = module.build_report(unity_equivalence_payload, ROOT / "unity_equivalence.json", engine_payloads)

    assert report["status"] == "partial"
    assert report["summary"]["deep_complete"] is True
    assert report["summary"]["runtime_truth_complete"] is False
    assert any("godot" in gap for gap in report["gaps"])
