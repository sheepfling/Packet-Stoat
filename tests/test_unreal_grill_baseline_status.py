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


def test_build_unreal_grill_baseline_status_blocks_without_current_grill_report(tmp_path: Path) -> None:
    module = _load_module("build_unreal_grill_baseline_status", ROOT / "tools" / "build_unreal_grill_baseline_status.py")
    fastdis = tmp_path / "unreal_engine_benchmark_report.json"
    fastdis.write_text(
        json.dumps(
            {
                "schema": "fastdis.engine_benchmark_report.v1",
                "surface": "unreal",
                "rows": [{"scenario": "unreal_proof_verification", "metrics": {}, "truth": {"final_truth_match": True}}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    sample_grill = tmp_path / "grill_unreal.sample.json"
    sample_grill.write_text("{}\n", encoding="utf-8")
    source_smoke = tmp_path / "grill_unreal_source_smoke.json"
    source_smoke.write_text(json.dumps({"status": "blocked-host-platform"}) + "\n", encoding="utf-8")
    mapping_export = tmp_path / "grill_mapping_export_report.json"
    mapping_export.write_text(json.dumps({"status": "missing-game-module", "failure_kind": "missing-game-module"}) + "\n", encoding="utf-8")
    mapping_materialize = tmp_path / "grill_mapping_materialize_report.json"
    mapping_materialize.write_text(json.dumps({"status": "missing-game-module", "failure_kind": "missing-game-module"}) + "\n", encoding="utf-8")

    report = module.build_report(
        fastdis,
        source_smoke_path=source_smoke,
        mapping_export_path=mapping_export,
        mapping_materialize_path=mapping_materialize,
        grill_candidates=[sample_grill],
    )

    assert report["schema"] == "fastdis.unreal_grill_baseline_status.v1"
    assert report["status"] == "blocked_on_grill_baseline"
    assert any("no current GRILL Unreal" in blocker for blocker in report["blockers"])
    assert "current host GRILL Unreal source smoke failed" in report["blockers"]
    assert "current host GRILL Unreal mapping export failed" in report["blockers"]
    assert "current host GRILL Unreal mapping materialize failed" in report["blockers"]
    assert report["mapping_export"]["failure_kind"] == "missing-game-module"
    assert report["mapping_materialize"]["failure_kind"] == "missing-game-module"
    assert "cannot load its game module" in report["note"]
    assert report["grill_candidates"][0]["classification"] == "sample"


def test_build_unreal_grill_baseline_status_cli_writes_outputs(tmp_path: Path) -> None:
    fastdis = tmp_path / "unreal_engine_benchmark_report.json"
    fastdis.write_text(
        json.dumps(
            {
                "schema": "fastdis.engine_benchmark_report.v1",
                "surface": "unreal",
                "rows": [{"scenario": "unreal_proof_verification", "metrics": {}, "truth": {"final_truth_match": True}}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    sample_grill = tmp_path / "grill_unreal.sample.json"
    sample_grill.write_text("{}\n", encoding="utf-8")
    source_smoke = tmp_path / "grill_unreal_source_smoke.json"
    source_smoke.write_text(json.dumps({"status": "blocked-host-platform"}) + "\n", encoding="utf-8")
    mapping_export = tmp_path / "grill_mapping_export_report.json"
    mapping_export.write_text(json.dumps({"status": "missing-game-module", "failure_kind": "missing-game-module"}) + "\n", encoding="utf-8")
    mapping_materialize = tmp_path / "grill_mapping_materialize_report.json"
    mapping_materialize.write_text(json.dumps({"status": "missing-game-module", "failure_kind": "missing-game-module"}) + "\n", encoding="utf-8")
    json_path = tmp_path / "status.json"
    md_path = tmp_path / "status.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unreal_grill_baseline_status.py"),
            "--fastdis",
            str(fastdis),
            "--grill-report",
            str(sample_grill),
            "--source-smoke",
            str(source_smoke),
            "--mapping-export",
            str(mapping_export),
            "--mapping-materialize",
            str(mapping_materialize),
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
    assert payload["status"] == "blocked_on_grill_baseline"
    assert payload["source_smoke"]["status"] == "blocked-host-platform"
    assert payload["mapping_export"]["failure_kind"] == "missing-game-module"
    assert "GRILL Candidates" in md_path.read_text(encoding="utf-8")
    assert "Mapping Export" in md_path.read_text(encoding="utf-8")
