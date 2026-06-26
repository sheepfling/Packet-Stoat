from __future__ import annotations

import importlib.util
import hashlib
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


def _load_fixture(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_handoff_manifest(bundle_root: Path, file_paths: list[Path]) -> None:
    entries = []
    for path in file_paths:
        relative = path.relative_to(bundle_root).as_posix()
        payload = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "schema": "fastdis.competitor_benchmark_handoff_manifest.v1",
        "bundle_root": bundle_root.name,
        "package_stamp": "test",
        "file_count": len(entries),
        "total_size_bytes": sum(entry["size_bytes"] for entry in entries),
        "files": entries,
    }
    _write_json(bundle_root / "MANIFEST.json", manifest)


def _unreal_manifest() -> dict:
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
                    "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
                    "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md",
                    "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
                    "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
                    "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md",
                    "build/reports/engine_head_to_head/unreal_vs_grill.json",
                    "build/reports/engine_head_to_head/unreal_vs_grill.md",
                    "build/reports/engine_head_to_head/unreal_vs_grill_status.json",
                    "build/reports/engine_head_to_head/unreal_vs_grill_status.md",
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


def _write_valid_unreal_bundle(bundle_root: Path) -> None:
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
            "notes": "Same host as FastDIS Unreal sample.",
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
    right = _load_fixture("tests/data/engine_benchmark_reports/grill_unreal.sample.json")
    left = _load_fixture("tests/data/engine_benchmark_reports/fastdis_unreal.sample.json")
    head_module = _load_module("run_engine_head_to_head_matrix", ROOT / "tools" / "run_engine_head_to_head_matrix.py")
    report = head_module.build_report(
        left,
        right,
        left_path=ROOT / "tests/data/engine_benchmark_reports/fastdis_unreal.sample.json",
        right_path=ROOT / "tests/data/engine_benchmark_reports/grill_unreal.sample.json",
        left_label="FastDIS Unreal",
        right_label="GRILL Unreal",
    )
    smoke = {
        "schema": "fastdis.grill_unreal_source_smoke.v1",
        "status": "pass",
        "host_platform": "Darwin",
        "requested_engine_version": "5.8",
        "resolved_engine_version": "5.8",
    }
    status = {
        "schema": "fastdis.unreal_grill_baseline_status.v1",
        "status": "ready",
        "blockers": [],
    }

    _write_json(bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json", smoke)
    _write_text(bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md", "# GRILL Unreal Source Smoke\n")
    _write_json(bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json", raw)
    _write_json(bundle_root / "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json", right)
    _write_text(bundle_root / "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md", "# GRILL Unreal Benchmark Report\n")
    _write_json(bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill.json", report)
    _write_text(bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill.md", "# Unreal vs GRILL\n")
    _write_json(bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill_status.json", status)
    _write_text(bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill_status.md", "# Unreal vs GRILL Status\n")
    _write_text(bundle_root / "README.md", "# Returned competitor bundle\n")
    _write_handoff_manifest(
        bundle_root,
        [
            bundle_root / "README.md",
            bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
            bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md",
            bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
            bundle_root / "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
            bundle_root / "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md",
            bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill.json",
            bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill.md",
            bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill_status.json",
            bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill_status.md",
        ],
    )


def test_validate_bundle_from_manifest_accepts_valid_unreal_bundle(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_valid_unreal_bundle(bundle_root)

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest())

    assert validation["status"] == "pass"
    assert validation["active_lane_count"] == 1
    assert validation["handoff_workbench"]["status"] == "pass"
    assert validation["handoff_workbench"]["summary"]["manifest_present"] is True
    assert validation["handoff_workbench"]["summary"]["manifest_valid"] is True
    assert validation["handoff_workbench"]["summary"]["bundle_kind"] == "archive_bundle"
    assert validation["handoff_workbench"]["summary"]["self_describing_bundle"] is True
    lane = validation["lanes"][0]
    assert lane["present"] is True
    assert lane["artifact_mode"] == "benchmark_capture"
    assert sorted(lane["shared_scenarios"]) == ["entity_state_100x30hz", "entity_state_1x10hz"]
    assert lane["errors"] == []


def test_validate_bundle_from_manifest_rejects_missing_required_artifact(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_valid_unreal_bundle(bundle_root)
    (bundle_root / "build/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md").unlink()

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest())

    assert validation["status"] == "fail"
    assert validation["handoff_workbench"]["status"] == "fail"
    assert any("embedded handoff workbench validation" in error for error in validation["errors"])
    lane_errors = validation["lanes"][0]["errors"]
    assert any("grill_unreal_engine_benchmark_report.md" in error for error in lane_errors)


def test_validate_bundle_from_manifest_rejects_missing_capture_field(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_valid_unreal_bundle(bundle_root)
    raw_path = bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["scenario"]["map"] = ""
    _write_json(raw_path, raw)

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest())

    assert validation["status"] == "fail"
    lane_errors = validation["lanes"][0]["errors"]
    assert any("scenario.map" in error for error in lane_errors)


def test_validate_bundle_from_manifest_rejects_scenario_mismatch(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_valid_unreal_bundle(bundle_root)
    manifest = _unreal_manifest()
    manifest["lanes"][0]["fastdis_scenarios"] = ["unreal_packaged_install_runtime"]

    validation = module.validate_bundle_from_manifest(bundle_root, manifest)

    assert validation["status"] == "fail"
    lane_errors = validation["lanes"][0]["errors"]
    assert any("no shared scenarios" in error for error in lane_errors)


def test_validate_competitor_capture_bundle_cli_writes_outputs(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_valid_unreal_bundle(bundle_root)
    manifest_path = tmp_path / "manifest.json"
    json_out = tmp_path / "out" / "validation.json"
    md_out = tmp_path / "out" / "validation.md"
    _write_json(manifest_path, _unreal_manifest())

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_competitor_capture_bundle.py"),
            str(bundle_root),
            "--manifest",
            str(manifest_path),
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
    assert payload["schema"] == "fastdis.competitor_capture_validation.v1"
    assert payload["status"] == "pass"
    assert payload["handoff_workbench"]["status"] == "pass"
    assert payload["handoff_workbench"]["summary"]["bundle_kind"] == "archive_bundle"
    assert "Competitor Capture Validation" in md_out.read_text(encoding="utf-8")
    assert "Handoff Workbench" in md_out.read_text(encoding="utf-8")


def test_validate_bundle_from_manifest_can_skip_when_no_lane_artifacts_present(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest(), if_available=True)

    assert validation["status"] == "skipped"
    assert validation["active_lane_count"] == 0
    assert validation["errors"] == []
    assert validation["handoff_workbench"]["status"] == "fail"
    assert validation["handoff_workbench"]["summary"]["bundle_kind"] == "local_checkout"
    assert validation["handoff_workbench"]["summary"]["self_describing_bundle"] is False


def test_validate_bundle_from_manifest_ignores_head_to_head_without_returned_baseline(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_text(bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill.md", "# Unreal vs GRILL\n")
    _write_json(
        bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill.json",
        {
            "schema": "fastdis.engine_head_to_head_report.v1",
            "status": "directional_only",
            "comparison": {"same_host": False, "matched_scenarios": 0},
        },
    )

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest(), if_available=True)

    assert validation["status"] == "skipped"
    assert validation["active_lane_count"] == 0


def test_validate_bundle_from_manifest_records_missing_handoff_manifest_without_lane_failure_when_empty(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle_missing_manifest", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_text(bundle_root / "README.md", "# Returned competitor bundle\n")

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest(), if_available=True)

    assert validation["status"] == "skipped"
    assert validation["handoff_workbench"]["summary"]["manifest_present"] is False
    assert validation["handoff_workbench"]["summary"]["manifest_valid"] is False
    assert validation["handoff_workbench"]["summary"]["bundle_kind"] == "local_checkout"
    assert validation["handoff_workbench"]["summary"]["self_describing_bundle"] is False
    assert validation["lanes"][0]["artifact_mode"] == "empty"


def test_validate_bundle_from_manifest_classifies_blocked_evidence_only_lane(tmp_path: Path) -> None:
    module = _load_module("validate_competitor_capture_bundle_blocked", ROOT / "tools" / "validate_competitor_capture_bundle.py")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    _write_text(bundle_root / "README.md", "# Returned competitor bundle\n")
    _write_json(
        bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
        {
            "schema": "fastdis.grill_unreal_source_smoke.v1",
            "status": "blocked-host-platform",
        },
    )
    _write_text(bundle_root / "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md", "# GRILL Unreal Source Smoke\n")
    _write_json(
        bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill_status.json",
        {
            "schema": "fastdis.unreal_grill_baseline_status.v1",
            "status": "blocked_on_grill_baseline",
            "blockers": ["plugin manifest does not allow host platform Mac"],
        },
    )
    _write_text(bundle_root / "build/reports/engine_head_to_head/unreal_vs_grill_status.md", "# Unreal vs GRILL Status\n")

    validation = module.validate_bundle_from_manifest(bundle_root, _unreal_manifest(), if_available=True)

    assert validation["status"] == "skipped"
    assert validation["active_lane_count"] == 0
    lane = validation["lanes"][0]
    assert lane["present"] is False
    assert lane["artifact_mode"] == "blocked_evidence_only"
