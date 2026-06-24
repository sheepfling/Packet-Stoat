#!/usr/bin/env python3
"""Generate an evidence-backed Epic 2 audit report from the current tree."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

from artifacts import REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import check_evidence_pack


DEFAULT_OUT_DIR = REPORTS_DIR / "epic2"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_rows(paths: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        rows.append(
            {
                "path": display_path(path),
                "exists": path.exists(),
                "kind": "file" if path.is_file() else ("dir" if path.is_dir() else "missing"),
            }
        )
    return rows


def _status(*, complete: bool, partial: bool) -> str:
    if complete:
        return "complete"
    if partial:
        return "partial"
    return "missing_evidence"


def audit_generated_truth() -> dict[str, object]:
    coverage_path = ROOT / "generated" / "pdu_coverage_manifest.json"
    endpoint_path = ROOT / "generated" / "endpoint_mapping_manifest.json"
    logging_path = ROOT / "generated" / "pdu_log_catalog.json"
    lattice_path = ROOT / "generated" / "lattice_dis_mapping_plan.json"
    coverage = load_json(coverage_path)
    endpoint = load_json(endpoint_path)
    logging = load_json(logging_path)
    lattice = load_json(lattice_path)
    evidence = evidence_rows([coverage_path, endpoint_path, logging_path, lattice_path])

    metrics = {
        "standard_total_rows": coverage["summary"]["standard_total_rows"] if coverage else None,
        "xml_catalog_total_rows": coverage["summary"]["xml_catalog_total_rows"] if coverage else None,
        "catalog_gap_rows": coverage["summary"]["catalog_gap_rows"] if coverage else None,
        "endpoint_records": endpoint["summary"]["records"] if endpoint else None,
        "missing_endpoint_behavior": endpoint["summary"]["missing_endpoint_behavior"] if endpoint else None,
        "logging_descriptors": logging["summary"]["records"] if logging else None,
        "lattice_records": lattice["summary"]["records"] if lattice else None,
    }
    complete = bool(
        coverage
        and endpoint
        and logging
        and lattice
        and coverage["summary"]["standard_total_rows"] == 141
        and coverage["summary"]["xml_catalog_total_rows"] == 141
        and coverage["summary"]["catalog_gap_rows"] == 0
        and endpoint["summary"]["records"] == 141
        and endpoint["summary"]["missing_endpoint_behavior"] == 0
        and logging["summary"]["records"] == 141
        and lattice["summary"]["records"] == 141
    )
    note = (
        "All 141 standard rows are now explicit across coverage, endpoint behavior, logging, "
        "and Lattice/Zorn mapping manifests."
        if complete
        else "One or more generated truth manifests are missing rows or still report explicit gaps."
    )
    return {
        "name": "141-row generated truth",
        "status": _status(complete=complete, partial=bool(coverage or endpoint or logging or lattice)),
        "note": note,
        "metrics": metrics,
        "evidence": evidence,
    }


def audit_wire_and_field_coverage() -> dict[str, object]:
    coverage_path = ROOT / "generated" / "pdu_coverage_manifest.json"
    typed_path = ROOT / "generated" / "typed_pdu_parser_manifest.json"
    translation_path = ROOT / "generated" / "version_translation_manifest.json"
    fuzz_path = ROOT / "generated" / "fuzz_shallow_corpus" / "manifest.json"
    coverage = load_json(coverage_path)
    typed = load_json(typed_path)
    translation = load_json(translation_path)
    fuzz = load_json(fuzz_path)
    evidence = evidence_rows([coverage_path, typed_path, translation_path, fuzz_path])

    metrics = {
        "safe_ingest_rows": coverage["summary"]["safe_ingest_rows"] if coverage else None,
        "generic_endpoint_rows": coverage["summary"]["generic_endpoint_rows"] if coverage else None,
        "field_visitor_rows": coverage["summary"]["field_visitor_rows"] if coverage else None,
        "typed_structural_rows": typed["summary"]["typed_structural"] if typed else None,
        "translation_rows": translation["summary"]["translation_rows"] if translation else None,
        "fuzz_catalog_entry_count": fuzz["catalog_entry_count"] if fuzz else None,
        "fuzz_seed_count": fuzz["seed_count"] if fuzz else None,
    }
    complete = bool(
        coverage
        and typed
        and translation
        and fuzz
        and coverage["summary"]["safe_ingest_rows"] == 141
        and coverage["summary"]["generic_endpoint_rows"] == 141
        and coverage["summary"]["field_visitor_rows"] == 141
        and typed["summary"]["typed_structural"] == 141
        and translation["summary"]["translation_rows"] == 141
        and fuzz["catalog_entry_count"] == 141
        and fuzz["seed_count"] >= 146
    )
    note = (
        "Wire safety, structural field access, translation coverage, and shallow fuzz seeds cover every standard row."
        if complete
        else "One or more wire/field surfaces are still below full-row coverage or missing reproducible fuzz receipts."
    )
    return {
        "name": "Generic wire and field coverage",
        "status": _status(complete=complete, partial=bool(coverage or typed or translation or fuzz)),
        "note": note,
        "metrics": metrics,
        "evidence": evidence,
    }


def audit_typed_semantic_waves() -> dict[str, object]:
    semantic_path = ROOT / "generated" / "semantic_pdu_parser_manifest.json"
    waves_path = ROOT / "generated" / "epic2_semantic_waves.json"
    semantic = load_json(semantic_path)
    waves = load_json(waves_path)
    evidence = evidence_rows([semantic_path, waves_path])

    wave_rows = {row["wave_id"]: row for row in (waves["waves"] if waves else [])}
    metrics = {
        "semantic_parsers": semantic["summary"]["semantic_parsers"] if semantic else None,
        "semantic_observation_rows": semantic["summary"]["semantic_observation"] if semantic else None,
        "fully_domain_decoded_rows": semantic["summary"]["fully_domain_decoded"] if semantic else None,
        "wave_count": waves["summary"]["waves"] if waves else None,
        "wave1_rows": wave_rows.get("wave1", {}).get("rows"),
        "wave2_rows": wave_rows.get("wave2", {}).get("rows"),
        "wave3_rows": wave_rows.get("wave3", {}).get("rows"),
        "wave4_rows": wave_rows.get("wave4", {}).get("rows"),
        "wave5_rows": wave_rows.get("wave5", {}).get("rows"),
    }
    complete = bool(
        semantic
        and waves
        and semantic["summary"]["semantic_parsers"] == 141
        and semantic["summary"]["semantic_observation"] == 0
        and semantic["summary"]["fully_domain_decoded"] == 141
        and waves["summary"]["records"] == 141
        and waves["summary"]["waves"] == 5
        and wave_rows.get("wave1", {}).get("rows") == 19
        and wave_rows.get("wave2", {}).get("rows") == 14
        and wave_rows.get("wave3", {}).get("rows") == 20
        and wave_rows.get("wave4", {}).get("rows") == 46
        and wave_rows.get("wave5", {}).get("rows") == 42
    )
    note = (
        "All five typed-semantic waves are classified and every standard row now lands on a fully domain-decoded or prefix-aware semantic surface."
        if complete
        else "Wave planning exists, but one or more wave counts or semantic coverage totals still fall short."
    )
    return {
        "name": "Typed semantic waves",
        "status": _status(complete=complete, partial=bool(semantic or waves)),
        "note": note,
        "metrics": metrics,
        "evidence": evidence,
    }


def audit_cross_engine_parity() -> dict[str, object]:
    cross_lang_path = ROOT / "docs" / "message_cross_language_set.json"
    logging_path = ROOT / "generated" / "pdu_log_catalog.json"
    lattice_path = ROOT / "generated" / "lattice_dis_mapping_plan.json"
    unity_bridge_probe_path = ROOT / "build" / "reports" / "unity_csharp_bridge_probe.json"
    cross_lang = load_json(cross_lang_path)
    logging = load_json(logging_path)
    lattice = load_json(lattice_path)
    unity_bridge_probe = load_json(unity_bridge_probe_path)
    evidence = evidence_rows([cross_lang_path, logging_path, lattice_path, unity_bridge_probe_path])

    records = cross_lang["records"] if cross_lang else []
    language_metrics = {}
    if records:
        for surface in ("c", "cpp", "python", "unreal", "godot", "unity"):
            catalog_key = f"{surface}_catalog"
            deep_key = f"{surface}_body_decoder" if surface in {"c", "cpp", "python"} else f"{surface}_adapter"
            language_metrics[surface] = {
                "catalog_rows": sum(1 for row in records if row.get(catalog_key)),
                "deep_rows": sum(1 for row in records if row.get(deep_key)),
            }
    lattice_summary = lattice["summary"] if lattice else {}
    metrics = {
        "language_rows": language_metrics,
        "logging_descriptors": logging["summary"]["records"] if logging else None,
        "lattice_records": lattice_summary.get("records"),
        "lattice_strict_buckets": lattice_summary.get("strict_buckets"),
        "lattice_surface_confidence": lattice_summary.get("surface_confidence"),
        "unity_csharp_bridge_probe_status": None if unity_bridge_probe is None else unity_bridge_probe.get("overall_status"),
    }
    complete = bool(
        records
        and all(language_metrics[surface]["catalog_rows"] == 141 for surface in ("c", "cpp", "python", "unreal", "godot", "unity"))
        and all(language_metrics[surface]["deep_rows"] == 141 for surface in ("c", "cpp", "python", "unreal", "godot", "unity"))
        and logging
        and logging["summary"]["records"] == 141
        and lattice
        and lattice_summary.get("records") == 141
    )
    partial = bool(records or logging or lattice)
    if complete:
        note = "Cross-language and engine surfaces expose equivalent deep semantics for every standard row."
    else:
        note = (
            "Generated catalogs and Lattice/Zorn row classifications are present, but runtime/deep parity is still incomplete. "
            "Current cross-language evidence shows Unity catalog visibility at 141 rows with the same 4 proven deep rows as the other language/engine surfaces, while full 141-row runtime parity is still outstanding."
        )
    return {
        "name": "Cross-engine and Lattice/Zorn parity",
        "status": _status(complete=complete, partial=partial),
        "note": note,
        "metrics": metrics,
        "evidence": evidence,
    }


def audit_evidence_release_gates() -> dict[str, object]:
    evidence_manifest_path = ROOT / "build" / "verification_reports" / "evidence" / "latest" / "manifest.json"
    release_ready_receipt_path = ROOT / "build" / "reports" / "release_ready_receipt.json"
    dev_check_path = ROOT / "tools" / "dev_check.py"
    docs_check_path = ROOT / "tools" / "check_docs.py"
    inspect_release_path = ROOT / "tools" / "inspect_alpha5_release_artifacts.py"
    evidence_pack_path = ROOT / "tools" / "generate_evidence_pack.py"
    evidence = evidence_rows([evidence_manifest_path, release_ready_receipt_path, dev_check_path, docs_check_path, inspect_release_path, evidence_pack_path])

    evidence_ok = False
    evidence_errors: list[str] = []
    if evidence_manifest_path.is_file():
        evidence_ok, evidence_errors = check_evidence_pack.check(evidence_manifest_path)
    release_ready_receipt = load_json(release_ready_receipt_path)

    dev_check_text = dev_check_path.read_text(encoding="utf-8") if dev_check_path.is_file() else ""
    metrics = {
        "evidence_pack_manifest_status": "pass" if evidence_ok else ("missing" if not evidence_manifest_path.exists() else "fail"),
        "evidence_pack_error_count": len(evidence_errors),
        "release_ready_receipt_status": None if release_ready_receipt is None else release_ready_receipt.get("overall_status"),
        "release_ready_receipt_mode": None if release_ready_receipt is None else release_ready_receipt.get("requested_mode"),
        "release_ready_receipt_missing_labels": [] if release_ready_receipt is None else release_ready_receipt.get("missing_labels", []),
        "release_ready_receipt_required_failures": [] if release_ready_receipt is None else release_ready_receipt.get("required_failures", []),
        "dev_check_wires_docs_audit": "tools/check_docs.py" in dev_check_text,
        "dev_check_wires_evidence_pack": "generate_evidence_pack.py" in dev_check_text,
        "dev_check_wires_evidence_check": "check_evidence_pack.py" in dev_check_text,
        "dev_check_wires_release_inspection": "inspect_alpha5_release_artifacts.py" in dev_check_text,
    }
    complete = bool(
        evidence_ok
        and release_ready_receipt is not None
        and release_ready_receipt.get("schema") == "fastdis.release_ready_receipt.v1"
        and release_ready_receipt.get("requested_mode") == "release_ready"
        and release_ready_receipt.get("overall_status") == "pass"
        and not release_ready_receipt.get("missing_labels")
        and not release_ready_receipt.get("required_failures")
        and metrics["dev_check_wires_docs_audit"]
        and metrics["dev_check_wires_evidence_pack"]
        and metrics["dev_check_wires_evidence_check"]
        and metrics["dev_check_wires_release_inspection"]
    )
    note = (
        "A current release-ready receipt proves the host ran the credential-free release gate stack, including docs audit, evidence pack generation/check, and release artifact inspection."
        if complete
        else "Evidence-pack and release-inspection surfaces exist, but current proof is still partial or missing."
    )
    status = _status(complete=complete, partial=any(item["exists"] for item in evidence))
    return {
        "name": "Evidence and release gates",
        "status": status,
        "note": note,
        "metrics": metrics,
        "evidence": evidence,
        "errors": evidence_errors,
    }


def build_report() -> dict[str, object]:
    criteria = [
        audit_generated_truth(),
        audit_wire_and_field_coverage(),
        audit_typed_semantic_waves(),
        audit_cross_engine_parity(),
        audit_evidence_release_gates(),
    ]
    if all(item["status"] == "complete" for item in criteria):
        overall_status = "complete"
    elif any(item["status"] == "missing_evidence" for item in criteria):
        overall_status = "missing_evidence"
    else:
        overall_status = "in_progress"
    return {
        "schema": "fastdis.epic2_audit.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status,
        "criteria": criteria,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Epic 2 Audit Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        "",
        "## Criteria",
        "",
        "| Criterion | Status | Note |",
        "| --- | --- | --- |",
    ]
    for item in report["criteria"]:
        lines.append(f"| {item['name']} | `{item['status']}` | {item['note']} |")
    lines.extend(["", "## Evidence", ""])
    for item in report["criteria"]:
        lines.append(f"### {item['name']}")
        lines.append("")
        lines.append(f"- status: `{item['status']}`")
        for key, value in item.get("metrics", {}).items():
            lines.append(f"- {key}: `{json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value}`")
        if item.get("errors"):
            lines.append(f"- errors: `{json.dumps(item['errors'])}`")
        lines.append("- evidence:")
        for evidence in item["evidence"]:
            lines.append(
                f"  - `{evidence['path']}` exists=`{evidence['exists']}` kind=`{evidence['kind']}`"
            )
        lines.append("")
    return "\n".join(lines)


def write_report(out_dir: Path) -> tuple[Path, Path]:
    report = build_report()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "epic2_audit_report.json"
    md_path = out_dir / "epic2_audit_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--strict", action="store_true", help="Fail unless every Epic 2 criterion is complete.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path, md_path = write_report(args.out_dir)
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    report = json.loads(json_path.read_text(encoding="utf-8"))
    if args.strict and report["overall_status"] != "complete":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
