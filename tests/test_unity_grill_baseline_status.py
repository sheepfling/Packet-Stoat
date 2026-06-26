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


def test_build_unity_grill_baseline_status_blocks_without_current_grill_report(tmp_path: Path) -> None:
    module = _load_module("build_unity_grill_baseline_status", ROOT / "tools" / "build_unity_grill_baseline_status.py")
    fastdis = tmp_path / "unity_engine_benchmark_report.json"
    fastdis.write_text(
        json.dumps(
            {
                "schema": "fastdis.engine_benchmark_report.v1",
                "surface": "unity",
                "rows": [{"scenario": "unity_runtime_verification", "metrics": {}, "truth": {"final_truth_match": True}}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    head_to_head = tmp_path / "unity_head_to_head_benchmark.json"
    head_to_head.write_text(json.dumps({"status": "incomplete", "note": "missing payload"}) + "\n", encoding="utf-8")
    import_smoke = tmp_path / "grill_unity_import_smoke.json"
    import_smoke.write_text(json.dumps({"status": "fail"}) + "\n", encoding="utf-8")
    template = tmp_path / "grill_unity_benchmark_baseline.template.json"
    template.write_text("{}\n", encoding="utf-8")

    report = module.build_report(
        fastdis,
        head_to_head_path=head_to_head,
        import_smoke_path=import_smoke,
        grill_candidates=[template],
    )

    assert report["schema"] == "fastdis.unity_grill_baseline_status.v1"
    assert report["status"] == "blocked_on_grill_baseline"
    assert any("no current GRILL Unity" in blocker for blocker in report["blockers"])
    assert any("import smoke failed" in blocker for blocker in report["blockers"])
    assert report["grill_candidates"][0]["classification"] == "template"


def test_build_unity_grill_baseline_status_cli_writes_outputs(tmp_path: Path) -> None:
    fastdis = tmp_path / "unity_engine_benchmark_report.json"
    fastdis.write_text(
        json.dumps(
            {
                "schema": "fastdis.engine_benchmark_report.v1",
                "surface": "unity",
                "rows": [{"scenario": "unity_runtime_verification", "metrics": {}, "truth": {"final_truth_match": True}}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    head_to_head = tmp_path / "unity_head_to_head_benchmark.json"
    head_to_head.write_text(json.dumps({"status": "incomplete", "note": "missing payload"}) + "\n", encoding="utf-8")
    import_smoke = tmp_path / "grill_unity_import_smoke.json"
    import_smoke.write_text(json.dumps({"status": "fail"}) + "\n", encoding="utf-8")
    template = tmp_path / "grill_unity_benchmark_baseline.template.json"
    template.write_text("{}\n", encoding="utf-8")
    json_path = tmp_path / "status.json"
    md_path = tmp_path / "status.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unity_grill_baseline_status.py"),
            "--fastdis",
            str(fastdis),
            "--head-to-head",
            str(head_to_head),
            "--import-smoke",
            str(import_smoke),
            "--grill-report",
            str(template),
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
    assert "GRILL Candidates" in md_path.read_text(encoding="utf-8")


def test_build_unity_grill_baseline_status_surfaces_host_startup_block(tmp_path: Path) -> None:
    module = _load_module("build_unity_grill_baseline_status", ROOT / "tools" / "build_unity_grill_baseline_status.py")
    fastdis = tmp_path / "unity_engine_benchmark_report.json"
    fastdis.write_text(
        json.dumps({"schema": "fastdis.engine_benchmark_report.v1", "surface": "unity", "rows": []}) + "\n",
        encoding="utf-8",
    )
    head_to_head = tmp_path / "unity_head_to_head_benchmark.json"
    head_to_head.write_text(json.dumps({"status": "incomplete", "note": "missing payload"}) + "\n", encoding="utf-8")
    import_smoke = tmp_path / "grill_unity_import_smoke.json"
    import_smoke.write_text(
        json.dumps({"status": "blocked-host-startup", "failure_stage": "host-startup"}) + "\n",
        encoding="utf-8",
    )

    report = module.build_report(
        fastdis,
        head_to_head_path=head_to_head,
        import_smoke_path=import_smoke,
        grill_candidates=[],
    )

    assert any("startup baseline failed" in blocker for blocker in report["blockers"])
    assert report["import_smoke"]["failure_stage"] == "host-startup"
    assert "Fix the current host Unity startup route" in report["next_steps"][0]


def test_build_unity_grill_baseline_status_prefers_live_comparator_when_available(tmp_path: Path) -> None:
    module = _load_module("build_unity_grill_baseline_status", ROOT / "tools" / "build_unity_grill_baseline_status.py")
    fastdis = tmp_path / "unity_engine_benchmark_report.json"
    fastdis.write_text(
        json.dumps({"schema": "fastdis.engine_benchmark_report.v1", "surface": "unity", "rows": [{"scenario": "entity_state_1x10hz", "metrics": {}, "truth": {"final_truth_match": False}}]}) + "\n",
        encoding="utf-8",
    )
    head_to_head = tmp_path / "unity_vs_grill.json"
    head_to_head.write_text(json.dumps({"status": "comparable", "note": "same-host comparable row present"}) + "\n", encoding="utf-8")
    import_smoke = tmp_path / "grill_unity_import_smoke.json"
    import_smoke.write_text(json.dumps({"status": "pass", "failure_stage": "none"}) + "\n", encoding="utf-8")
    grill = tmp_path / "grill_unity_engine_benchmark_report.json"
    grill.write_text(json.dumps({"schema": "fastdis.engine_benchmark_report.v1", "surface": "grill_unity", "rows": [{"scenario": "entity_state_1x10hz", "metrics": {}, "truth": {"final_truth_match": None}}]}) + "\n", encoding="utf-8")

    report = module.build_report(
        fastdis,
        head_to_head_path=head_to_head,
        import_smoke_path=import_smoke,
        grill_candidates=[grill],
    )

    assert report["status"] == "ready"
    assert report["head_to_head_readiness"]["status"] == "comparable"
    assert "Review the direct Unity-vs-GRILL comparison outputs" in report["next_steps"][0]
