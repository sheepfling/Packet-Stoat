#!/usr/bin/env python3
"""Build a machine-readable manifest for same-host GRILL competitor captures."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "build" / "reports"
DEFAULT_MATRIX = ROOT / "build" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_UNREAL_STATUS = ROOT / "build" / "reports" / "engine_head_to_head" / "unreal_vs_grill_status.json"
DEFAULT_UNITY_STATUS = ROOT / "build" / "reports" / "engine_head_to_head" / "unity_vs_grill_status.json"
DEFAULT_UNREAL_REPORT = ROOT / "build" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json"
DEFAULT_UNITY_REPORT = ROOT / "build" / "reports" / "engine_benchmarks" / "unity_engine_benchmark_report.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--unreal-status", type=Path, default=DEFAULT_UNREAL_STATUS)
    parser.add_argument("--unity-status", type=Path, default=DEFAULT_UNITY_STATUS)
    parser.add_argument("--unreal-report", type=Path, default=DEFAULT_UNREAL_REPORT)
    parser.add_argument("--unity-report", type=Path, default=DEFAULT_UNITY_REPORT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "competitor_capture_manifest.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "competitor_capture_manifest.md")
    return parser.parse_args(argv)


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def report_scenarios(payload: dict[str, Any] | None) -> list[str]:
    rows = payload.get("rows") if isinstance(payload, dict) and isinstance(payload.get("rows"), list) else []
    return [str(row.get("scenario")) for row in rows if isinstance(row, dict) and isinstance(row.get("scenario"), str)]


def host_summary(payload: dict[str, Any] | None) -> dict[str, Any]:
    host = payload.get("host") if isinstance(payload, dict) and isinstance(payload.get("host"), dict) else {}
    return dict(host)


def build_manifest(
    matrix_payload: dict[str, Any] | None,
    unreal_status_payload: dict[str, Any] | None,
    unity_status_payload: dict[str, Any] | None,
    unreal_report_payload: dict[str, Any] | None,
    unity_report_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    unreal_scenarios = report_scenarios(unreal_report_payload)
    unity_scenarios = report_scenarios(unity_report_payload)
    matrix_gaps = matrix_payload.get("gaps") if isinstance(matrix_payload, dict) and isinstance(matrix_payload.get("gaps"), list) else []

    common_requirements = [
        "capture on the same physical host class used for the paired FastDIS report",
        "keep scenario names aligned with the FastDIS shared report rows",
        "return normalized grill_*_engine_benchmark_report.json and .md output, not only raw notes",
        "include host OS, engine version, plugin version/commit, traffic mix, and scene/map identifiers",
        "do not claim direct support if the competitor plugin failed to install or run on that host",
    ]

    return {
        "schema": "fastdis.competitor_capture_manifest.v1",
        "generated_at_utc": utc_now(),
        "note": "This manifest defines the minimum same-host evidence required before GRILL comparison claims can move from blocked to supported.",
        "global_claim_boundaries": [
            "A normalized competitor report is necessary but not sufficient; it must also be same-host and scenario-aligned.",
            "Wall-clock runtime rows are acceptable for runtime-lane evidence, but they are not parser-speed claims.",
            "If the competitor import/install lane fails, return the failure artifact instead of fabricated benchmark numbers.",
        ],
        "matrix_gaps": matrix_gaps,
        "common_requirements": common_requirements,
        "lanes": [
            {
                "lane": "unreal_vs_grill",
                "status": unreal_status_payload.get("status") if isinstance(unreal_status_payload, dict) else "missing",
                "blockers": unreal_status_payload.get("blockers") if isinstance(unreal_status_payload, dict) and isinstance(unreal_status_payload.get("blockers"), list) else [],
                "fastdis_report": display_path(DEFAULT_UNREAL_REPORT),
                "fastdis_host": host_summary(unreal_report_payload),
                "fastdis_scenarios": unreal_scenarios,
                "required_return_artifacts": [
                    "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
                    "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.md",
                    "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
                    "artifacts/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
                    "artifacts/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.md",
                    "artifacts/reports/engine_head_to_head/unreal_vs_grill.json",
                    "artifacts/reports/engine_head_to_head/unreal_vs_grill.md",
                    "artifacts/reports/engine_head_to_head/unreal_vs_grill_status.json",
                    "artifacts/reports/engine_head_to_head/unreal_vs_grill_status.md",
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
            },
            {
                "lane": "unity_vs_grill",
                "status": unity_status_payload.get("status") if isinstance(unity_status_payload, dict) else "missing",
                "blockers": unity_status_payload.get("blockers") if isinstance(unity_status_payload, dict) and isinstance(unity_status_payload.get("blockers"), list) else [],
                "fastdis_report": display_path(DEFAULT_UNITY_REPORT),
                "fastdis_host": host_summary(unity_report_payload),
                "fastdis_scenarios": unity_scenarios,
                "required_return_artifacts": [
                    "verification_reports/unity_grill_baseline/grill_unity_import_smoke.json",
                    "verification_reports/unity_grill_baseline/grill_unity_import_smoke.md",
                    "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json",
                    "artifacts/reports/engine_benchmarks/grill_unity_engine_benchmark_report.json",
                    "artifacts/reports/engine_benchmarks/grill_unity_engine_benchmark_report.md",
                    "artifacts/reports/engine_head_to_head/unity_vs_grill.json",
                    "artifacts/reports/engine_head_to_head/unity_vs_grill.md",
                    "artifacts/reports/engine_head_to_head/unity_vs_grill_status.json",
                    "artifacts/reports/engine_head_to_head/unity_vs_grill_status.md",
                ],
                "required_capture_fields": [
                    "host.system",
                    "host.machine",
                    "unity.version",
                    "scenario.scene",
                    "scenario.traffic_mix",
                    "results[].case",
                    "results[].packets_per_sec",
                    "results[].main_thread_ms_avg",
                    "results[].gc_alloc_bytes_per_frame",
                ],
            },
        ],
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Competitor Capture Manifest",
        "",
        manifest["note"],
        "",
        "## Global Claim Boundaries",
        "",
    ]
    for line in manifest["global_claim_boundaries"]:
        lines.append(f"- {line}")
    lines.extend(["", "## Common Requirements", ""])
    for line in manifest["common_requirements"]:
        lines.append(f"- {line}")
    lines.extend(["", "## Lanes", ""])
    for lane in manifest["lanes"]:
        lines.extend(
            [
                f"### {lane['lane']}",
                "",
                f"- status: `{lane['status']}`",
                f"- fastdis_report: `{lane['fastdis_report']}`",
                f"- fastdis_scenarios: `{', '.join(lane['fastdis_scenarios']) if lane['fastdis_scenarios'] else 'none'}`",
                "",
                "Required return artifacts:",
            ]
        )
        for item in lane["required_return_artifacts"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "Required capture fields:"])
        for item in lane["required_capture_fields"]:
            lines.append(f"- `{item}`")
        if lane["blockers"]:
            lines.extend(["", "Current blockers:"])
            for item in lane["blockers"]:
                lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_manifest(
        load_json(args.matrix),
        load_json(args.unreal_status),
        load_json(args.unity_status),
        load_json(args.unreal_report),
        load_json(args.unity_report),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(manifest) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
