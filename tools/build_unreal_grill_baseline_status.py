#!/usr/bin/env python3
"""Summarize the current Unreal-vs-GRILL baseline readiness state."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FASTDIS = ROOT / "artifacts" / "reports" / "engine_benchmarks" / "unreal_engine_benchmark_report.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_head_to_head"
DEFAULT_SOURCE_SMOKE = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_source_smoke.json"
DEFAULT_MAPPING_EXPORT = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_export_report.json"
DEFAULT_MAPPING_MATERIALIZE = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_mapping_materialize_report.json"
DEFAULT_LINUX_BUILD_PROOF = ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_linux_build_proof.json"
DEFAULT_GRILL_CANDIDATES = [
    ROOT / "artifacts" / "reports" / "engine_benchmarks" / "grill_unreal_engine_benchmark_report.json",
    ROOT / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_engine_benchmark_report.json",
    ROOT / "tests" / "data" / "engine_benchmark_reports" / "grill_unreal.sample.json",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--source-smoke", type=Path, default=DEFAULT_SOURCE_SMOKE)
    parser.add_argument("--mapping-export", type=Path, default=DEFAULT_MAPPING_EXPORT)
    parser.add_argument("--mapping-materialize", type=Path, default=DEFAULT_MAPPING_MATERIALIZE)
    parser.add_argument("--linux-build-proof", type=Path, default=DEFAULT_LINUX_BUILD_PROOF)
    parser.add_argument("--grill-report", dest="grill_reports", type=Path, action="append", help="Candidate GRILL Unreal shared report path")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "unreal_vs_grill_status.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "unreal_vs_grill_status.md")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def classify_path(path: Path) -> str:
    if "/samples/" in path.as_posix() or ".sample." in path.name:
        return "sample"
    return "current"


def _evidence_payload(path: Path) -> dict[str, Any] | None:
    return load_json(path) if path.exists() else None


def _evidence_summary(path: Path, payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "path": display_path(path),
            "present": False,
            "status": None,
            "failure_kind": None,
            "failure_detail": None,
        }
    return {
        "path": display_path(path),
        "present": True,
        "status": payload.get("status"),
        "failure_kind": payload.get("failure_kind"),
        "failure_detail": payload.get("failure_detail") or payload.get("detail"),
    }


def build_report(
    fastdis_path: Path,
    *,
    source_smoke_path: Path,
    mapping_export_path: Path,
    mapping_materialize_path: Path,
    linux_build_proof_path: Path,
    grill_candidates: list[Path],
) -> dict[str, Any]:
    fastdis_exists = fastdis_path.exists()
    fastdis_payload = load_json(fastdis_path) if fastdis_exists else None
    source_smoke_payload = _evidence_payload(source_smoke_path)
    mapping_export_payload = _evidence_payload(mapping_export_path)
    mapping_materialize_payload = _evidence_payload(mapping_materialize_path)
    linux_build_proof_payload = _evidence_payload(linux_build_proof_path)
    grill_present = []
    for candidate in grill_candidates:
        if candidate.exists():
            grill_present.append(
                {
                    "path": display_path(candidate),
                    "classification": classify_path(candidate),
                }
            )

    blockers: list[str] = []
    if not fastdis_exists:
        blockers.append("current FastDIS Unreal shared report missing")
    if not any(row["classification"] == "current" for row in grill_present):
        blockers.append("no current GRILL Unreal shared benchmark report present")
    source_smoke_status = source_smoke_payload.get("status") if isinstance(source_smoke_payload, dict) else None
    if source_smoke_status not in {None, "pass"}:
        blockers.append("current host GRILL Unreal source smoke failed")
    mapping_export_status = mapping_export_payload.get("status") if isinstance(mapping_export_payload, dict) else None
    mapping_materialize_status = mapping_materialize_payload.get("status") if isinstance(mapping_materialize_payload, dict) else None
    if mapping_export_status not in {None, "ok", "dry-run"}:
        blockers.append("current host GRILL Unreal mapping export failed")
    if mapping_materialize_status not in {None, "ok", "dry-run"}:
        blockers.append("current host GRILL Unreal mapping materialize failed")
    linux_build_proof_status = linux_build_proof_payload.get("status") if isinstance(linux_build_proof_payload, dict) else None
    if linux_build_proof_status not in {None, "pass"}:
        blockers.append("current GRILL Unreal Linux build proof is missing or failed")

    status = "ready" if not blockers else "blocked_on_grill_baseline"
    if blockers:
        note = "A real Unreal-vs-GRILL same-host head-to-head report requires a current GRILL Unreal shared benchmark report and a GRILL-compatible host."
        export_failure_kind = mapping_export_payload.get("failure_kind") if isinstance(mapping_export_payload, dict) else None
        materialize_failure_kind = mapping_materialize_payload.get("failure_kind") if isinstance(mapping_materialize_payload, dict) else None
        if export_failure_kind == materialize_failure_kind == "missing-game-module":
            note = (
                "A real Unreal-vs-GRILL same-host head-to-head report is blocked on this Mac/UE5.8 route because the public GRILL example cannot "
                "load its game module after Unreal skips incompatible public GRILL plugins and encounters unloadable example assets."
            )
    else:
        note = "Both sides have current shared benchmark reports and can be compared."

    return {
        "schema": "fastdis.unreal_grill_baseline_status.v1",
        "generated_at_utc": utc_now(),
        "status": status,
        "note": note,
        "fastdis": {
            "path": display_path(fastdis_path),
            "exists": fastdis_exists,
            "surface": fastdis_payload.get("surface") if isinstance(fastdis_payload, dict) else None,
            "evidence_kind": classify_path(fastdis_path) if fastdis_exists else None,
        },
        "source_smoke": {
            **_evidence_summary(source_smoke_path, source_smoke_payload),
        },
        "mapping_export": _evidence_summary(mapping_export_path, mapping_export_payload),
        "mapping_materialize": _evidence_summary(mapping_materialize_path, mapping_materialize_payload),
        "linux_build_proof": _evidence_summary(linux_build_proof_path, linux_build_proof_payload),
        "grill_candidates": grill_present,
        "blockers": blockers,
        "next_steps": [
            "Keep the Linux build proof current with `python tools/unreal_workflow.py grill-linux-proof` after each GRILL portability rerun.",
            "Capture a current GRILL Unreal shared benchmark report on a GRILL-compatible Unreal host.",
            "Rerun the shared head-to-head comparator with current FastDIS and GRILL Unreal reports.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Unreal vs GRILL Baseline Status",
        "",
        f"- status: `{report['status']}`",
        "",
        report["note"],
        "",
        "## FastDIS",
        "",
        f"- path: `{report['fastdis']['path']}`",
        f"- exists: `{report['fastdis']['exists']}`",
        f"- surface: `{report['fastdis']['surface']}`",
        "",
        "## Source Smoke",
        "",
        f"- path: `{report['source_smoke']['path']}`",
        f"- status: `{report['source_smoke']['status']}`",
        f"- failure_kind: `{report['source_smoke']['failure_kind']}`",
        "",
        "## Mapping Export",
        "",
        f"- path: `{report['mapping_export']['path']}`",
        f"- present: `{report['mapping_export']['present']}`",
        f"- status: `{report['mapping_export']['status']}`",
        f"- failure_kind: `{report['mapping_export']['failure_kind']}`",
        f"- failure_detail: `{report['mapping_export']['failure_detail']}`",
        "",
        "## Mapping Materialize",
        "",
        f"- path: `{report['mapping_materialize']['path']}`",
        f"- present: `{report['mapping_materialize']['present']}`",
        f"- status: `{report['mapping_materialize']['status']}`",
        f"- failure_kind: `{report['mapping_materialize']['failure_kind']}`",
        f"- failure_detail: `{report['mapping_materialize']['failure_detail']}`",
        "",
        "## Linux Build Proof",
        "",
        f"- path: `{report['linux_build_proof']['path']}`",
        f"- present: `{report['linux_build_proof']['present']}`",
        f"- status: `{report['linux_build_proof']['status']}`",
        f"- failure_kind: `{report['linux_build_proof']['failure_kind']}`",
        f"- failure_detail: `{report['linux_build_proof']['failure_detail']}`",
        "",
        "## GRILL Candidates",
        "",
    ]
    if report["grill_candidates"]:
        for row in report["grill_candidates"]:
            lines.append(f"- `{row['path']}` classification=`{row['classification']}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Blockers", ""])
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    grill_candidates = args.grill_reports or DEFAULT_GRILL_CANDIDATES
    report = build_report(
        args.fastdis,
        source_smoke_path=args.source_smoke,
        mapping_export_path=args.mapping_export,
        mapping_materialize_path=args.mapping_materialize,
        linux_build_proof_path=args.linux_build_proof,
        grill_candidates=grill_candidates,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
