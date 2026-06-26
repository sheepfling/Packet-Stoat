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


def test_build_competitor_lane_summary_reports_measured_and_blocked_lanes(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("build_competitor_lane_summary", ROOT / "tools" / "build_competitor_lane_summary.py")
    status_dir = tmp_path / "status"
    monkeypatch.setattr(
        module,
        "DEFAULT_STATUS_REPORTS",
        {
            "unreal_vs_grill": status_dir / "unreal_vs_grill_status.json",
            "unity_vs_grill": status_dir / "unity_vs_grill_status.json",
        },
    )

    matrix = {
        "comparisons": [
            {
                "left_surface": "unreal",
                "right_surface": "grill_unreal",
                "path": "build/reports/engine_head_to_head/unreal_vs_grill.json",
                "status": "comparable",
                "evidence_kind": "measured",
                "matched_scenarios": 4,
                "supported_claim": True,
                "validation_passed": True,
            },
            {
                "left_surface": "unity",
                "right_surface": "grill_unity",
                "path": "build/reports/engine_head_to_head/unity_vs_grill.json",
                "status": "blocked_on_competitor",
                "evidence_kind": "blocked",
                "matched_scenarios": 0,
                "supported_claim": False,
                "validation_passed": False,
            },
        ]
    }
    validation = {
        "schema": "fastdis.competitor_capture_validation.v1",
        "status": "skipped",
        "lanes": [
            {"lane": "unreal_vs_grill", "artifact_mode": "benchmark_capture", "present": True, "errors": []},
            {"lane": "unity_vs_grill", "artifact_mode": "blocked_evidence_only", "present": False, "errors": []},
        ],
    }
    claim_summary = {
        "summary": {
            "publishable_claim_count": 4,
            "blocked_claim_count": 1,
        }
    }
    _write(status_dir / "unreal_vs_grill_status.json", {"status": "ready", "blockers": []})
    _write(status_dir / "unity_vs_grill_status.json", {"status": "blocked_on_grill_baseline", "blockers": ["no current GRILL Unity shared benchmark report present"]})

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        matrix,
        tmp_path / "competitor_capture_validation.json",
        validation,
        tmp_path / "benchmark_claim_summary.json",
        claim_summary,
    )

    assert report["schema"] == "fastdis.competitor_lane_summary.v1"
    assert report["summary"]["lane_count"] == 2
    assert report["summary"]["measured_claim_ready_count"] == 1
    assert report["summary"]["blocked_evidence_lane_count"] == 1
    unreal = next(row for row in report["lanes"] if row["lane"] == "unreal_vs_grill")
    unity = next(row for row in report["lanes"] if row["lane"] == "unity_vs_grill")
    assert unreal["current_state"] == "measured_claim_ready"
    assert unreal["direct_claim_publishable"] is True
    assert unreal["claim_boundary"]["route_scope"] == "current public GRILL Unreal source route"
    assert unreal["claim_boundary"]["publishable_today"] is True
    assert unity["current_state"] == "blocked_evidence_only"
    assert unity["blocked_evidence_available"] is True
    assert unity["claim_boundary"]["route_scope"] == "current public GRILL Unity source/package route"
    assert "import-blocked on the current Mac host" in unity["claim_boundary"]["gap_summary"]
    assert unity["claim_boundary"]["publishable_today"] is True


def test_competitor_lane_summary_cli_writes_outputs(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {"comparisons": []},
    )
    validation_path = _write(
        tmp_path / "competitor_capture_validation.json",
        {"schema": "fastdis.competitor_capture_validation.v1", "status": "skipped", "lanes": []},
    )
    claim_summary_path = _write(
        tmp_path / "benchmark_claim_summary.json",
        {"summary": {"publishable_claim_count": 0, "blocked_claim_count": 2}},
    )
    json_out = tmp_path / "out" / "competitor_lane_summary.json"
    md_out = tmp_path / "out" / "competitor_lane_summary.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_competitor_lane_summary.py"),
            "--matrix",
            str(matrix_path),
            "--validation",
            str(validation_path),
            "--claim-summary",
            str(claim_summary_path),
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
    assert payload["schema"] == "fastdis.competitor_lane_summary.v1"
    markdown = md_out.read_text(encoding="utf-8")
    assert "Competitor Lane Summary" in markdown
    assert "route_scope:" in markdown


def test_competitor_lane_summary_uses_dynamic_unity_claim_boundary_when_import_smoke_passes(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("build_competitor_lane_summary", ROOT / "tools" / "build_competitor_lane_summary.py")
    status_dir = tmp_path / "status"
    monkeypatch.setattr(
        module,
        "DEFAULT_STATUS_REPORTS",
        {
            "unreal_vs_grill": status_dir / "unreal_vs_grill_status.json",
            "unity_vs_grill": status_dir / "unity_vs_grill_status.json",
        },
    )
    _write(status_dir / "unreal_vs_grill_status.json", {"status": "ready", "blockers": []})
    _write(
        status_dir / "unity_vs_grill_status.json",
        {
            "status": "blocked_on_grill_baseline",
            "blockers": ["no current GRILL Unity shared benchmark report present"],
            "import_smoke": {"status": "pass", "failure_stage": "none"},
        },
    )

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        {"comparisons": []},
        tmp_path / "competitor_capture_validation.json",
        {"schema": "fastdis.competitor_capture_validation.v1", "status": "skipped", "lanes": []},
        tmp_path / "benchmark_claim_summary.json",
        {"summary": {"publishable_claim_count": 0, "blocked_claim_count": 1}},
    )

    unity = next(row for row in report["lanes"] if row["lane"] == "unity_vs_grill")
    assert "imports on the checked Mac/Unity host" in unity["claim_boundary"]["gap_summary"]


def test_competitor_lane_summary_uses_ready_unity_claim_boundary_after_public_capture(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("build_competitor_lane_summary", ROOT / "tools" / "build_competitor_lane_summary.py")
    status_dir = tmp_path / "status"
    monkeypatch.setattr(
        module,
        "DEFAULT_STATUS_REPORTS",
        {
            "unreal_vs_grill": status_dir / "unreal_vs_grill_status.json",
            "unity_vs_grill": status_dir / "unity_vs_grill_status.json",
        },
    )
    _write(status_dir / "unreal_vs_grill_status.json", {"status": "ready", "blockers": []})
    _write(
        status_dir / "unity_vs_grill_status.json",
        {
            "status": "ready",
            "blockers": [],
            "import_smoke": {"status": "pass", "failure_stage": "none"},
            "head_to_head_readiness": {"status": "directional_only"},
        },
    )

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        {"comparisons": []},
        tmp_path / "competitor_capture_validation.json",
        {"schema": "fastdis.competitor_capture_validation.v1", "status": "fail", "lanes": []},
        tmp_path / "benchmark_claim_summary.json",
        {"summary": {"publishable_claim_count": 0, "blocked_claim_count": 1}},
    )

    unity = next(row for row in report["lanes"] if row["lane"] == "unity_vs_grill")
    assert unity["current_state"] == "missing_or_unverified"
    assert unity["direct_claim_publishable"] is False
    assert "imports and benchmark-captures on the checked Mac/Unity host" in unity["claim_boundary"]["gap_summary"]


def test_competitor_lane_summary_marks_unity_measured_when_ready_and_comparable(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("build_competitor_lane_summary", ROOT / "tools" / "build_competitor_lane_summary.py")
    status_dir = tmp_path / "status"
    monkeypatch.setattr(
        module,
        "DEFAULT_STATUS_REPORTS",
        {
            "unreal_vs_grill": status_dir / "unreal_vs_grill_status.json",
            "unity_vs_grill": status_dir / "unity_vs_grill_status.json",
        },
    )
    _write(status_dir / "unreal_vs_grill_status.json", {"status": "ready", "blockers": []})
    _write(
        status_dir / "unity_vs_grill_status.json",
        {
            "status": "ready",
            "blockers": [],
            "import_smoke": {"status": "pass", "failure_stage": "none"},
            "head_to_head_readiness": {"status": "comparable"},
        },
    )

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        {"comparisons": []},
        tmp_path / "competitor_capture_validation.json",
        {"schema": "fastdis.competitor_capture_validation.v1", "status": "pass", "lanes": []},
        tmp_path / "benchmark_claim_summary.json",
        {"summary": {"publishable_claim_count": 0, "blocked_claim_count": 0}},
    )

    unity = next(row for row in report["lanes"] if row["lane"] == "unity_vs_grill")
    assert unity["current_state"] == "measured_claim_ready"
    assert unity["direct_claim_publishable"] is True


def test_competitor_lane_summary_uses_dynamic_unreal_claim_boundary_when_mapping_failures_are_classified(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("build_competitor_lane_summary", ROOT / "tools" / "build_competitor_lane_summary.py")
    status_dir = tmp_path / "status"
    monkeypatch.setattr(
        module,
        "DEFAULT_STATUS_REPORTS",
        {
            "unreal_vs_grill": status_dir / "unreal_vs_grill_status.json",
            "unity_vs_grill": status_dir / "unity_vs_grill_status.json",
        },
    )
    _write(
        status_dir / "unreal_vs_grill_status.json",
        {
            "status": "blocked_on_grill_baseline",
            "blockers": [
                "no current GRILL Unreal shared benchmark report present",
                "current host GRILL Unreal mapping export failed",
            ],
            "mapping_export": {"status": "missing-game-module", "failure_kind": "missing-game-module"},
            "mapping_materialize": {"status": "missing-game-module", "failure_kind": "missing-game-module"},
        },
    )
    _write(status_dir / "unity_vs_grill_status.json", {"status": "ready", "blockers": []})

    report = module.build_report(
        tmp_path / "benchmark_matrix.json",
        {"comparisons": []},
        tmp_path / "competitor_capture_validation.json",
        {"schema": "fastdis.competitor_capture_validation.v1", "status": "fail", "lanes": []},
        tmp_path / "benchmark_claim_summary.json",
        {"summary": {"publishable_claim_count": 0, "blocked_claim_count": 1}},
    )

    unreal = next(row for row in report["lanes"] if row["lane"] == "unreal_vs_grill")
    assert "missing-game-module" in unreal["claim_boundary"]["gap_summary"]
    assert "same-host failure boundaries" in unreal["claim_boundary"]["safe_advertising_point"]
