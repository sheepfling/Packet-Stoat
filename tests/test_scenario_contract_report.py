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


def test_build_scenario_contract_report_marks_bridge_only_and_partial(tmp_path: Path) -> None:
    module = _load_module("build_scenario_contract_report", ROOT / "tools" / "build_scenario_contract_report.py")
    matrix = {
        "surfaces": [
            {"surface": "native", "scenarios": ["entity_state_1x10hz", "entity_state_100x30hz"]},
            {"surface": "c", "scenarios": ["c_localhost_udp_ingest_truth"]},
            {"surface": "cpp", "scenarios": ["entity_state_1x10hz"]},
            {"surface": "python_ctypes", "scenarios": ["entity_state_1x10hz", "python_only_case"]},
            {"surface": "unreal", "scenarios": ["unreal_proof_verification"]},
            {"surface": "unity", "scenarios": ["entity_state_1x10hz"]},
            {"surface": "godot", "scenarios": ["entity_state_1x10hz", "godot_demo_runtime"]},
        ]
    }
    scenarios = {
        "scenarios": [
            {"name": "entity_state_1x10hz"},
            {"name": "entity_state_100x30hz"},
            {"name": "filter_reject_90pct"},
        ]
    }
    aliases = {
        "aliases": [
            {
                "surface": "c",
                "observed": "c_localhost_udp_ingest_truth",
                "canonical": "entity_state_1x10hz",
                "alignment": "equivalent",
                "reason": "Test-only equivalence row.",
            },
            {
                "surface": "unreal",
                "observed": "unreal_proof_verification",
                "canonical": "entity_state_1x10hz",
                "alignment": "family",
                "reason": "Test-only family row.",
            },
        ]
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "scenarios.json",
        scenarios,
        tmp_path / "aliases.json",
        aliases,
    )

    assert report["schema"] == "fastdis.scenario_contract_report.v1"
    assert report["status"] == "partial"
    assert report["summary"]["canonical_scenario_count"] == 3
    assert report["summary"]["alias_equivalent_surface_count"] == 1
    assert report["summary"]["family_aligned_surface_count"] == 1
    c_row = next(row for row in report["surfaces"] if row["surface"] == "c")
    native_row = next(row for row in report["surfaces"] if row["surface"] == "native")
    unreal_row = next(row for row in report["surfaces"] if row["surface"] == "unreal")
    assert c_row["status"] == "alias_equivalent"
    assert c_row["alias_equivalent_matches"] == ["entity_state_1x10hz"]
    assert unreal_row["status"] == "family_aligned"
    assert unreal_row["family_alignments"] == ["entity_state_1x10hz"]
    assert native_row["status"] == "partial"
    assert "no canonical scenario name is currently shared across every required surface" in report["gaps"][-1]


def test_scenario_contract_report_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(tmp_path / "benchmark_matrix.json", {"surfaces": [{"surface": "native", "scenarios": ["entity_state_1x10hz"]}]})
    scenarios_path = _write(tmp_path / "scenarios.json", {"scenarios": [{"name": "entity_state_1x10hz"}]})
    json_out = tmp_path / "out" / "scenario_contract_report.json"
    md_out = tmp_path / "out" / "scenario_contract_report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_scenario_contract_report.py"),
            "--matrix",
            str(matrix_path),
            "--scenarios",
            str(scenarios_path),
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
    assert payload["schema"] == "fastdis.scenario_contract_report.v1"
    assert payload["sources"]["scenario_aliases"].endswith("core_matrix_aliases.v1.json")
    assert "Scenario Contract Report" in md_out.read_text(encoding="utf-8")


def test_scenario_contract_report_marks_canonical_names_present_but_unverified(tmp_path: Path) -> None:
    module = _load_module("build_scenario_contract_report", ROOT / "tools" / "build_scenario_contract_report.py")
    matrix = {
        "surfaces": [
            {"surface": "native", "scenarios": ["entity_state_1x10hz"], "truth_supported_scenarios": ["entity_state_1x10hz"]},
            {"surface": "c", "scenarios": []},
            {"surface": "cpp", "scenarios": []},
            {"surface": "python_ctypes", "scenarios": []},
            {"surface": "unreal", "scenarios": []},
            {"surface": "unity", "scenarios": ["entity_state_1x10hz", "entity_state_100x30hz"], "truth_supported_scenarios": []},
            {"surface": "godot", "scenarios": []},
        ]
    }
    scenarios = {
        "scenarios": [
            {"name": "entity_state_1x10hz"},
            {"name": "entity_state_100x30hz"},
        ]
    }
    aliases = {"aliases": []}

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "scenarios.json",
        scenarios,
        tmp_path / "aliases.json",
        aliases,
    )

    unity_row = next(row for row in report["surfaces"] if row["surface"] == "unity")
    assert unity_row["status"] == "canonical_present_unverified"
    assert unity_row["canonical_observed_matches"] == ["entity_state_1x10hz", "entity_state_100x30hz"]
    assert unity_row["canonical_matches"] == []
    assert any("unity publishes 2 exact canonical scenario names" in gap for gap in report["gaps"])
