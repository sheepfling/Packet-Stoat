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


def test_build_benchmark_claim_summary_marks_supported_and_blocked_claims(tmp_path: Path) -> None:
    module = _load_module("build_benchmark_claim_summary", ROOT / "tools" / "build_benchmark_claim_summary.py")
    matrix = {
        "summary": {"blocked_evidence_lane_count": 2},
        "claim_boundaries": ["same-host only", "no sample claims"],
        "surfaces": [
            {"surface": "native", "surface_kind": "native", "evidence_kind": "measured", "row_count": 4, "latency_rows": 4, "runtime_metric_rows": 0, "truth_rows": 0, "path": "artifacts/reports/engine_benchmarks/native_engine_benchmark_report.json"},
            {"surface": "unreal", "surface_kind": "engine", "evidence_kind": "measured_or_verified", "row_count": 2, "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 2, "path": "artifacts/reports/engine_benchmarks/unreal_engine_benchmark_report.json"},
        ],
        "comparisons": [
            {"left_surface": "unreal", "right_surface": "grill_unreal", "supported_claim": True, "path": "artifacts/reports/engine_head_to_head/unreal_vs_grill.json"},
            {"left_surface": "unity", "right_surface": "grill_unity", "supported_claim": False, "path": "artifacts/reports/engine_head_to_head/unity_vs_grill.json"},
        ],
        "competitor_validations": [
            {"lanes": [{"lane": "unreal_vs_grill", "artifact_mode": "blocked_evidence_only"}, {"lane": "unity_vs_grill", "artifact_mode": "blocked_evidence_only"}]}
        ],
    }
    audit = {
        "requirements": [
            {"id": "shared_contract", "status": "partial", "title": "Shared contract", "gaps": ["native overlaps 2 canonical scenario families, but does not yet publish exact shared scenario names", "canonical scenario names are not shared across every required surface"], "evidence": ["artifacts/reports/benchmark_matrix/benchmark_matrix.json", "artifacts/reports/scenario_contract/scenario_contract_report.json"]},
            {"id": "ingest_filter_latest_state", "status": "complete", "title": "Core coverage", "gaps": [], "evidence": ["artifacts/reports/benchmark_coverage/benchmark_coverage_report.json"]},
            {"id": "replay_reports", "status": "complete", "title": "Replay coverage", "gaps": [], "evidence": ["artifacts/reports/benchmark_coverage/benchmark_coverage_report.json"]},
            {"id": "cross_engine_equivalence", "status": "complete", "title": "Cross-engine equivalence", "gaps": [], "evidence": ["artifacts/reports/cross_engine_equivalence.json"]},
            {"id": "engine_runtime_reports", "status": "complete", "title": "Engine runtime reports", "gaps": [], "evidence": ["artifacts/reports/benchmark_matrix/benchmark_matrix.json"]},
            {"id": "unreal_competitor", "status": "complete", "title": "Unreal competitor", "gaps": [], "evidence": ["artifacts/reports/engine_head_to_head/unreal_vs_grill.json"]},
            {"id": "unity_competitor", "status": "blocked", "title": "Honest same-host Unity FastDIS-vs-GRILL head-to-head report", "gaps": ["no current GRILL Unity shared benchmark report present"], "evidence": ["artifacts/reports/engine_head_to_head/unity_vs_grill_status.json"]},
        ],
        "next_steps": ["Capture a current GRILL Unity shared benchmark report on a GRILL-compatible host and rerun the shared comparator."],
    }
    coverage = {
        "summary": {
            "ingest": {"surface_count": 7},
            "filtering": {"surface_count": 2},
            "latest_state": {"surface_count": 4},
            "replay": {"surface_count": 2},
        }
    }
    competitor_summary = {
        "lanes": [
            {
                "lane": "unity_vs_grill",
                "current_state": "blocked_evidence_only",
                "claim_boundary": {
                    "route_scope": "current public GRILL Unity source/package route",
                    "gap_summary": "The current public GRILL Unity route is source-available but import-blocked on the current Mac host and Unity editor combination.",
                    "testing_workaround": "Capture GRILL Unity on a Unity host/editor combination that successfully imports the public plugin or example project.",
                    "safe_advertising_point": "FastDIS publishes install smoke and failure artifacts for competitor routes instead of hand-waving over importability gaps.",
                    "publishable_today": True,
                    "non_publishable_angle": "Do not claim direct Unity head-to-head performance wins until a same-host or clearly comparable-host GRILL capture exists.",
                },
            }
        ]
    }

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        matrix,
        tmp_path / "benchmark_coverage_report.json",
        coverage,
        tmp_path / "benchmark_completion_audit.json",
        audit,
        tmp_path / "competitor_lane_summary.json",
        competitor_summary,
    )

    assert report["schema"] == "fastdis.benchmark_claim_summary.v1"
    assert report["status"] == "publishable_partial"
    assert report["summary"]["publishable_claim_count"] >= 5
    assert report["summary"]["blocked_claim_count"] == 2
    assert report["summary"]["blocked_evidence_lane_count"] == 2
    assert any("supported same-host direct competitor claim for unreal vs grill_unreal" in row["claim"].lower() for row in report["publishable_today"])
    assert any("reproducible ingest, filtering, and latest-state" in row["claim"].lower() for row in report["publishable_today"])
    assert any("explicit replay benchmark coverage" in row["claim"].lower() for row in report["publishable_today"])
    shared_contract_row = next(row for row in report["not_publishable_yet"] if "canonical shared benchmark scenario contract" in row["claim"])
    unity_row = next(row for row in report["not_publishable_yet"] if row["claim"] == "Honest same-host Unity FastDIS-vs-GRILL head-to-head report")
    assert shared_contract_row["status"] == "partial"
    assert "canonical scenario names are not shared" in shared_contract_row["gaps"][-1]
    assert "scenario-family overlap" in shared_contract_row["safe_advertising_point"]
    assert "some surfaces now overlap canonical scenario families" in shared_contract_row["gap_summary"]
    assert unity_row["status"] == "blocked"
    assert unity_row["blocked_evidence_available"] is True
    assert unity_row["route_scope"] == "current public GRILL Unity source/package route"
    assert "import-blocked on the current Mac host" in unity_row["gap_summary"]
    assert report["claim_boundaries"] == ["same-host only", "no sample claims"]
    assert report["sources"]["matrix"].endswith("benchmark_matrix.json")
    assert report["sources"]["coverage"].endswith("benchmark_coverage_report.json")
    assert report["sources"]["audit"].endswith("benchmark_completion_audit.json")
    assert report["sources"]["competitor_summary"].endswith("competitor_lane_summary.json")


def test_benchmark_claim_summary_uses_measured_competitor_lane_when_matrix_is_stale(tmp_path: Path) -> None:
    module = _load_module("build_benchmark_claim_summary", ROOT / "tools" / "build_benchmark_claim_summary.py")
    matrix = {
        "summary": {"blocked_evidence_lane_count": 1},
        "claim_boundaries": ["same-host only"],
        "surfaces": [],
        "comparisons": [
            {"left_surface": "unity", "right_surface": "grill_unity", "supported_claim": False, "path": "artifacts/reports/engine_head_to_head/unity_vs_grill.json"},
        ],
        "competitor_validations": [
            {"lanes": [{"lane": "unity_vs_grill", "artifact_mode": "benchmark_capture"}]}
        ],
    }
    audit = {
        "requirements": [
            {"id": "unity_competitor", "status": "blocked", "title": "Honest same-host Unity FastDIS-vs-GRILL head-to-head report", "gaps": ["stale audit"], "evidence": ["artifacts/reports/engine_head_to_head/unity_vs_grill_status.json"]},
        ],
        "next_steps": [],
    }
    coverage = {"summary": {}}
    competitor_summary = {
        "lanes": [
            {
                "lane": "unity_vs_grill",
                "current_state": "measured_claim_ready",
                "comparison": {"path": "artifacts/reports/engine_head_to_head/unity_vs_grill.json"},
                "baseline_status": {"path": "artifacts/reports/engine_head_to_head/unity_vs_grill_status.json"},
                "claim_boundary": {
                    "route_scope": "current public GRILL Unity source/package route",
                    "gap_summary": "The current public GRILL Unity route imports and compares directly on the checked Mac/Unity host.",
                    "testing_workaround": "Review the matched Unity comparison rows and publish only the claims supported by the same-host report.",
                    "safe_advertising_point": "FastDIS now has same-host public-route Unity comparison evidence and can publish proof-backed competitor claims.",
                    "publishable_today": True,
                    "non_publishable_angle": None,
                },
            }
        ]
    }

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        matrix,
        tmp_path / "benchmark_coverage_report.json",
        coverage,
        tmp_path / "benchmark_completion_audit.json",
        audit,
        tmp_path / "competitor_lane_summary.json",
        competitor_summary,
    )

    assert any(row["claim"] == "Honest same-host Unity FastDIS-vs-GRILL head-to-head report" for row in report["publishable_today"])
    assert not any(row["claim"] == "Honest same-host Unity FastDIS-vs-GRILL head-to-head report" for row in report["not_publishable_yet"])
    assert report["summary"]["supported_competitor_claim_count"] == 1


def test_benchmark_claim_summary_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {
            "summary": {"blocked_evidence_lane_count": 0},
            "claim_boundaries": ["same-host only"],
            "surfaces": [],
            "comparisons": [],
        },
    )
    coverage_path = _write(
        tmp_path / "benchmark_coverage_report.json",
        {
            "summary": {
                "ingest": {"surface_count": 1},
                "filtering": {"surface_count": 1},
                "latest_state": {"surface_count": 0},
                "replay": {"surface_count": 0},
            }
        },
    )
    audit_path = _write(
        tmp_path / "benchmark_completion_audit.json",
        {
            "requirements": [],
            "next_steps": [],
        },
    )
    competitor_summary_path = _write(
        tmp_path / "competitor_lane_summary.json",
        {"lanes": []},
    )
    json_out = tmp_path / "out" / "benchmark_claim_summary.json"
    md_out = tmp_path / "out" / "benchmark_claim_summary.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_benchmark_claim_summary.py"),
            "--matrix",
            str(matrix_path),
            "--coverage",
            str(coverage_path),
            "--audit",
            str(audit_path),
            "--competitor-summary",
            str(competitor_summary_path),
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
    assert json_out.is_file()
    assert md_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.benchmark_claim_summary.v1"
    markdown = md_out.read_text(encoding="utf-8")
    assert "Publishable Today" in markdown
    assert "Not Publishable Yet" in markdown
