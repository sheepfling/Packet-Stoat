from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import zipfile
import hashlib
import io
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import export_competitor_benchmark_handoff


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_archive(archive_path: Path, files: dict[str, str]) -> None:
    bundle_root = "fastdis-competitor-benchmark-handoff-test"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, content in files.items():
            archive.writestr(f"{bundle_root}/{relative}", content)


def _write_manifest_archive(archive_path: Path, files: dict[str, str]) -> None:
    bundle_root = "fastdis-competitor-benchmark-handoff-test"
    entries = []
    for relative, content in files.items():
        payload = content.encode("utf-8")
        entries.append(
            {
                "path": relative,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    readme = "# Returned bundle\n"
    readme_bytes = readme.encode("utf-8")
    entries.append(
        {
            "path": "README.md",
            "size_bytes": len(readme_bytes),
            "sha256": hashlib.sha256(readme_bytes).hexdigest(),
        }
    )
    manifest = {
        "schema": "fastdis.competitor_benchmark_handoff_manifest.v1",
        "bundle_root": bundle_root,
        "package_stamp": "test",
        "file_count": len(entries),
        "total_size_bytes": sum(entry["size_bytes"] for entry in entries),
        "files": entries,
    }
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{bundle_root}/README.md", readme)
        archive.writestr(f"{bundle_root}/MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        for relative, content in files.items():
            archive.writestr(f"{bundle_root}/{relative}", content)


def _unreal_capture_manifest() -> dict:
    return {
        "schema": "fastdis.competitor_capture_manifest.v1",
        "lanes": [
            {
                "lane": "unreal_vs_grill",
                "fastdis_host": {
                    "system": "Darwin",
                    "release": "25.5.0",
                    "machine": "arm64",
                    "engine_version": "5.8",
                },
                "fastdis_scenarios": [
                    "entity_state_1x10hz",
                    "entity_state_100x30hz",
                ],
                "required_return_artifacts": [
                    "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
                    "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
                    "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md",
                    "build/reports/engine_head_to_head/unreal_vs_grill.json",
                    "build/reports/engine_head_to_head/unreal_vs_grill.md",
                ],
                "required_capture_fields": [
                    "host.system",
                    "host.machine",
                    "engine.version",
                    "scenario.map",
                    "scenario.traffic_mix",
                    "results[].scenario",
                    "results[].packets_per_sec",
                    "results[].main_thread_apply_ms",
                ],
            }
        ],
    }


def _full_capture_manifest() -> dict:
    return {
        "schema": "fastdis.competitor_capture_manifest.v1",
        "lanes": [
            {
                "lane": "unreal_vs_grill",
                "fastdis_host": {
                    "system": "Darwin",
                    "release": "25.5.0",
                    "machine": "arm64",
                    "engine_version": "5.8",
                },
                "fastdis_scenarios": [
                    "entity_state_1x10hz",
                ],
                "required_return_artifacts": [
                    "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
                    "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
                    "build/reports/engine_head_to_head/unreal_vs_grill.json",
                ],
                "required_capture_fields": [
                    "host.system",
                    "engine.version",
                ],
            },
            {
                "lane": "unity_vs_grill",
                "fastdis_host": {
                    "system": "Darwin",
                    "release": "25.5.0",
                    "machine": "arm64",
                    "unity_version": "6000.5.0f1",
                },
                "fastdis_scenarios": [
                    "entity_state_1x10hz",
                ],
                "required_return_artifacts": [
                    "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json",
                    "build/reports/engine_benchmarks/grill_unity_engine_benchmark_report.json",
                    "build/reports/engine_head_to_head/unity_vs_grill.json",
                ],
                "required_capture_fields": [
                    "host.system",
                    "unity.version",
                ],
            },
        ],
    }


def _write_returned_unreal_lane(bundle_root: Path) -> None:
    raw = {
        "schema": "fastdis.unreal_grill_benchmark_baseline.v1",
        "product": "GRILL DIS for Unreal",
        "captured_at_utc": "2026-06-26T02:00:00Z",
        "repository": {
            "url": "https://github.com/AF-GRILL/DISPluginForUnreal",
            "commit": "abc123",
        },
        "engine": {
            "version": "5.8",
        },
        "host": {
            "system": "Darwin",
            "release": "25.5.0",
            "machine": "arm64",
        },
        "scenario": {
            "map": "LoopbackBench",
            "traffic_mix": "100% Entity State",
            "notes": "Synthetic same-host return bundle for importer roundtrip proof.",
        },
        "results": [
            {
                "scenario": "entity_state_1x10hz",
                "packets_received": 24,
                "packets_parsed": 24,
                "packets_accepted": 24,
                "packets_rejected": 0,
                "malformed": 0,
                "socket_drops": 0,
                "queue_drops": 0,
                "p50_ingest_ms": 0.32,
                "p95_ingest_ms": 0.4,
                "p99_ingest_ms": 0.44,
                "steady_state_gc_bytes": 0,
                "main_thread_apply_ms": 0.12,
                "packets_per_sec": 110000.0,
                "notes": "Measured same-host baseline.",
            }
        ],
    }
    fastdis_report = json.loads((ROOT / "tests" / "data" / "engine_benchmark_reports" / "fastdis_unreal.sample.json").read_text(encoding="utf-8"))
    grill_report = json.loads((ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json").read_text(encoding="utf-8"))
    head_module = _load_module("run_engine_head_to_head_matrix_roundtrip", ROOT / "tools" / "run_engine_head_to_head_matrix.py")
    comparison = head_module.build_report(
        fastdis_report,
        grill_report,
        left_path=ROOT / "tests" / "data" / "engine_benchmark_reports" / "fastdis_unreal.sample.json",
        right_path=ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json",
        left_label="FastDIS Unreal",
        right_label="GRILL Unreal",
    )

    raw_path = bundle_root / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json"
    report_json_path = bundle_root / "build" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.json"
    report_md_path = bundle_root / "build" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.md"
    head_json_path = bundle_root / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill.json"
    head_md_path = bundle_root / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill.md"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    head_json_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    report_json_path.write_text(json.dumps(grill_report, indent=2) + "\n", encoding="utf-8")
    report_md_path.write_text("# GRILL Unreal Benchmark Report\n", encoding="utf-8")
    head_json_path.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    head_md_path.write_text("# Unreal vs GRILL\n", encoding="utf-8")


def test_adopt_files_copies_returned_competitor_artifacts(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)

    bundle_root = tmp_path / "bundle"
    (bundle_root / "verification_reports" / "unity_grill_baseline").mkdir(parents=True)
    (bundle_root / "build" / "reports" / "engine_benchmarks").mkdir(parents=True)
    (bundle_root / "build" / "reports").mkdir(parents=True, exist_ok=True)
    (bundle_root / "build" / "reports" / "benchmark_matrix").mkdir(parents=True, exist_ok=True)
    (bundle_root / "build" / "reports" / "benchmark_coverage").mkdir(parents=True, exist_ok=True)
    (bundle_root / "build" / "reports" / "scenario_contract").mkdir(parents=True, exist_ok=True)
    (bundle_root / "build" / "reports" / "benchmark_completion_audit").mkdir(parents=True, exist_ok=True)
    (bundle_root / "build" / "reports" / "benchmark_claim_summary").mkdir(parents=True, exist_ok=True)
    (bundle_root / "build" / "reports" / "benchmark_contract_stack").mkdir(parents=True, exist_ok=True)
    unity_raw = bundle_root / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"
    unity_shared = bundle_root / "build" / "reports" / "engine_benchmarks" / "grill_unity_engine_benchmark_report.json"
    unity_shared_md = bundle_root / "build" / "reports" / "engine_benchmarks" / "grill_unity_engine_benchmark_report.md"
    matrix = bundle_root / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
    coverage = bundle_root / "build" / "reports" / "benchmark_coverage" / "benchmark_coverage_report.json"
    coverage_md = bundle_root / "build" / "reports" / "benchmark_coverage" / "benchmark_coverage_report.md"
    scenario_contract = bundle_root / "build" / "reports" / "scenario_contract" / "scenario_contract_report.json"
    scenario_contract_md = bundle_root / "build" / "reports" / "scenario_contract" / "scenario_contract_report.md"
    manifest = bundle_root / "build" / "reports" / "competitor_capture_manifest.json"
    validation = bundle_root / "build" / "reports" / "competitor_capture_validation.json"
    completion_audit = bundle_root / "build" / "reports" / "benchmark_completion_audit" / "benchmark_completion_audit.json"
    claim_summary = bundle_root / "build" / "reports" / "benchmark_claim_summary" / "benchmark_claim_summary.json"
    contract_stack = bundle_root / "build" / "reports" / "benchmark_contract_stack" / "benchmark_contract_stack.json"
    unity_raw.write_text('{"schema":"fastdis.unity_grill_benchmark_baseline.v1"}\n', encoding="utf-8")
    unity_shared.write_text('{"schema":"fastdis.engine_benchmark_report.v1"}\n', encoding="utf-8")
    unity_shared_md.write_text("# GRILL Unity Benchmark Report\n", encoding="utf-8")
    matrix.write_text('{"schema":"fastdis.engine_benchmark_matrix.v1"}\n', encoding="utf-8")
    coverage.write_text('{"schema":"fastdis.benchmark_coverage_report.v1"}\n', encoding="utf-8")
    coverage_md.write_text("# Benchmark Coverage Report\n", encoding="utf-8")
    scenario_contract.write_text('{"schema":"fastdis.scenario_contract_report.v1"}\n', encoding="utf-8")
    scenario_contract_md.write_text("# Scenario Contract Report\n", encoding="utf-8")
    manifest.write_text('{"schema":"fastdis.competitor_capture_manifest.v1"}\n', encoding="utf-8")
    validation.write_text('{"schema":"fastdis.competitor_capture_validation.v1"}\n', encoding="utf-8")
    completion_audit.write_text('{"schema":"fastdis.engine_benchmark_completion_audit.v1"}\n', encoding="utf-8")
    claim_summary.write_text('{"schema":"fastdis.benchmark_claim_summary.v1"}\n', encoding="utf-8")
    contract_stack.write_text('{"schema":"fastdis.benchmark_contract_stack.v1"}\n', encoding="utf-8")

    adopted = module.adopt_files(bundle_root, overwrite=False)

    assert [path.relative_to(sandbox_root).as_posix() for path in adopted] == [
        "build/reports/benchmark_matrix/benchmark_matrix.json",
        "build/reports/benchmark_coverage/benchmark_coverage_report.json",
        "build/reports/benchmark_coverage/benchmark_coverage_report.md",
        "build/reports/scenario_contract/scenario_contract_report.json",
        "build/reports/scenario_contract/scenario_contract_report.md",
        "build/reports/competitor_capture_manifest.json",
        "build/reports/competitor_capture_validation.json",
        "build/reports/benchmark_completion_audit/benchmark_completion_audit.json",
        "build/reports/benchmark_claim_summary/benchmark_claim_summary.json",
        "build/reports/benchmark_contract_stack/benchmark_contract_stack.json",
        "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json",
        "build/reports/engine_benchmarks/grill_unity_engine_benchmark_report.json",
        "build/reports/engine_benchmarks/grill_unity_engine_benchmark_report.md",
    ]
    assert (sandbox_root / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json").is_file()


def test_adopt_files_copies_blocked_evidence_artifacts(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff_blocked", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)

    bundle_root = tmp_path / "bundle"
    (bundle_root / "verification_reports" / "unreal_grill_baseline").mkdir(parents=True)
    (bundle_root / "verification_reports" / "unity_grill_baseline").mkdir(parents=True)
    (bundle_root / "build" / "reports" / "engine_head_to_head").mkdir(parents=True)

    unreal_smoke = bundle_root / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_source_smoke.json"
    unreal_smoke_md = bundle_root / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_source_smoke.md"
    unity_smoke = bundle_root / "verification_reports" / "unity_grill_baseline" / "grill_unity_import_smoke.json"
    unity_smoke_md = bundle_root / "verification_reports" / "unity_grill_baseline" / "grill_unity_import_smoke.md"
    unreal_status = bundle_root / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json"
    unreal_status_md = bundle_root / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.md"
    unity_status = bundle_root / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.json"
    unity_status_md = bundle_root / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.md"

    unreal_smoke.write_text('{"schema":"fastdis.grill_unreal_source_smoke.v1"}\n', encoding="utf-8")
    unreal_smoke_md.write_text("# GRILL Unreal Source Smoke\n", encoding="utf-8")
    unity_smoke.write_text('{"schema":"fastdis.grill_unity_import_smoke.v1"}\n', encoding="utf-8")
    unity_smoke_md.write_text("# GRILL Unity Import Smoke\n", encoding="utf-8")
    unreal_status.write_text('{"schema":"fastdis.unreal_grill_baseline_status.v1"}\n', encoding="utf-8")
    unreal_status_md.write_text("# Unreal vs GRILL Status\n", encoding="utf-8")
    unity_status.write_text('{"schema":"fastdis.unity_grill_baseline_status.v1"}\n', encoding="utf-8")
    unity_status_md.write_text("# Unity vs GRILL Status\n", encoding="utf-8")

    adopted = module.adopt_files(bundle_root, overwrite=False)

    assert [path.relative_to(sandbox_root).as_posix() for path in adopted] == [
        "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
        "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md",
        "verification_reports/unity_grill_baseline/grill_unity_import_smoke.json",
        "verification_reports/unity_grill_baseline/grill_unity_import_smoke.md",
        "build/reports/engine_head_to_head/unreal_vs_grill_status.json",
        "build/reports/engine_head_to_head/unreal_vs_grill_status.md",
        "build/reports/engine_head_to_head/unity_vs_grill_status.json",
        "build/reports/engine_head_to_head/unity_vs_grill_status.md",
    ]


def test_validate_bundle_accepts_blocked_evidence_only_return(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff_validate_blocked", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    manifest_path = sandbox_root / "build" / "reports" / "competitor_capture_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"schema": "fastdis.competitor_capture_manifest.v1", "lanes": []}) + "\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.WORKBENCH, "build_report", lambda bundle_root: {"status": "pass"})
    monkeypatch.setattr(
        module.VALIDATOR,
        "validate_bundle_from_manifest",
        lambda bundle_root, manifest_payload, if_available=False: {
            "status": "skipped",
            "lanes": [
                {
                    "lane": "unreal_vs_grill",
                    "artifact_mode": "blocked_evidence_only",
                }
            ],
        },
    )

    validation = module.validate_bundle(tmp_path / "bundle")

    assert validation["status"] == "skipped"


def test_validate_bundle_rejects_empty_skipped_return(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff_validate_empty", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    manifest_path = sandbox_root / "build" / "reports" / "competitor_capture_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"schema": "fastdis.competitor_capture_manifest.v1", "lanes": []}) + "\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.WORKBENCH, "build_report", lambda bundle_root: {"status": "pass"})
    monkeypatch.setattr(
        module.VALIDATOR,
        "validate_bundle_from_manifest",
        lambda bundle_root, manifest_payload, if_available=False: {
            "status": "skipped",
            "lanes": [
                {
                    "lane": "unreal_vs_grill",
                    "artifact_mode": "empty",
                }
            ],
        },
    )

    try:
        module.validate_bundle(tmp_path / "bundle")
    except ValueError as exc:
        assert "did not contain benchmark captures or blocked evidence" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_post_import_summary_lines_report_lane_and_claim_state(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff_summary", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    monkeypatch.setattr(module, "ROOT", sandbox_root)

    reports = sandbox_root / "build" / "reports"
    (reports / "engine_head_to_head").mkdir(parents=True, exist_ok=True)
    (reports / "benchmark_claim_summary").mkdir(parents=True, exist_ok=True)
    (reports / "competitor_lane_summary").mkdir(parents=True, exist_ok=True)

    (reports / "competitor_lane_summary" / "competitor_lane_summary.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "summary": {
                    "measured_claim_ready_count": 1,
                    "blocked_lane_count": 1,
                    "blocked_evidence_lane_count": 1,
                },
                "lanes": [
                    {
                        "lane": "unreal_vs_grill",
                        "current_state": "blocked_evidence_only",
                        "direct_claim_publishable": False,
                        "blocked_evidence_available": True,
                    },
                    {
                        "lane": "unity_vs_grill",
                        "current_state": "measured_claim_ready",
                        "direct_claim_publishable": True,
                        "blocked_evidence_available": False,
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    (reports / "competitor_capture_validation.json").write_text(
        json.dumps(
            {
                "status": "skipped",
                "lanes": [
                    {
                        "lane": "unreal_vs_grill",
                        "artifact_mode": "blocked_evidence_only",
                        "present": False,
                    },
                    {
                        "lane": "unity_vs_grill",
                        "artifact_mode": "benchmark_capture",
                        "present": True,
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (reports / "engine_head_to_head" / "unreal_vs_grill_status.json").write_text(
        json.dumps({"status": "blocked_on_grill_baseline", "blockers": ["host mismatch"]}) + "\n",
        encoding="utf-8",
    )
    (reports / "engine_head_to_head" / "unity_vs_grill_status.json").write_text(
        json.dumps({"status": "pass", "blockers": []}) + "\n",
        encoding="utf-8",
    )
    (reports / "benchmark_claim_summary" / "benchmark_claim_summary.json").write_text(
        json.dumps(
            {
                "summary": {
                    "publishable_claim_count": 3,
                    "blocked_claim_count": 2,
                    "blocked_evidence_lane_count": 1,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    lines = module.post_import_summary_lines()

    assert "competitor_lane_summary: status=complete measured=1 blocked=1 blocked_evidence=1" in lines
    assert "  unreal_vs_grill: state=blocked_evidence_only publishable=False blocked_evidence=True" in lines
    assert "  unity_vs_grill: state=measured_claim_ready publishable=True blocked_evidence=False" in lines
    assert "competitor_capture_validation: skipped" in lines
    assert "  unreal_vs_grill: artifact_mode=blocked_evidence_only present=False" in lines
    assert "  unity_vs_grill: artifact_mode=benchmark_capture present=True" in lines
    assert "claim_summary: publishable=3 blocked=2 blocked_evidence_lanes=1" in lines


def test_main_imports_archive_and_can_skip_refresh(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(module, "validate_bundle", lambda bundle_root: {"status": "pass"})
    archive_path = tmp_path / "handoff.zip"
    _write_manifest_archive(
        archive_path,
        {
            "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json": json.dumps({"schema": "fastdis.unreal_grill_benchmark_baseline.v1"}) + "\n",
            "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json": json.dumps({"schema": "fastdis.engine_benchmark_report.v1"}) + "\n",
            "build/reports/benchmark_matrix/benchmark_matrix.json": json.dumps({"schema": "fastdis.engine_benchmark_matrix.v1"}) + "\n",
            "build/reports/competitor_capture_validation.json": json.dumps({"schema": "fastdis.competitor_capture_validation.v1"}) + "\n",
            "build/reports/benchmark_completion_audit/benchmark_completion_audit.json": json.dumps({"schema": "fastdis.engine_benchmark_completion_audit.v1"}) + "\n",
        },
    )
    args = module.argparse.Namespace(
        archive=str(archive_path),
        overwrite=False,
        checksum=None,
        skip_refresh=True,
    )
    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)

    rc = module.main()

    assert rc == 0
    assert (sandbox_root / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json").is_file()
    assert (sandbox_root / "build" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.json").is_file()
    assert (sandbox_root / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json").is_file()
    assert (sandbox_root / "build" / "reports" / "competitor_capture_validation.json").is_file()
    assert (sandbox_root / "build" / "reports" / "benchmark_completion_audit" / "benchmark_completion_audit.json").is_file()


def test_main_imports_archive_and_runs_refresh_when_enabled(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(module, "validate_bundle", lambda bundle_root: {"status": "pass"})
    archive_path = tmp_path / "handoff.zip"
    _write_manifest_archive(
        archive_path,
        {
            "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json": json.dumps({"schema": "fastdis.unity_grill_benchmark_baseline.v1"}) + "\n",
            "build/reports/engine_head_to_head/unity_vs_grill.json": json.dumps({"schema": "fastdis.engine_head_to_head_report.v1"}) + "\n",
        },
    )
    args = module.argparse.Namespace(
        archive=str(archive_path),
        overwrite=False,
        checksum=None,
        skip_refresh=False,
    )
    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)
    refresh_calls: list[str] = []
    monkeypatch.setattr(module, "run_refresh", lambda: refresh_calls.append("refresh") or 0)

    rc = module.main()

    assert rc == 0
    assert refresh_calls == ["refresh"]
    assert (sandbox_root / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json").is_file()
    assert (sandbox_root / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill.json").is_file()


def test_main_prints_post_import_summary(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff_print_summary", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(module, "validate_bundle", lambda bundle_root: {"status": "skipped"})
    monkeypatch.setattr(module, "post_import_summary_lines", lambda: ["competitor_capture_validation: skipped", "  unreal_vs_grill: artifact_mode=blocked_evidence_only present=False"])
    archive_path = tmp_path / "handoff.zip"
    _write_manifest_archive(
        archive_path,
        {
            "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json": json.dumps({"schema": "fastdis.grill_unreal_source_smoke.v1"}) + "\n",
        },
    )
    args = module.argparse.Namespace(
        archive=str(archive_path),
        overwrite=False,
        checksum=None,
        skip_refresh=True,
    )
    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        rc = module.main()

    assert rc == 0
    out = stdout.getvalue()
    assert "Post-import summary:" in out
    assert "competitor_capture_validation: skipped" in out
    assert "artifact_mode=blocked_evidence_only" in out


def test_main_rejects_invalid_bundle_before_adoption(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    archive_path = tmp_path / "handoff.zip"
    _write_manifest_archive(
        archive_path,
        {
            "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json": json.dumps({"schema": "fastdis.unreal_grill_benchmark_baseline.v1"}) + "\n",
        },
    )
    args = module.argparse.Namespace(
        archive=str(archive_path),
        overwrite=False,
        checksum=None,
        skip_refresh=True,
    )
    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(module, "validate_bundle", lambda bundle_root: (_ for _ in ()).throw(ValueError("invalid bundle")))

    try:
        module.main()
    except ValueError as exc:
        assert "invalid bundle" in str(exc)
    else:
        raise AssertionError("expected invalid bundle to be rejected")


def test_validate_bundle_rejects_missing_workbench_manifest(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("import_competitor_benchmark_handoff_workbench", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    reports = sandbox_root / "build" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "competitor_capture_manifest.json").write_text('{"lanes":[]}\n', encoding="utf-8")
    monkeypatch.setattr(module.VALIDATOR, "load_json", lambda path: {"lanes": []})
    monkeypatch.setattr(module.VALIDATOR, "validate_bundle_from_manifest", lambda bundle_root, manifest_payload: {"status": "pass"})

    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    (bundle_root / "README.md").write_text("# Missing manifest\n", encoding="utf-8")

    try:
        module.validate_bundle(bundle_root)
    except ValueError as exc:
        assert "workbench validation" in str(exc)
    else:
        raise AssertionError("expected workbench validation failure for missing manifest")


def test_exported_handoff_archive_can_roundtrip_with_synthetic_unreal_return_bundle(tmp_path: Path, monkeypatch) -> None:
    export_archive = tmp_path / "export" / f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}.zip"
    export_competitor_benchmark_handoff.export_archive(export_archive)

    extracted = tmp_path / "returned"
    with zipfile.ZipFile(export_archive) as archive:
        archive.extractall(extracted)
    bundle_root = next(child for child in extracted.iterdir() if child.is_dir())
    _write_returned_unreal_lane(bundle_root)

    returned_archive = tmp_path / "returned.zip"
    with zipfile.ZipFile(returned_archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in bundle_root.rglob("*"):
            if path.is_file():
                archive.write(path, arcname=str(Path(bundle_root.name) / path.relative_to(bundle_root)))

    module = _load_module("import_competitor_benchmark_handoff_roundtrip", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(module, "run_refresh", lambda: 0)

    manifest_path = sandbox_root / "build" / "reports" / "competitor_capture_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(_unreal_capture_manifest(), indent=2) + "\n", encoding="utf-8")

    args = module.argparse.Namespace(
        archive=str(returned_archive),
        overwrite=True,
        checksum=None,
        skip_refresh=True,
    )
    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)

    rc = module.main()

    assert rc == 0
    assert (sandbox_root / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json").is_file()
    assert (sandbox_root / "build" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.json").is_file()
    assert (sandbox_root / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill.json").is_file()


def test_exported_handoff_archive_can_roundtrip_with_blocked_evidence_only_return_bundle(tmp_path: Path, monkeypatch) -> None:
    export_archive = tmp_path / "export" / f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}.zip"
    export_competitor_benchmark_handoff.export_archive(export_archive)

    extracted = tmp_path / "returned"
    with zipfile.ZipFile(export_archive) as archive:
        archive.extractall(extracted)
    bundle_root = next(child for child in extracted.iterdir() if child.is_dir())

    returned_archive = tmp_path / "returned.zip"
    with zipfile.ZipFile(returned_archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in bundle_root.rglob("*"):
            if path.is_file():
                archive.write(path, arcname=str(Path(bundle_root.name) / path.relative_to(bundle_root)))

    module = _load_module("import_competitor_benchmark_handoff_roundtrip_blocked", ROOT / "tools" / "import_competitor_benchmark_handoff.py")
    sandbox_root = tmp_path / "repo"
    sandbox_root.mkdir()
    monkeypatch.setattr(module, "ROOT", sandbox_root)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(module, "run_refresh", lambda: 0)

    manifest_path = sandbox_root / "build" / "reports" / "competitor_capture_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(_full_capture_manifest(), indent=2) + "\n", encoding="utf-8")

    args = module.argparse.Namespace(
        archive=str(returned_archive),
        overwrite=True,
        checksum=None,
        skip_refresh=True,
    )
    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        rc = module.main()

    assert rc == 0
    assert (sandbox_root / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_source_smoke.json").is_file()
    assert (sandbox_root / "verification_reports" / "unity_grill_baseline" / "grill_unity_import_smoke.json").is_file()
    assert (sandbox_root / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json").is_file()
    assert (sandbox_root / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.json").is_file()
    out = stdout.getvalue()
    assert "Post-import summary:" in out
