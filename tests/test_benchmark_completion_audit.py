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


def test_build_benchmark_completion_audit_marks_current_gaps_incomplete(tmp_path: Path) -> None:
    module = _load_module("audit_engine_benchmark_completion", ROOT / "tools" / "audit_engine_benchmark_completion.py")

    matrix = {
        "summary": {
            "supported_competitor_claim_count": 0,
            "passing_competitor_validation_count": 0,
            "blocked_evidence_lane_count": 2,
        },
        "claim_boundaries": ["matrix boundary"],
        "surfaces": [
            {
                "surface": "native",
                "latency_rows": 3,
                "scenarios": ["header_filter_90pct_reject", "entity_table_ingest_latest"],
                "notes": [],
            },
            {
                "surface": "python_ctypes",
                "latency_rows": 2,
                "scenarios": ["ctypes_entity_force_reject_no_callback", "ctypes_entity_table_ingest_latest"],
                "notes": [],
            },
            {
                "surface": "unreal",
                "latency_rows": 0,
                "scenarios": ["unreal_proof_verification"],
                "notes": ["engine lane currently has no measured latency fields"],
            },
            {
                "surface": "unity",
                "latency_rows": 0,
                "scenarios": ["unity_runtime_verification"],
                "notes": ["engine lane currently has no measured latency fields"],
            },
            {
                "surface": "godot",
                "latency_rows": 0,
                "scenarios": ["godot_proof_verification"],
                "notes": ["engine lane currently has no measured latency fields"],
            },
        ],
        "comparisons": [
            {
                "left_surface": "unreal",
                "right_surface": "grill_unreal",
                "supported_claim": False,
            }
        ],
        "competitor_validations": [
            {
                "status": "skipped",
                "lanes": [
                    {"lane": "unreal_vs_grill", "present": False, "error_count": 0, "artifact_mode": "blocked_evidence_only"},
                    {"lane": "unity_vs_grill", "present": False, "error_count": 0, "artifact_mode": "blocked_evidence_only"},
                ],
            }
        ],
    }
    cross_engine = {
        "status": "complete",
        "claim_boundaries": ["equivalence boundary"],
        "summary": {
            "benchmark_contract_present": True,
        },
        "deep_surfaces": {
            name: {"deep_rows": 141} for name in ("c", "cpp", "python", "unreal", "godot", "unity")
        },
        "gaps": [],
    }
    unreal_status = {
        "blockers": ["no current GRILL Unreal shared benchmark report present"],
    }
    unity_status = {
        "blockers": ["no current GRILL Unity shared benchmark report present"],
    }
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
                },
            },
            {
                "lane": "unity_vs_grill",
                "claim_boundary": {
                    "route_scope": "current public GRILL Unity source/package route",
                    "gap_summary": "The current public GRILL Unity route is source-available but import-blocked on the current Mac host and Unity editor combination.",
                    "testing_workaround": "Capture GRILL Unity on a Unity host/editor combination that successfully imports the public plugin or example project.",
                    "safe_advertising_point": "FastDIS publishes install smoke and failure artifacts for competitor routes instead of hand-waving over importability gaps.",
                    "publishable_today": True,
                    "non_publishable_angle": "Do not claim direct Unity head-to-head performance wins until a same-host or clearly comparable-host GRILL capture exists.",
                },
            },
        ]
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        {
            "summary": {
                "ingest": {"surface_count": 2},
                "filtering": {"surface_count": 2},
                "latest_state": {"surface_count": 2},
                "replay": {"surface_count": 0},
            }
        },
        tmp_path / "scenario_contract_report.json",
        {
            "status": "partial",
            "summary": {
                "required_surface_count": 7,
                "canonical_scenario_count": 11,
                "canonical_covered_surface_count": 0,
                "all_surface_shared_scenario_count": 0
            },
            "gaps": ["no canonical scenario name is currently shared across every required surface"]
        },
        tmp_path / "surface_claim_report.json",
        {
            "surfaces": [
                {"surface": "native", "boundaries": ["no replay"]},
                {"surface": "python_ctypes", "boundaries": ["no replay"]},
                {"surface": "unreal", "boundaries": ["no filtering"]},
                {"surface": "unity", "boundaries": ["no filtering"]},
                {"surface": "godot", "boundaries": ["no filtering"]},
            ]
        },
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "competitor_lane_summary.json",
        competitor_summary,
        tmp_path / "unreal_status.json",
        unreal_status,
        tmp_path / "unity_status.json",
        unity_status,
    )

    assert report["schema"] == "fastdis.engine_benchmark_completion_audit.v1"
    assert report["status"] == "incomplete"
    assert report["summary"]["complete_count"] >= 1
    assert report["summary"]["partial_count"] >= 3
    assert report["summary"]["blocked_count"] == 2
    assert report["summary"]["blocked_evidence_lane_count"] == 2
    assert "cpp shared benchmark coverage" in report["note"]

    requirement_index = {row["id"]: row for row in report["requirements"]}
    assert requirement_index["shared_contract"]["status"] == "partial"
    assert "no canonical scenario name is currently shared across every required surface" in requirement_index["shared_contract"]["gaps"][-1]
    assert requirement_index["cross_engine_equivalence"]["status"] == "complete"
    assert requirement_index["claim_boundaries"]["status"] == "complete"
    assert requirement_index["engine_runtime_reports"]["status"] == "partial"
    assert requirement_index["unreal_competitor"]["status"] == "blocked"
    assert requirement_index["unity_competitor"]["status"] == "blocked"
    assert "blocked-evidence lane" in requirement_index["unreal_competitor"]["gaps"][-1]
    assert requirement_index["unreal_competitor"]["route_scope"] == "current public GRILL Unreal source route"
    assert "Windows-only" in requirement_index["unreal_competitor"]["gap_summary"]
    assert requirement_index["unity_competitor"]["route_scope"] == "current public GRILL Unity source/package route"
    assert "import-blocked on the current Mac host" in requirement_index["unity_competitor"]["gap_summary"]
    assert requirement_index["replay_reports"]["status"] == "partial"
    assert requirement_index["claim_boundaries"]["status"] == "complete"
    assert report["next_steps"][0].startswith("Promote ")
    assert report["next_steps"][-2].startswith("Capture GRILL Unreal on a Windows host")
    assert report["next_steps"][-1].startswith("Capture GRILL Unity on a Unity host/editor combination")


def test_build_benchmark_completion_audit_can_mark_objective_complete(tmp_path: Path) -> None:
    module = _load_module("audit_engine_benchmark_completion", ROOT / "tools" / "audit_engine_benchmark_completion.py")

    matrix = {
        "summary": {
            "supported_competitor_claim_count": 2,
            "passing_competitor_validation_count": 1,
        },
        "claim_boundaries": ["matrix boundary"],
        "surfaces": [
            {
                "surface": "native",
                "latency_rows": 5,
                "scenarios": [
                    "header_filter_90pct_reject",
                    "entity_table_ingest_latest",
                    "replay_latest_state_apply",
                ],
                "notes": [],
            },
            {
                "surface": "c",
                "latency_rows": 0,
                "runtime_metric_rows": 1,
                "scenarios": [
                    "c_localhost_udp_ingest_truth",
                    "replay_latest_state_apply",
                ],
                "notes": ["truth-verified localhost UDP ingest route normalized from network_ingest_matrix"],
            },
            {
                "surface": "cpp",
                "latency_rows": 4,
                "scenarios": [
                    "cpp_header_filter_90pct_reject",
                    "cpp_entity_table_ingest_latest",
                    "cpp_replay_latest_state_apply",
                ],
                "notes": [],
            },
            {
                "surface": "python_ctypes",
                "latency_rows": 4,
                "scenarios": [
                    "ctypes_entity_force_reject_no_callback",
                    "ctypes_entity_table_ingest_latest",
                    "ctypes_replay_latest_state_apply",
                ],
                "notes": [],
            },
            {
                "surface": "unreal",
                "latency_rows": 3,
                "scenarios": ["unreal_replay_latest_state_apply"],
                "notes": [],
            },
            {
                "surface": "unity",
                "latency_rows": 3,
                "scenarios": ["unity_replay_latest_state_apply"],
                "notes": [],
            },
            {
                "surface": "godot",
                "latency_rows": 3,
                "scenarios": ["godot_replay_latest_state_apply"],
                "notes": [],
            },
        ],
        "comparisons": [
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
        ],
        "competitor_validations": [
            {
                "status": "pass",
                "handoff_workbench_status": "pass",
                "handoff_bundle_kind": "archive_bundle",
                "handoff_self_describing_bundle": True,
                "lanes": [
                    {"lane": "unreal_vs_grill", "present": True, "error_count": 0},
                    {"lane": "unity_vs_grill", "present": True, "error_count": 0},
                ],
            }
        ],
    }
    cross_engine = {
        "status": "complete",
        "claim_boundaries": ["equivalence boundary"],
        "summary": {
            "benchmark_contract_present": True,
        },
        "deep_surfaces": {
            name: {"deep_rows": 141} for name in ("c", "cpp", "python", "unreal", "godot", "unity")
        },
        "gaps": [],
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        {
            "summary": {
                "ingest": {"surface_count": 4},
                "filtering": {"surface_count": 2},
                "latest_state": {"surface_count": 3},
                "replay": {"surface_count": 4},
            }
        },
        tmp_path / "scenario_contract_report.json",
        {
            "status": "complete",
            "summary": {
                "required_surface_count": 7,
                "canonical_scenario_count": 3,
                "canonical_covered_surface_count": 7,
                "all_surface_shared_scenario_count": 3
            },
            "gaps": []
        },
        tmp_path / "surface_claim_report.json",
        {
            "surfaces": [
                {"surface": "native", "boundaries": ["no replay"]},
                {"surface": "c", "boundaries": ["no filtering"]},
                {"surface": "cpp", "boundaries": ["no filtering"]},
                {"surface": "python_ctypes", "boundaries": ["no replay"]},
                {"surface": "unreal", "boundaries": ["no filtering"]},
                {"surface": "unity", "boundaries": ["no filtering"]},
                {"surface": "godot", "boundaries": ["no filtering"]},
            ]
        },
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "competitor_lane_summary.json",
        {"lanes": []},
        tmp_path / "unreal_status.json",
        {"blockers": []},
        tmp_path / "unity_status.json",
        {"blockers": []},
    )

    assert report["status"] == "complete"
    assert report["summary"]["complete_count"] == report["summary"]["requirement_count"]
    assert report["summary"]["partial_count"] == 0
    assert report["summary"]["blocked_count"] == 0
    assert report["summary"]["passing_competitor_validation_count"] == 1


def test_benchmark_completion_audit_cli_writes_outputs_and_optionally_fails(tmp_path: Path) -> None:
    matrix_path = _write(
        tmp_path / "benchmark_matrix.json",
        {
            "summary": {"supported_competitor_claim_count": 0, "passing_competitor_validation_count": 0},
            "claim_boundaries": ["matrix boundary"],
            "surfaces": [
                {"surface": "native", "latency_rows": 1, "scenarios": ["header_filter_90pct_reject", "entity_table_ingest_latest"], "notes": []},
                {"surface": "python_ctypes", "latency_rows": 1, "scenarios": ["ctypes_entity_force_reject_no_callback", "ctypes_entity_table_ingest_latest"], "notes": []},
                {"surface": "unreal", "latency_rows": 0, "scenarios": ["unreal_proof_verification"], "notes": []},
                {"surface": "unity", "latency_rows": 0, "scenarios": ["unity_runtime_verification"], "notes": []},
                {"surface": "godot", "latency_rows": 0, "scenarios": ["godot_proof_verification"], "notes": []},
            ],
            "comparisons": [],
            "competitor_validations": [
                {
                    "status": "skipped",
                    "lanes": [
                        {"lane": "unreal_vs_grill", "present": False, "error_count": 0},
                        {"lane": "unity_vs_grill", "present": False, "error_count": 0},
                    ],
                }
            ],
        },
    )
    cross_path = _write(
        tmp_path / "cross_engine.json",
        {
            "status": "complete",
            "claim_boundaries": ["equivalence boundary"],
            "summary": {"benchmark_contract_present": True},
            "deep_surfaces": {name: {"deep_rows": 141} for name in ("c", "cpp", "python", "unreal", "godot", "unity")},
            "gaps": [],
        },
    )
    surface_claims_path = _write(tmp_path / "surface_claim_report.json", {"surfaces": []})
    scenario_contract_path = _write(
        tmp_path / "scenario_contract_report.json",
        {
            "status": "partial",
            "summary": {
                "required_surface_count": 7,
                "canonical_scenario_count": 11,
                "canonical_covered_surface_count": 0,
                "all_surface_shared_scenario_count": 0
            },
            "gaps": ["no canonical scenario name is currently shared across every required surface"]
        },
    )
    coverage_path = _write(
        tmp_path / "coverage.json",
        {
            "summary": {
                "ingest": {"surface_count": 2},
                "filtering": {"surface_count": 2},
                "latest_state": {"surface_count": 2},
                "replay": {"surface_count": 0},
            }
        },
    )
    competitor_summary_path = _write(tmp_path / "competitor_lane_summary.json", {"lanes": []})
    unreal_status_path = _write(tmp_path / "unreal_status.json", {"blockers": ["missing unreal grill"]})
    unity_status_path = _write(tmp_path / "unity_status.json", {"blockers": ["missing unity grill"]})
    json_out = tmp_path / "out" / "benchmark_completion_audit.json"
    md_out = tmp_path / "out" / "benchmark_completion_audit.md"

    ok = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "audit_engine_benchmark_completion.py"),
            "--matrix",
            str(matrix_path),
            "--coverage",
            str(coverage_path),
            "--scenario-contract",
            str(scenario_contract_path),
            "--surface-claims",
            str(surface_claims_path),
            "--cross-engine-equivalence",
            str(cross_path),
            "--competitor-summary",
            str(competitor_summary_path),
            "--unreal-status",
            str(unreal_status_path),
            "--unity-status",
            str(unity_status_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0
    assert json_out.is_file()
    assert md_out.is_file()
    assert "Benchmark Completion Audit" in md_out.read_text(encoding="utf-8")

    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "audit_engine_benchmark_completion.py"),
            "--matrix",
            str(matrix_path),
            "--coverage",
            str(coverage_path),
            "--scenario-contract",
            str(scenario_contract_path),
            "--surface-claims",
            str(surface_claims_path),
            "--cross-engine-equivalence",
            str(cross_path),
            "--competitor-summary",
            str(competitor_summary_path),
            "--unreal-status",
            str(unreal_status_path),
            "--unity-status",
            str(unity_status_path),
            "--json-out",
            str(tmp_path / "out_fail" / "benchmark_completion_audit.json"),
            "--md-out",
            str(tmp_path / "out_fail" / "benchmark_completion_audit.md"),
            "--fail-incomplete",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1


def test_build_benchmark_completion_audit_requires_competitor_validation_for_publishable_claims(tmp_path: Path) -> None:
    module = _load_module("audit_engine_benchmark_completion", ROOT / "tools" / "audit_engine_benchmark_completion.py")

    matrix = {
        "summary": {
            "supported_competitor_claim_count": 2,
            "passing_competitor_validation_count": 0,
        },
        "claim_boundaries": ["matrix boundary"],
        "surfaces": [
            {"surface": "native", "latency_rows": 5, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject", "entity_table_ingest_latest", "replay_latest_state_apply"], "notes": []},
            {"surface": "python_ctypes", "latency_rows": 4, "runtime_metric_rows": 0, "scenarios": ["ctypes_entity_force_reject_no_callback", "ctypes_entity_table_ingest_latest", "ctypes_replay_latest_state_apply"], "notes": []},
            {"surface": "unreal", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["unreal_replay_latest_state_apply"], "notes": []},
            {"surface": "unity", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["unity_replay_latest_state_apply"], "notes": []},
            {"surface": "godot", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["godot_replay_latest_state_apply"], "notes": []},
        ],
        "comparisons": [
            {"left_surface": "unreal", "right_surface": "grill_unreal", "supported_claim": True},
            {"left_surface": "unity", "right_surface": "grill_unity", "supported_claim": True},
        ],
        "competitor_validations": [
            {
                "status": "fail",
                "path": "artifacts/reports/competitor_capture_validation.json",
                "handoff_workbench_status": "pass",
                "handoff_bundle_kind": "archive_bundle",
                "handoff_self_describing_bundle": True,
                "lanes": [
                    {"lane": "unreal_vs_grill", "present": True, "error_count": 1},
                    {"lane": "unity_vs_grill", "present": True, "error_count": 1},
                ],
            }
        ],
    }
    cross_engine = {
        "status": "complete",
        "claim_boundaries": ["equivalence boundary"],
        "summary": {"benchmark_contract_present": True},
        "deep_surfaces": {name: {"deep_rows": 141} for name in ("c", "cpp", "python", "unreal", "godot", "unity")},
        "gaps": [],
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        {
            "summary": {
                "ingest": {"surface_count": 4},
                "filtering": {"surface_count": 2},
                "latest_state": {"surface_count": 3},
                "replay": {"surface_count": 4},
            }
        },
        tmp_path / "scenario_contract_report.json",
        {
            "status": "complete",
            "summary": {
                "required_surface_count": 7,
                "canonical_scenario_count": 3,
                "canonical_covered_surface_count": 7,
                "all_surface_shared_scenario_count": 3
            },
            "gaps": []
        },
        tmp_path / "surface_claim_report.json",
        {
            "surfaces": [
                {"surface": "native", "boundaries": ["no replay"]},
                {"surface": "python_ctypes", "boundaries": ["no replay"]},
                {"surface": "unreal", "boundaries": ["no filtering"]},
                {"surface": "unity", "boundaries": ["no filtering"]},
                {"surface": "godot", "boundaries": ["no filtering"]},
            ]
        },
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "competitor_lane_summary.json",
        {"lanes": []},
        tmp_path / "unreal_status.json",
        {"blockers": []},
        tmp_path / "unity_status.json",
        {"blockers": []},
    )

    requirement_index = {row["id"]: row for row in report["requirements"]}
    assert report["status"] == "incomplete"
    assert requirement_index["unreal_competitor"]["status"] == "partial"
    assert requirement_index["unity_competitor"]["status"] == "partial"
    assert "validation" in requirement_index["unreal_competitor"]["gaps"][0]
    assert report["summary"]["passing_competitor_validation_count"] == 0


def test_build_benchmark_completion_audit_accepts_live_measured_competitor_lane_from_summary(tmp_path: Path) -> None:
    module = _load_module("audit_engine_benchmark_completion_measured_lane", ROOT / "tools" / "audit_engine_benchmark_completion.py")

    matrix = {
        "summary": {
            "supported_competitor_claim_count": 0,
            "passing_competitor_validation_count": 0,
        },
        "claim_boundaries": ["matrix boundary"],
        "surfaces": [
            {"surface": "native", "latency_rows": 5, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject", "entity_table_ingest_latest", "replay_latest_state_apply"], "notes": []},
            {"surface": "c", "latency_rows": 0, "runtime_metric_rows": 1, "scenarios": ["c_localhost_udp_ingest_truth", "replay_latest_state_apply"], "notes": []},
            {"surface": "cpp", "latency_rows": 4, "runtime_metric_rows": 0, "scenarios": ["cpp_header_filter_90pct_reject", "cpp_entity_table_ingest_latest", "cpp_replay_latest_state_apply"], "notes": []},
            {"surface": "python_ctypes", "latency_rows": 4, "runtime_metric_rows": 0, "scenarios": ["ctypes_entity_force_reject_no_callback", "ctypes_entity_table_ingest_latest", "ctypes_replay_latest_state_apply"], "notes": []},
            {"surface": "unreal", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["unreal_replay_latest_state_apply"], "notes": []},
            {"surface": "unity", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["unity_replay_latest_state_apply"], "notes": []},
            {"surface": "godot", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["godot_replay_latest_state_apply"], "notes": []},
        ],
        "comparisons": [
            {"left_surface": "unreal", "right_surface": "grill_unreal", "supported_claim": False},
            {"left_surface": "unity", "right_surface": "grill_unity", "supported_claim": False},
        ],
        "competitor_validations": [
            {
                "status": "pass",
                "path": "artifacts/reports/competitor_capture_validation.json",
                "handoff_workbench_status": "pass",
                "handoff_bundle_kind": "local_checkout",
                "handoff_self_describing_bundle": False,
                "lanes": [
                    {"lane": "unreal_vs_grill", "present": False, "error_count": 0, "artifact_mode": "blocked_evidence_only"},
                    {"lane": "unity_vs_grill", "present": True, "error_count": 0, "artifact_mode": "benchmark_capture"},
                ],
            }
        ],
    }
    cross_engine = {
        "status": "complete",
        "claim_boundaries": ["equivalence boundary"],
        "summary": {"benchmark_contract_present": True},
        "deep_surfaces": {name: {"deep_rows": 141} for name in ("c", "cpp", "python", "unreal", "godot", "unity")},
        "gaps": [],
    }
    competitor_summary = {
        "lanes": [
            {
                "lane": "unreal_vs_grill",
                "current_state": "blocked_evidence_only",
                "claim_boundary": {
                    "route_scope": "current public GRILL Unreal source route",
                    "gap_summary": "blocked unreal",
                    "testing_workaround": "use windows",
                    "safe_advertising_point": "blocked unreal evidence",
                    "publishable_today": True,
                    "non_publishable_angle": "no unreal claim",
                },
            },
            {
                "lane": "unity_vs_grill",
                "current_state": "measured_claim_ready",
                "claim_boundary": {
                    "route_scope": "current public GRILL Unity source/package route",
                    "gap_summary": "unity compares directly",
                    "testing_workaround": "review matched rows",
                    "safe_advertising_point": "unity proof-backed",
                    "publishable_today": True,
                    "non_publishable_angle": None,
                },
            },
        ]
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        {
            "summary": {
                "ingest": {"surface_count": 4},
                "filtering": {"surface_count": 2},
                "latest_state": {"surface_count": 3},
                "replay": {"surface_count": 4},
            }
        },
        tmp_path / "scenario_contract_report.json",
        {
            "status": "complete",
            "summary": {
                "required_surface_count": 7,
                "canonical_scenario_count": 3,
                "canonical_covered_surface_count": 7,
                "all_surface_shared_scenario_count": 3
            },
            "gaps": []
        },
        tmp_path / "surface_claim_report.json",
        {
            "surfaces": [
                {"surface": "native", "boundaries": ["no replay"]},
                {"surface": "c", "boundaries": ["no filtering"]},
                {"surface": "cpp", "boundaries": ["no filtering"]},
                {"surface": "python_ctypes", "boundaries": ["no replay"]},
                {"surface": "unreal", "boundaries": ["no filtering"]},
                {"surface": "unity", "boundaries": ["no filtering"]},
                {"surface": "godot", "boundaries": ["no filtering"]},
            ]
        },
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "competitor_lane_summary.json",
        competitor_summary,
        tmp_path / "unreal_status.json",
        {"blockers": ["unreal blocked"]},
        tmp_path / "unity_status.json",
        {"blockers": []},
    )

    requirement_index = {row["id"]: row for row in report["requirements"]}
    assert requirement_index["unreal_competitor"]["status"] == "blocked"
    assert requirement_index["unity_competitor"]["status"] == "complete"


def test_build_benchmark_completion_audit_requires_self_describing_competitor_bundle_for_publishable_claims(tmp_path: Path) -> None:
    module = _load_module("audit_engine_benchmark_completion_self_describing", ROOT / "tools" / "audit_engine_benchmark_completion.py")

    matrix = {
        "summary": {
            "supported_competitor_claim_count": 2,
            "passing_competitor_validation_count": 1,
        },
        "claim_boundaries": ["matrix boundary"],
        "surfaces": [
            {"surface": "native", "latency_rows": 5, "runtime_metric_rows": 0, "scenarios": ["header_filter_90pct_reject", "entity_table_ingest_latest", "replay_latest_state_apply"], "notes": []},
            {"surface": "c", "latency_rows": 0, "runtime_metric_rows": 1, "scenarios": ["c_localhost_udp_ingest_truth", "replay_latest_state_apply"], "notes": []},
            {"surface": "cpp", "latency_rows": 4, "runtime_metric_rows": 0, "scenarios": ["cpp_header_filter_90pct_reject", "cpp_entity_table_ingest_latest", "cpp_replay_latest_state_apply"], "notes": []},
            {"surface": "python_ctypes", "latency_rows": 4, "runtime_metric_rows": 0, "scenarios": ["ctypes_entity_force_reject_no_callback", "ctypes_entity_table_ingest_latest", "ctypes_replay_latest_state_apply"], "notes": []},
            {"surface": "unreal", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["unreal_replay_latest_state_apply"], "notes": []},
            {"surface": "unity", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["unity_replay_latest_state_apply"], "notes": []},
            {"surface": "godot", "latency_rows": 3, "runtime_metric_rows": 0, "scenarios": ["godot_replay_latest_state_apply"], "notes": []},
        ],
        "comparisons": [
            {"left_surface": "unreal", "right_surface": "grill_unreal", "supported_claim": True},
            {"left_surface": "unity", "right_surface": "grill_unity", "supported_claim": True},
        ],
        "competitor_validations": [
            {
                "status": "pass",
                "path": "artifacts/reports/competitor_capture_validation.json",
                "handoff_workbench_status": "pass",
                "handoff_bundle_kind": "local_checkout",
                "handoff_self_describing_bundle": False,
                "lanes": [
                    {"lane": "unreal_vs_grill", "present": True, "error_count": 0},
                    {"lane": "unity_vs_grill", "present": True, "error_count": 0},
                ],
            }
        ],
    }
    cross_engine = {
        "status": "complete",
        "claim_boundaries": ["equivalence boundary"],
        "summary": {"benchmark_contract_present": True},
        "deep_surfaces": {name: {"deep_rows": 141} for name in ("c", "cpp", "python", "unreal", "godot", "unity")},
        "gaps": [],
    }

    report = module.build_report(
        tmp_path / "matrix.json",
        matrix,
        tmp_path / "coverage.json",
        {
            "summary": {
                "ingest": {"surface_count": 4},
                "filtering": {"surface_count": 2},
                "latest_state": {"surface_count": 3},
                "replay": {"surface_count": 4},
            }
        },
        tmp_path / "scenario_contract_report.json",
        {
            "status": "complete",
            "summary": {
                "required_surface_count": 7,
                "canonical_scenario_count": 3,
                "canonical_covered_surface_count": 7,
                "all_surface_shared_scenario_count": 3
            },
            "gaps": []
        },
        tmp_path / "surface_claim_report.json",
        {
            "surfaces": [
                {"surface": "native", "boundaries": ["no replay"]},
                {"surface": "c", "boundaries": ["no filtering"]},
                {"surface": "cpp", "boundaries": ["no filtering"]},
                {"surface": "python_ctypes", "boundaries": ["no replay"]},
                {"surface": "unreal", "boundaries": ["no filtering"]},
                {"surface": "unity", "boundaries": ["no filtering"]},
                {"surface": "godot", "boundaries": ["no filtering"]},
            ]
        },
        tmp_path / "cross_engine.json",
        cross_engine,
        tmp_path / "competitor_lane_summary.json",
        {"lanes": []},
        tmp_path / "unreal_status.json",
        {"blockers": []},
        tmp_path / "unity_status.json",
        {"blockers": []},
    )

    requirement_index = {row["id"]: row for row in report["requirements"]}
    assert report["status"] == "incomplete"
    assert requirement_index["unreal_competitor"]["status"] == "partial"
    assert requirement_index["unity_competitor"]["status"] == "partial"
    assert "self-describing returned bundle" in requirement_index["unreal_competitor"]["gaps"][0]
