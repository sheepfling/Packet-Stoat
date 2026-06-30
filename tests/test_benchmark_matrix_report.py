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


def _fixture(path: str) -> Path:
    return ROOT / path


def _validation_payload(status: str = "skipped") -> dict:
    return {
        "schema": "fastdis.competitor_capture_validation.v1",
        "bundle_root": ".",
        "manifest_schema": "fastdis.competitor_capture_manifest.v1",
        "status": status,
        "active_lane_count": 0 if status == "skipped" else 1,
        "errors": [],
        "handoff_workbench": {
            "schema": "fastdis.competitor_handoff_workbench_check.v1",
            "status": "pass" if status == "pass" else "fail",
            "summary": {
                "required_file_count": 1,
                "present_file_count": 1 if status == "pass" else 0,
                "missing_file_count": 0 if status == "pass" else 1,
                "checksum_mismatch_count": 0,
                "readme_present": True,
                "bundle_kind": "archive_bundle" if status == "pass" else "local_checkout",
                "self_describing_bundle": True if status == "pass" else False,
                "manifest_present": True if status == "pass" else False,
                "manifest_valid": True if status == "pass" else False,
            },
        },
        "lanes": [],
    }


def test_build_benchmark_matrix_report_summarizes_surfaces_and_claims() -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")

    engine_reports = [
        _fixture("tests/data/engine_benchmark_reports/fastdis_unreal.sample.json"),
        _fixture("tests/data/engine_benchmark_reports/grill_unreal.sample.json"),
    ]
    head_reports = [
        ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill.sample.json",
    ]
    status_report = ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json"
    validation_report = ROOT / "artifacts" / "reports" / "competitor_capture_validation.json"
    competitor_summary_report = ROOT / "artifacts" / "reports" / "competitor_lane_summary" / "competitor_lane_summary.json"
    cross_engine_report = ROOT / "artifacts" / "reports" / "cross_engine_equivalence.json"
    report = module.build_report(
        engine_reports,
        head_reports,
        [status_report] if status_report.exists() else [],
        [validation_report] if validation_report.exists() else [],
        competitor_summary_report if competitor_summary_report.exists() else None,
        [cross_engine_report] if cross_engine_report.exists() else [],
    )

    assert report["schema"] == "fastdis.engine_benchmark_matrix.v1"
    assert report["summary"]["surface_report_count"] == 2
    assert report["summary"]["comparison_report_count"] == 1
    assert report["summary"]["competitor_status_count"] in {0, 1}
    assert report["summary"]["competitor_validation_count"] in {0, 1}
    assert report["summary"]["cross_engine_equivalence_count"] in {0, 1}
    assert report["summary"]["supported_competitor_claim_count"] == 0
    assert any(row["surface"] == "unreal" for row in report["surfaces"])
    assert any(row["surface"] == "grill_unreal" for row in report["surfaces"])
    assert any(row["left_surface"] == "unreal" and row["supported_claim"] is False for row in report["comparisons"])
    unreal_comparison = next(row for row in report["comparisons"] if row["left_surface"] == "unreal")
    if competitor_summary_report.exists():
        assert unreal_comparison["claim_boundary_detail"]["route_scope"] == "current public GRILL Unreal source route"
    if cross_engine_report.exists():
        assert report["summary"]["complete_cross_engine_equivalence_count"] == 1
        assert report["cross_engine_equivalence"][0]["status"] == "complete"
    assert any("unreal vs grill" in gap for gap in report["gaps"])
    assert any("cpp benchmark report not present" == gap for gap in report["gaps"])
    assert any("unity" in gap for gap in report["gaps"])


def test_build_benchmark_matrix_report_cli_writes_outputs(tmp_path: Path) -> None:
    json_path = tmp_path / "benchmark_matrix.json"
    md_path = tmp_path / "benchmark_matrix.md"
    validation_path = tmp_path / "competitor_capture_validation.json"
    validation_path.write_text(json.dumps(_validation_payload()) + "\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_benchmark_matrix_report.py"),
            "--engine-report",
            str(ROOT / "tests" / "data" / "engine_benchmark_reports" / "fastdis_unreal.sample.json"),
            "--engine-report",
            str(ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json"),
            "--head-to-head",
            str(ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill.sample.json"),
            "--competitor-status",
            str(ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json"),
            "--competitor-validation",
            str(validation_path),
            "--competitor-summary",
            str(ROOT / "artifacts" / "reports" / "competitor_lane_summary" / "competitor_lane_summary.json"),
            "--cross-engine-equivalence",
            str(ROOT / "artifacts" / "reports" / "cross_engine_equivalence.json"),
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
    assert payload["summary"]["comparison_report_count"] == 1
    assert payload["summary"]["competitor_status_count"] == 1
    assert payload["summary"]["competitor_validation_count"] == 1
    assert payload["summary"]["blocked_evidence_lane_count"] == 0
    assert payload["summary"]["cross_engine_equivalence_count"] == 1
    assert "Claim Boundaries" in md_path.read_text(encoding="utf-8")
    assert "validation_lane" in md_path.read_text(encoding="utf-8")
    assert "validation_passed" in md_path.read_text(encoding="utf-8")
    assert "route_scope:" in md_path.read_text(encoding="utf-8")


def test_preferred_default_engine_reports_prefers_current_over_sample(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    current = tmp_path / "unity_engine_benchmark_report.json"
    sample = tmp_path / "samples" / "unity_engine_benchmark_report.json"
    sample.parent.mkdir(parents=True, exist_ok=True)
    current.write_text("{}\n", encoding="utf-8")
    sample.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        module,
        "DEFAULT_ENGINE_REPORT_CANDIDATES",
        [
            [current, sample],
        ],
    )

    preferred = module.preferred_default_engine_reports()

    assert preferred == [current]


def test_preferred_default_head_to_head_reports_prefers_current_over_sample(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    current = tmp_path / "unreal_vs_grill.json"
    sample = tmp_path / "unreal_vs_grill.sample.json"
    current.write_text("{}\n", encoding="utf-8")
    sample.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        module,
        "DEFAULT_HEAD_TO_HEAD_CANDIDATES",
        [
            [current, sample],
        ],
    )

    preferred = module.preferred_default_head_to_head_reports()

    assert preferred == [current]


def test_head_to_head_summary_marks_sample_when_current_output_uses_sample_input(tmp_path: Path) -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    path = tmp_path / "unreal_vs_grill.json"
    payload = {
        "inputs": {
            "left": "artifacts/reports/engine_benchmarks/unreal_engine_benchmark_report.json",
            "right": "tests/data/engine_benchmark_reports/grill_unreal.sample.json",
            "left_surface": "unreal",
            "right_surface": "grill_unreal",
        },
        "comparison": {
            "same_host": True,
            "matched_scenarios": 1,
            "comparable_metric_rows": 1,
            "claim_boundaries": [],
        },
        "status": "comparable",
    }

    row = module.summarize_head_to_head_report(path, payload)

    assert row["evidence_kind"] == "sample"
    assert row["supported_claim"] is False


def test_head_to_head_summary_marks_blocked_lane_as_blocked_not_sample(tmp_path: Path) -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    path = tmp_path / "unreal_vs_grill.json"
    payload = {
        "inputs": {
            "left": "artifacts/reports/engine_benchmarks/unreal_engine_benchmark_report.json",
            "right": "tests/data/engine_benchmark_reports/grill_unreal.sample.json",
            "left_surface": "unreal",
            "right_surface": "grill_unreal",
        },
        "comparison": {
            "same_host": False,
            "matched_scenarios": 0,
            "comparable_metric_rows": 0,
            "claim_boundaries": [],
        },
        "status": "blocked_on_competitor",
    }

    row = module.summarize_head_to_head_report(path, payload)

    assert row["evidence_kind"] == "blocked"
    assert row["supported_claim"] is False


def test_summaries_preserve_optional_proof_context() -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    engine_payload = {
        "surface": "unity",
        "surface_kind": "engine",
        "rows": [],
        "host": {"system": "Darwin"},
        "proof_context": {
            "schema": "fastdis.proof_context.v1",
            "evidence_class": "truth_backed_bridge",
            "comparison_axis": "engine_adapter",
            "host": {"system": "Darwin"},
            "platform": {"os": "macos", "arch": "arm64"},
            "qualification": {"claim_boundary": "verification-first route", "comparable": False}
        },
    }
    surface_row = module.summarize_engine_report(ROOT / "surface.json", engine_payload)
    assert surface_row["proof_context"]["schema"] == "fastdis.proof_context.v1"

    comparison_payload = {
        "inputs": {
            "left": "left.json",
            "right": "right.json",
            "left_surface": "unity",
            "right_surface": "grill_unity",
            "left_proof_context": {
                "schema": "fastdis.proof_context.v1",
                "evidence_class": "direct_measured",
                "comparison_axis": "engine_adapter",
                "host": {"system": "Darwin"},
                "platform": {"os": "macos", "arch": "arm64"},
                "qualification": {"claim_boundary": "same host measured row", "comparable": True}
            },
            "right_proof_context": {
                "schema": "fastdis.proof_context.v1",
                "evidence_class": "same_host_competitor",
                "comparison_axis": "competitor_same_host",
                "host": {"system": "Darwin"},
                "platform": {"os": "macos", "arch": "arm64"},
                "qualification": {"claim_boundary": "same host competitor row", "comparable": True}
            }
        },
        "comparison": {
            "same_host": True,
            "matched_scenarios": 1,
            "comparable_metric_rows": 1,
            "claim_boundaries": [],
        },
        "status": "comparable",
    }
    comparison_row = module.summarize_head_to_head_report(ROOT / "comparison.json", comparison_payload)
    assert comparison_row["left_proof_context"]["schema"] == "fastdis.proof_context.v1"
    assert comparison_row["right_proof_context"]["comparison_axis"] == "competitor_same_host"


def test_apply_competitor_validation_requires_passing_lane_validation() -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    comparison_rows = [
        {
            "left_surface": "unreal",
            "right_surface": "grill_unreal",
            "supported_claim": True,
        },
        {
            "left_surface": "unity",
            "right_surface": "grill_unity",
            "supported_claim": True,
        },
    ]
    competitor_validation_rows = [
        {
            "status": "pass",
            "handoff_workbench_status": "pass",
            "handoff_bundle_kind": "archive_bundle",
            "handoff_self_describing_bundle": True,
            "lanes": [
                {"lane": "unreal_vs_grill", "present": True, "error_count": 0, "artifact_mode": "benchmark_capture"},
                {"lane": "unity_vs_grill", "present": True, "error_count": 1, "artifact_mode": "benchmark_capture"},
            ],
        }
    ]
    competitor_summary = {
        "lanes": [
            {
                "lane": "unreal_vs_grill",
                "claim_boundary": {
                    "route_scope": "current public GRILL Unreal source route",
                    "gap_summary": "The current public GRILL Unreal route is source-available but Windows-only on the checked-in plugin path.",
                    "testing_workaround": "Capture GRILL Unreal on a Windows host, or keep a private Mac/Linux port clearly labeled as internal-only research.",
                    "safe_advertising_point": "FastDIS publishes route-scoped failure evidence and broader host/build proof, while the current public GRILL Unreal route remains Windows-only.",
                    "publishable_today": True,
                    "non_publishable_angle": "Do not claim direct Unreal head-to-head performance wins until a same-host GRILL capture exists.",
                }
            }
        ]
    }

    adjusted = module.apply_competitor_validation(comparison_rows, competitor_validation_rows, competitor_summary)

    rows = {(row["left_surface"], row["right_surface"]): row for row in adjusted}
    assert rows[("unreal", "grill_unreal")]["supported_claim"] is True
    assert rows[("unreal", "grill_unreal")]["validation_passed"] is True
    assert rows[("unreal", "grill_unreal")]["claim_boundary_detail"]["route_scope"] == "current public GRILL Unreal source route"
    assert rows[("unity", "grill_unity")]["supported_claim"] is False
    assert rows[("unity", "grill_unity")]["validation_passed"] is False


def test_apply_competitor_validation_requires_self_describing_archive_bundle() -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    comparison_rows = [
        {
            "left_surface": "unreal",
            "right_surface": "grill_unreal",
            "supported_claim": True,
        },
    ]
    competitor_validation_rows = [
        {
            "status": "pass",
            "handoff_workbench_status": "pass",
            "handoff_bundle_kind": "local_checkout",
            "handoff_self_describing_bundle": False,
            "lanes": [
                {"lane": "unreal_vs_grill", "present": True, "error_count": 0},
            ],
        }
    ]

    adjusted = module.apply_competitor_validation(comparison_rows, competitor_validation_rows)

    assert adjusted[0]["validation_passed"] is False
    assert adjusted[0]["supported_claim"] is False


def test_summarize_competitor_validation_report_counts_blocked_evidence_lanes(tmp_path: Path) -> None:
    module = _load_module("build_benchmark_matrix_report", ROOT / "tools" / "build_benchmark_matrix_report.py")
    payload = {
        "schema": "fastdis.competitor_capture_validation.v1",
        "status": "skipped",
        "active_lane_count": 0,
        "errors": [],
        "handoff_workbench": {
            "status": "pass",
            "summary": {
                "bundle_kind": "local_checkout",
                "self_describing_bundle": False,
                "manifest_present": False,
            },
        },
        "lanes": [
            {"lane": "unreal_vs_grill", "present": False, "artifact_mode": "blocked_evidence_only", "shared_scenarios": [], "errors": []},
            {"lane": "unity_vs_grill", "present": False, "artifact_mode": "blocked_evidence_only", "shared_scenarios": [], "errors": []},
        ],
    }

    row = module.summarize_competitor_validation_report(tmp_path / "validation.json", payload)

    assert row["blocked_evidence_lane_count"] == 2
    assert row["lanes"][0]["artifact_mode"] == "blocked_evidence_only"
