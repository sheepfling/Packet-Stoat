#!/usr/bin/env python3
"""Import a competitor benchmark handoff archive and adopt returned baseline/report artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import importlib.util
import zipfile

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
OPTIONAL_IMPORTS = (
    "artifacts/reports/benchmark_matrix/benchmark_matrix.json",
    "artifacts/reports/benchmark_matrix/benchmark_matrix.md",
    "artifacts/reports/benchmark_coverage/benchmark_coverage_report.json",
    "artifacts/reports/benchmark_coverage/benchmark_coverage_report.md",
    "artifacts/reports/scenario_contract/scenario_contract_report.json",
    "artifacts/reports/scenario_contract/scenario_contract_report.md",
    "artifacts/reports/surface_claim_report/surface_claim_report.json",
    "artifacts/reports/surface_claim_report/surface_claim_report.md",
    "artifacts/reports/competitor_capture_manifest.json",
    "artifacts/reports/competitor_capture_manifest.md",
    "artifacts/reports/competitor_capture_validation.json",
    "artifacts/reports/competitor_capture_validation.md",
    "artifacts/reports/benchmark_completion_audit/benchmark_completion_audit.json",
    "artifacts/reports/benchmark_completion_audit/benchmark_completion_audit.md",
    "artifacts/reports/benchmark_claim_summary/benchmark_claim_summary.json",
    "artifacts/reports/benchmark_claim_summary/benchmark_claim_summary.md",
    "artifacts/reports/competitor_lane_summary/competitor_lane_summary.json",
    "artifacts/reports/competitor_lane_summary/competitor_lane_summary.md",
    "artifacts/reports/benchmark_contract_stack/benchmark_contract_stack.json",
    "artifacts/reports/benchmark_contract_stack/benchmark_contract_stack.md",
    "artifacts/verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
    "artifacts/verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
    "artifacts/verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md",
    "artifacts/verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json",
    "artifacts/verification_reports/unity_grill_baseline/grill_unity_import_smoke.json",
    "artifacts/verification_reports/unity_grill_baseline/grill_unity_import_smoke.md",
    "artifacts/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
    "artifacts/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md",
    "artifacts/reports/engine_benchmarks/grill_unity_engine_benchmark_report.json",
    "artifacts/reports/engine_benchmarks/grill_unity_engine_benchmark_report.md",
    "artifacts/reports/engine_head_to_head/unreal_vs_grill.json",
    "artifacts/reports/engine_head_to_head/unreal_vs_grill.md",
    "artifacts/reports/engine_head_to_head/unreal_vs_grill_status.json",
    "artifacts/reports/engine_head_to_head/unreal_vs_grill_status.md",
    "artifacts/reports/engine_head_to_head/unity_vs_grill.json",
    "artifacts/reports/engine_head_to_head/unity_vs_grill.md",
    "artifacts/reports/engine_head_to_head/unity_vs_grill_status.json",
    "artifacts/reports/engine_head_to_head/unity_vs_grill_status.md",
)


def _load_tool_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_tool_module("validate_competitor_capture_bundle", "tools/validate_competitor_capture_bundle.py")
WORKBENCH = _load_tool_module("check_competitor_handoff_workbench", "tools/check_competitor_handoff_workbench.py")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Zip archive produced by export_competitor_benchmark_handoff.py and optionally filled on a benchmark host")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing adopted files")
    parser.add_argument("--checksum", help="Optional .sha256 sidecar to verify before import")
    parser.add_argument("--skip-refresh", action="store_true", help="Do not rerun tools/refresh_engine_benchmark_artifacts.py after import")
    return parser.parse_args(argv)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive_checksum(archive_path: Path, checksum_path: Path) -> None:
    line = checksum_path.read_text(encoding="utf-8").strip()
    expected, _, recorded_name = line.partition("  ")
    if not expected or recorded_name != archive_path.name:
        raise ValueError(f"Checksum file has unexpected format: {checksum_path}")
    actual = sha256_file(archive_path)
    if actual != expected:
        raise ValueError(f"Archive checksum mismatch for {archive_path.name}: expected {expected}, got {actual}")


def extracted_bundle_root(tmp_root: Path) -> Path:
    children = [child for child in tmp_root.iterdir() if child.is_dir()]
    if len(children) != 1:
        raise ValueError("Imported archive must contain exactly one top-level bundle directory")
    return children[0]


def validate_bundle(bundle_root: Path) -> dict:
    workbench = WORKBENCH.build_report(bundle_root)
    if workbench.get("status") != "pass":
        raise ValueError("Returned competitor bundle failed workbench validation")
    manifest_path = ROOT / "artifacts" / "reports" / "competitor_capture_manifest.json"
    manifest_payload = VALIDATOR.load_json(manifest_path)
    validation = VALIDATOR.validate_bundle_from_manifest(bundle_root, manifest_payload, if_available=True)
    status = validation.get("status")
    if status not in {"pass", "skipped"}:
        raise ValueError("Returned competitor bundle failed validation")
    if status == "skipped":
        lanes = validation.get("lanes")
        if not isinstance(lanes, list) or not any(
            isinstance(lane, dict) and lane.get("artifact_mode") == "blocked_evidence_only"
            for lane in lanes
        ):
            raise ValueError("Returned competitor bundle did not contain benchmark captures or blocked evidence")
    return validation


def load_json_if_present(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def adopt_files(bundle_root: Path, *, overwrite: bool) -> list[Path]:
    adopted: list[Path] = []
    for relative in OPTIONAL_IMPORTS:
        source = bundle_root / relative
        if not source.is_file():
            continue
        dest = ROOT / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {dest}")
        if dest.exists():
            dest.unlink()
        shutil.copy2(source, dest)
        adopted.append(dest)
    return adopted


def post_import_summary_lines() -> list[str]:
    lines: list[str] = []
    lane_summary = load_json_if_present(ROOT / "artifacts" / "reports" / "competitor_lane_summary" / "competitor_lane_summary.json")
    if isinstance(lane_summary, dict):
        summary = lane_summary.get("summary") if isinstance(lane_summary.get("summary"), dict) else {}
        lines.append(
            "competitor_lane_summary: "
            f"status={lane_summary.get('status', 'unknown')} "
            f"measured={summary.get('measured_claim_ready_count', 0)} "
            f"blocked={summary.get('blocked_lane_count', 0)} "
            f"blocked_evidence={summary.get('blocked_evidence_lane_count', 0)}"
        )
        lanes = lane_summary.get("lanes")
        if isinstance(lanes, list):
            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                lines.append(
                    f"  {lane.get('lane', 'unknown')}: "
                    f"state={lane.get('current_state', 'unknown')} "
                    f"publishable={lane.get('direct_claim_publishable', False)} "
                    f"blocked_evidence={lane.get('blocked_evidence_available', False)}"
                )

    validation = load_json_if_present(ROOT / "artifacts" / "reports" / "competitor_capture_validation.json")
    if isinstance(validation, dict):
        lines.append(f"competitor_capture_validation: {validation.get('status', 'unknown')}")
        lanes = validation.get("lanes")
        if isinstance(lanes, list):
            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                lines.append(
                    f"  {lane.get('lane', 'unknown')}: "
                    f"artifact_mode={lane.get('artifact_mode', 'unknown')} "
                    f"present={lane.get('present', False)}"
                )

    if not isinstance(lane_summary, dict):
        for label, relative in (
            ("unreal_baseline_status", "artifacts/reports/engine_head_to_head/unreal_vs_grill_status.json"),
            ("unity_baseline_status", "artifacts/reports/engine_head_to_head/unity_vs_grill_status.json"),
        ):
            payload = load_json_if_present(ROOT / relative)
            if not isinstance(payload, dict):
                continue
            status = payload.get("status", "unknown")
            blockers = payload.get("blockers")
            if isinstance(blockers, list) and blockers:
                lines.append(f"{label}: {status} ({'; '.join(str(item) for item in blockers[:2])})")
            else:
                lines.append(f"{label}: {status}")

    claim_summary = load_json_if_present(ROOT / "artifacts" / "reports" / "benchmark_claim_summary/benchmark_claim_summary.json")
    if isinstance(claim_summary, dict):
        summary = claim_summary.get("summary")
        if isinstance(summary, dict):
            lines.append(
                "claim_summary: "
                f"publishable={summary.get('publishable_claim_count', 0)} "
                f"blocked={summary.get('blocked_claim_count', 0)} "
                f"blocked_evidence_lanes={summary.get('blocked_evidence_lane_count', 0)}"
            )
    return lines


def run_refresh() -> int:
    import subprocess
    import sys

    cmd = [sys.executable, "tools/refresh_engine_benchmark_artifacts.py"]
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT).returncode


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    archive_path = Path(args.archive).expanduser().resolve()
    checksum_path = Path(args.checksum).expanduser().resolve() if args.checksum else archive_path.with_suffix(archive_path.suffix + ".sha256")
    if checksum_path.exists():
        verify_archive_checksum(archive_path, checksum_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(tmp_root)
        bundle_root = extracted_bundle_root(tmp_root)
        validate_bundle(bundle_root)
        adopted = adopt_files(bundle_root, overwrite=bool(args.overwrite))

    if not adopted:
        print("No returned competitor benchmark artifacts were present in the archive.")
    else:
        for path in adopted:
            print(f"Adopted: {path.relative_to(ROOT)}")

    if not args.skip_refresh:
        code = run_refresh()
        if code != 0:
            return code
    summary_lines = post_import_summary_lines()
    if summary_lines:
        print("Post-import summary:")
        for line in summary_lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
