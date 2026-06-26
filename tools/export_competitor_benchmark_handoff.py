#!/usr/bin/env python3
"""Export a self-contained competitor benchmark handoff kit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import load_local_env
import refresh_engine_benchmark_artifacts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "dist" / "competitor_benchmark_handoff"
MANIFEST_NAME = "MANIFEST.json"
BASE_HANDOFF_FILES = (
    "tools/load_local_env.py",
    "tools/build_competitor_capture_manifest.py",
    "tools/validate_competitor_capture_bundle.py",
    "tools/check_competitor_handoff_workbench.py",
    "tools/init_unreal_grill_benchmark_baseline.py",
    "tools/init_unity_grill_benchmark_baseline.py",
    "tools/run_grill_unreal_source_smoke.py",
    "tools/run_grill_unity_import_smoke.py",
    "tools/build_unreal_grill_baseline_status.py",
    "tools/build_unity_grill_baseline_status.py",
    "tools/refresh_engine_benchmark_artifacts.py",
    "tools/run_engine_head_to_head_matrix.py",
    "tools/build_benchmark_coverage_report.py",
    "tools/build_scenario_contract_report.py",
    "tools/build_surface_claim_report.py",
    "tools/build_competitor_lane_summary.py",
    "schemas/json/fastdis.engine_benchmark_scenario.v1.schema.json",
    "schemas/json/fastdis.engine_benchmark_truth.v1.schema.json",
    "schemas/json/fastdis.engine_benchmark_report.v1.schema.json",
    "schemas/json/fastdis.engine_head_to_head_report.v1.schema.json",
    "schemas/json/fastdis.cross_engine_equivalence_report.v1.schema.json",
    "schemas/json/fastdis.engine_benchmark_matrix.v1.schema.json",
    "schemas/json/fastdis.benchmark_coverage_report.v1.schema.json",
    "schemas/json/fastdis.scenario_contract_report.v1.schema.json",
    "schemas/json/fastdis.surface_claim_report.v1.schema.json",
    "schemas/json/fastdis.engine_benchmark_completion_audit.v1.schema.json",
    "schemas/json/fastdis.benchmark_claim_summary.v1.schema.json",
    "schemas/json/fastdis.competitor_lane_summary.v1.schema.json",
    "schemas/json/fastdis.competitor_capture_manifest.v1.schema.json",
    "schemas/json/fastdis.competitor_capture_validation.v1.schema.json",
    "schemas/json/fastdis.competitor_benchmark_handoff_manifest.v1.schema.json",
    "tests/data/engine_benchmark_scenarios/core_matrix.v1.json",
    "tests/data/engine_benchmark_truth/core_matrix.v1.json",
    "docs/research/GRILL_COMPARISON_POLICY.md",
    "docs/research/grill_source_route.md",
    "verification_reports/unreal_grill_baseline/README.md",
    "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.template.json",
    "verification_reports/unity_grill_baseline/README.md",
    "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.template.json",
    "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
    "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md",
    "verification_reports/unity_grill_baseline/grill_unity_import_smoke.json",
    "verification_reports/unity_grill_baseline/grill_unity_import_smoke.md",
    "build/benchmark_results/current/current.json",
    "build/reports/engine_benchmarks/native_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/native_engine_benchmark_report.md",
    "build/reports/engine_benchmarks/c_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/c_engine_benchmark_report.md",
    "build/reports/engine_benchmarks/cpp_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/cpp_engine_benchmark_report.md",
    "build/reports/engine_benchmarks/python_ctypes_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/python_ctypes_engine_benchmark_report.md",
    "build/reports/engine_benchmarks/unreal_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/unreal_engine_benchmark_report.md",
    "build/reports/engine_benchmarks/unity_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/unity_engine_benchmark_report.md",
    "build/reports/engine_benchmarks/godot_engine_benchmark_report.json",
    "build/reports/engine_benchmarks/godot_engine_benchmark_report.md",
    "build/reports/network_ingest_matrix/network_ingest_matrix.json",
    "build/reports/network_ingest_matrix/network_ingest_matrix.md",
    "build/reports/cross_engine_equivalence.json",
    "build/reports/cross_engine_equivalence.md",
    "build/reports/unity_cross_engine_equivalence.json",
    "build/reports/unity_cross_engine_equivalence.md",
    "build/reports/benchmark_matrix/benchmark_matrix.json",
    "build/reports/benchmark_matrix/benchmark_matrix.md",
    "build/reports/benchmark_coverage/benchmark_coverage_report.json",
    "build/reports/benchmark_coverage/benchmark_coverage_report.md",
    "build/reports/scenario_contract/scenario_contract_report.json",
    "build/reports/scenario_contract/scenario_contract_report.md",
    "build/reports/surface_claim_report/surface_claim_report.json",
    "build/reports/surface_claim_report/surface_claim_report.md",
    "build/reports/engine_head_to_head/unreal_vs_grill_status.json",
    "build/reports/engine_head_to_head/unreal_vs_grill_status.md",
    "build/reports/engine_head_to_head/unity_vs_grill_status.json",
    "build/reports/engine_head_to_head/unity_vs_grill_status.md",
    "build/reports/competitor_capture_manifest.json",
    "build/reports/competitor_capture_manifest.md",
    "build/reports/competitor_capture_validation.json",
    "build/reports/competitor_capture_validation.md",
    "build/reports/benchmark_completion_audit/benchmark_completion_audit.json",
    "build/reports/benchmark_completion_audit/benchmark_completion_audit.md",
    "build/reports/benchmark_claim_summary/benchmark_claim_summary.json",
    "build/reports/benchmark_claim_summary/benchmark_claim_summary.md",
    "build/reports/competitor_lane_summary/competitor_lane_summary.json",
    "build/reports/competitor_lane_summary/competitor_lane_summary.md",
    "build/reports/benchmark_contract_stack/benchmark_contract_stack.json",
    "build/reports/benchmark_contract_stack/benchmark_contract_stack.md",
)


def _refresh_default_args() -> argparse.Namespace:
    return argparse.Namespace(
        skip_native_canonical=False,
        skip_current_benchmarks=False,
        skip_network_ingest_matrix=False,
        skip_network_ingest_normalize=False,
        skip_unreal_grill_baseline=False,
        skip_unity_grill_baseline=False,
        skip_unreal_proof=False,
        skip_godot_proof=False,
        skip_unity_proof=False,
        skip_cross_engine_equivalence=False,
        skip_unreal_compare=False,
        skip_unity_compare=False,
        skip_unreal_status=False,
        skip_unity_status=False,
        skip_competitor_manifest=False,
        skip_competitor_validation=False,
        skip_matrix=False,
        skip_coverage=False,
        skip_scenario_contract=False,
        skip_surface_claims=False,
        skip_completion_audit=False,
        skip_claim_summary=False,
        skip_competitor_lane_summary=False,
        skip_contract_check=False,
    )


def refresh_dependency_files() -> tuple[str, ...]:
    dependencies: list[str] = []
    for step in refresh_engine_benchmark_artifacts.build_steps(_refresh_default_args()):
        if len(step) >= 2 and isinstance(step[1], str) and step[1].startswith("tools/"):
            dependencies.append(step[1])
    return tuple(dict.fromkeys(dependencies))


def _merge_unique(*groups: tuple[str, ...]) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
    return tuple(merged)


HANDOFF_FILES = _merge_unique(BASE_HANDOFF_FILES, refresh_dependency_files())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory that will receive the archive")
    return parser.parse_args(argv)


def package_stamp() -> str:
    current = json.loads((ROOT / "build" / "benchmark_results" / "current" / "current.json").read_text(encoding="utf-8"))
    return str(current.get("generated_at_utc") or "unknown").replace(":", "").replace("-", "")


def handoff_paths() -> list[Path]:
    return [ROOT / relative for relative in HANDOFF_FILES]


def validate_handoff_paths(paths: list[Path]) -> None:
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Competitor benchmark handoff kit is missing required files:\n" + "\n".join(f"- {path}" for path in missing))


def relative_archive_paths(paths: list[Path]) -> list[tuple[Path, Path]]:
    bundle_root = Path(f"fastdis-competitor-benchmark-handoff-{package_stamp()}")
    archive_paths: list[tuple[Path, Path]] = []
    for path in paths:
        archive_paths.append((path, bundle_root / path.relative_to(ROOT)))
    return archive_paths


def build_bundle_manifest(paths: list[Path], readme_payload: str) -> dict[str, object]:
    bundle_root = f"fastdis-competitor-benchmark-handoff-{package_stamp()}"
    entries: list[dict[str, object]] = []
    total_bytes = 0
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        size_bytes = path.stat().st_size
        total_bytes += size_bytes
        entries.append(
            {
                "path": relative,
                "size_bytes": size_bytes,
                "sha256": sha256_file(path),
            }
        )
    readme_bytes = readme_payload.encode("utf-8")
    entries.append(
        {
            "path": "README.md",
            "size_bytes": len(readme_bytes),
            "sha256": hashlib.sha256(readme_bytes).hexdigest(),
        }
    )
    total_bytes += len(readme_bytes)
    return {
        "schema": "fastdis.competitor_benchmark_handoff_manifest.v1",
        "bundle_root": bundle_root,
        "package_stamp": package_stamp(),
        "file_count": len(entries),
        "total_size_bytes": total_bytes,
        "files": entries,
    }


def render_readme() -> str:
    return "\n".join(
        [
            "# Competitor Benchmark Handoff Kit",
            "",
            "This archive is intended for a host that will capture pinned GRILL",
            "benchmark baselines and return normalized shared reports for FastDIS",
            "comparison.",
            "",
            "The bundle is self-describing. Inspect `MANIFEST.json` to verify the",
            "shipped file list, sizes, and content digests before or after capture.",
            "",
            "## Included Inputs",
            "",
            "- current FastDIS benchmark source payload",
            "- current normalized FastDIS engine benchmark reports across native, C, C++, Python, Unreal, Unity, and Godot in both JSON and markdown form",
            "- current normalized C/C++ localhost UDP ingest matrix artifact in both JSON and markdown form",
            "- current benchmark matrix plus shared and Unity-specific cross-engine equivalence summaries",
            "- current benchmark capability coverage report from `build_benchmark_coverage_report.py`",
            "- current canonical shared-scenario contract report from `build_scenario_contract_report.py`",
            "- current per-surface claim-boundary report from `build_surface_claim_report.py`",
            "- machine-readable competitor capture manifest",
            "- current competitor capture validation artifact",
            "- current benchmark completion audit",
            "- current benchmark claim summary",
            "- current competitor lane summary",
            "- current benchmark contract-stack audit",
            "- benchmark contract schema files for scenarios, truth, reports, comparisons, matrix, audit, claim summary, and competitor validation",
            "- canonical benchmark scenario suite and truth suite fixtures",
            "- Unreal and Unity GRILL baseline templates",
            "- current Unreal source-smoke and Unity import-smoke blocker artifacts from this host",
            "- Unreal and Unity baseline scaffold generators",
            "- Unreal source-smoke and Unity import-smoke capture tools",
            "- Unreal and Unity GRILL baseline-status builders",
            "- current benchmark normalization and proof-bridge tools used by the shared refresh entrypoint",
            "- Unreal and Unity baseline normalizers",
            "- competitor bundle validation tool",
            "- competitor handoff workbench self-check tool",
            "- shared benchmark refresh entrypoint and its shipped dependencies",
            "- shared head-to-head comparator, equivalence, benchmark-matrix, coverage, scenario-contract, surface-claim, completion-audit, and claim-summary tools",
            "- competitor lane summary tool: `build_competitor_lane_summary.py` for measured-vs-blocked lane state",
            "- benchmark contract-stack audit tool",
            "- benchmark schema definitions",
            "",
            "## Expected Workflow",
            "",
            "1. Unzip this archive on the benchmark host.",
            "2. Scaffold the pinned GRILL baselines:",
            "",
            "```bash",
            "python tools/init_unreal_grill_benchmark_baseline.py --engine-version 5.8 --map LoopbackBench --traffic-mix '100% Entity State'",
            "python tools/init_unity_grill_benchmark_baseline.py --unity-version 6000.5.0f1 --scene LoopbackBench --traffic-mix '100% Entity State' --scripting-backend Mono",
            "```",
            "",
            "3. Review the capture manifest for required return artifacts and",
            "   capture fields, then align the run against the shipped canonical",
            "   scenario/truth fixtures:",
            "",
            "```bash",
            "python tools/build_competitor_capture_manifest.py",
            "```",
            "",
            "4. Capture host-compatibility evidence before or alongside the real",
            "   benchmark numbers:",
            "",
            "```bash",
            "python tools/run_grill_unreal_source_smoke.py --engine-version 5.8",
            "python tools/run_grill_unity_import_smoke.py --unity-version 6000.5.0f1",
            "```",
            "",
            "These artifacts are part of the required return set because blocked",
            "or failing competitor routes must remain explicit.",
            "",
            "5. Replace the scaffolded measurement rows with real same-host GRILL",
            "   numbers while keeping scenario names aligned with FastDIS cases.",
            "6. Normalize the captured baselines into shared competitor reports:",
            "",
            "```bash",
            "python tools/normalize_unreal_grill_baseline.py",
            "python tools/normalize_unity_grill_baseline.py",
            "```",
            "",
            "7. Rebuild the lane status and current benchmark packet:",
            "",
            "```bash",
            "python tools/build_unreal_grill_baseline_status.py",
            "python tools/build_unity_grill_baseline_status.py",
            "python tools/refresh_engine_benchmark_artifacts.py",
            "```",
            "",
            "Optional: validate the returned bundle contents locally before",
            "re-zipping them for import:",
            "",
            "```bash",
            "python tools/validate_competitor_capture_bundle.py .",
            "```",
            "",
            "Optional: validate that the shipped workbench itself is complete:",
            "",
            "```bash",
            "python tools/check_competitor_handoff_workbench.py . --fail-missing",
            "```",
            "",
            "6. Preferred: rerun the shared refresh entrypoint once the GRILL",
            "   baseline artifacts are populated:",
            "",
            "```bash",
            "python tools/refresh_engine_benchmark_artifacts.py",
            "```",
            "",
            "7. Or generate the side-by-side reports manually:",
            "",
            "```bash",
            "python tools/run_unreal_grill_benchmark.py",
            "python tools/run_unity_grill_benchmark.py",
            "python tools/build_cross_engine_equivalence_report.py",
            "python tools/build_benchmark_matrix_report.py",
            "python tools/audit_engine_benchmark_completion.py",
            "python tools/build_benchmark_claim_summary.py",
            "python tools/check_benchmark_contract_stack.py --fail-missing",
            "```",
            "",
            "The goal is to return current `grill_unreal_engine_benchmark_report.json`",
            "and `grill_unity_engine_benchmark_report.json` files plus the resulting",
            "head-to-head outputs, while keeping the shared benchmark matrix aligned",
            "with the exported FastDIS core surfaces, validation status, and",
            "completion audit.",
            "",
            "## Return Path",
            "",
            "Back on the aggregation checkout, import the returned archive with:",
            "",
            "```bash",
            "python -m fastdis release import-competitor-handoff <returned-archive.zip>",
            "```",
            "",
            "That adopts any returned raw baselines, normalized competitor reports,",
            "and head-to-head outputs, then refreshes the shared benchmark matrix.",
            "",
        ]
    )


def export_archive(archive_path: Path) -> Path:
    paths = handoff_paths()
    validate_handoff_paths(paths)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    readme_payload = render_readme()
    manifest_payload = json.dumps(build_bundle_manifest(paths, readme_payload), indent=2) + "\n"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in relative_archive_paths(paths):
            archive.write(source, arcname=str(arcname))
        bundle_root = Path(f"fastdis-competitor-benchmark-handoff-{package_stamp()}")
        archive.writestr(str(bundle_root / "README.md"), readme_payload)
        archive.writestr(str(bundle_root / MANIFEST_NAME), manifest_payload)
    return archive_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_archive_checksum(archive_path: Path) -> Path:
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{sha256_file(archive_path)}  {archive_path.name}\n", encoding="utf-8")
    return checksum_path


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    out_dir = Path(args.out_dir).expanduser().resolve()
    archive_path = out_dir / f"fastdis-competitor-benchmark-handoff-{package_stamp()}.zip"
    export_archive(archive_path)
    checksum_path = write_archive_checksum(archive_path)
    print(f"Exported competitor benchmark handoff archive: {archive_path}")
    print(f"Archive checksum: {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
