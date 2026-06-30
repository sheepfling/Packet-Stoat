#!/usr/bin/env python3
"""Validate a returned competitor capture bundle against the current manifest."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "build" / "reports" / "competitor_capture_manifest.json"
DEFAULT_JSON_OUT = ROOT / "build" / "reports" / "competitor_capture_validation.json"
DEFAULT_MD_OUT = ROOT / "build" / "reports" / "competitor_capture_validation.md"


def _load_tool_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UNREAL_BASELINE = _load_tool_module("normalize_unreal_grill_baseline", "tools/normalize_unreal_grill_baseline.py")
UNITY_BASELINE = _load_tool_module("normalize_unity_grill_baseline", "tools/normalize_unity_grill_baseline.py")
HEAD_TO_HEAD = _load_tool_module("run_engine_head_to_head_matrix", "tools/run_engine_head_to_head_matrix.py")
WORKBENCH = _load_tool_module("check_competitor_handoff_workbench", "tools/check_competitor_handoff_workbench.py")

LANE_CONFIG = {
    "unreal_vs_grill": {
        "raw_baseline": "verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json",
        "normalized_report": "artifacts/reports/engine_benchmarks/grill_unreal_engine_benchmark_report.json",
        "head_to_head": "artifacts/reports/engine_head_to_head/unreal_vs_grill.json",
        "status_report": "artifacts/reports/engine_head_to_head/unreal_vs_grill_status.json",
        "blocked_smoke": "verification_reports/unreal_grill_baseline/grill_unreal_source_smoke.json",
        "surface": "grill_unreal",
        "version_path": ("engine", "version"),
        "manifest_version_key": "engine_version",
        "baseline_validator": UNREAL_BASELINE.validate_payload,
    },
    "unity_vs_grill": {
        "raw_baseline": "verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json",
        "normalized_report": "artifacts/reports/engine_benchmarks/grill_unity_engine_benchmark_report.json",
        "head_to_head": "artifacts/reports/engine_head_to_head/unity_vs_grill.json",
        "status_report": "artifacts/reports/engine_head_to_head/unity_vs_grill_status.json",
        "blocked_smoke": "verification_reports/unity_grill_baseline/grill_unity_import_smoke.json",
        "surface": "grill_unity",
        "version_path": ("unity", "version"),
        "manifest_version_key": "unity_version",
        "baseline_validator": UNITY_BASELINE.validate_payload,
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Returned competitor bundle root or .zip archive")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument(
        "--if-available",
        action="store_true",
        help="Succeed with a skipped report when no returned competitor artifacts are present",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def extracted_bundle_root(tmp_root: Path) -> Path:
    children = [child for child in tmp_root.iterdir() if child.is_dir()]
    if len(children) != 1:
        raise ValueError("Imported archive must contain exactly one top-level bundle directory")
    return children[0]


def resolve_bundle_root(bundle_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if bundle_path.is_dir():
        return bundle_path, None
    if bundle_path.is_file() and bundle_path.suffix == ".zip":
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_root = Path(tmp_dir.name)
        with zipfile.ZipFile(bundle_path) as archive:
            archive.extractall(tmp_root)
        return extracted_bundle_root(tmp_root), tmp_dir
    raise FileNotFoundError(f"Bundle path is neither a directory nor a zip archive: {bundle_path}")


def _extract_values(payload: Any, parts: list[str]) -> list[Any]:
    if not parts:
        return [payload]
    head = parts[0]
    tail = parts[1:]
    if head.endswith("[]"):
        key = head[:-2]
        if not isinstance(payload, dict):
            return []
        items = payload.get(key)
        if not isinstance(items, list):
            return []
        values: list[Any] = []
        for item in items:
            values.extend(_extract_values(item, tail))
        return values
    if not isinstance(payload, dict) or head not in payload:
        return []
    return _extract_values(payload[head], tail)


def _value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value) and not value.startswith("REPLACE_ME")
    return True


def _validate_required_fields(payload: dict[str, Any], field_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for field_path in field_paths:
        values = _extract_values(payload, field_path.split("."))
        if not values:
            errors.append(f"missing required capture field `{field_path}`")
            continue
        if not all(_value_present(value) for value in values):
            errors.append(f"required capture field `{field_path}` contains empty or template values")
    return errors


def _read_nested_string(payload: dict[str, Any], *path: str) -> str | None:
    current: Any = payload
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current if isinstance(current, str) else None


def _collect_report_scenarios(payload: dict[str, Any]) -> list[str]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return []
    scenarios: list[str] = []
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("scenario"), str):
            scenarios.append(str(row["scenario"]))
    return scenarios


def _validate_head_to_head(payload: dict[str, Any], lane_name: str) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "fastdis.engine_head_to_head_report.v1":
        errors.append(f"{lane_name}: head-to-head schema must equal fastdis.engine_head_to_head_report.v1")
    comparison = payload.get("comparison")
    if not isinstance(comparison, dict):
        errors.append(f"{lane_name}: head-to-head report is missing `comparison`")
        return errors
    if payload.get("validation_errors"):
        errors.append(f"{lane_name}: head-to-head report contains validation errors")
    if comparison.get("same_host") is not True:
        errors.append(f"{lane_name}: head-to-head report is not marked same-host")
    matched = comparison.get("matched_scenarios")
    if not isinstance(matched, int) or matched <= 0:
        errors.append(f"{lane_name}: head-to-head report must include at least one matched scenario")
    return errors


def _artifact_mode(bundle_root: Path, config: dict[str, Any], present_artifacts: list[str]) -> str:
    raw_path = bundle_root / str(config["raw_baseline"])
    report_path = bundle_root / str(config["normalized_report"])
    blocked_smoke_path = bundle_root / str(config["blocked_smoke"])
    status_report_path = bundle_root / str(config["status_report"])
    head_path = bundle_root / str(config["head_to_head"])
    if raw_path.is_file() or report_path.is_file():
        return "benchmark_capture"
    if blocked_smoke_path.is_file() or status_report_path.is_file():
        return "blocked_evidence_only"
    if head_path.is_file() or present_artifacts:
        return "artifact_only"
    return "empty"


def validate_bundle_from_manifest(bundle_root: Path, manifest_payload: dict[str, Any], *, if_available: bool = False) -> dict[str, Any]:
    workbench = WORKBENCH.build_report(bundle_root)
    lane_results: list[dict[str, Any]] = []
    global_errors: list[str] = []
    lane_entries = manifest_payload.get("lanes")
    if not isinstance(lane_entries, list):
        raise ValueError("Manifest is missing `lanes`")

    for lane_entry in lane_entries:
        if not isinstance(lane_entry, dict):
            continue
        lane_name = lane_entry.get("lane")
        if lane_name not in LANE_CONFIG:
            continue
        config = LANE_CONFIG[str(lane_name)]
        required_artifacts = lane_entry.get("required_return_artifacts")
        if not isinstance(required_artifacts, list):
            raise ValueError(f"Manifest lane {lane_name} is missing `required_return_artifacts`")
        raw_path = bundle_root / config["raw_baseline"]
        report_path = bundle_root / config["normalized_report"]
        head_path = bundle_root / config["head_to_head"]
        present_artifacts = [artifact for artifact in required_artifacts if (bundle_root / artifact).is_file()]
        artifact_mode = _artifact_mode(bundle_root, config, present_artifacts)
        lane_present = artifact_mode == "benchmark_capture"
        lane_errors: list[str] = []
        shared_scenarios: list[str] = []
        host_alignment: dict[str, Any] = {}
        if lane_present:
            missing = [artifact for artifact in required_artifacts if not (bundle_root / artifact).is_file()]
            lane_errors.extend(f"missing required artifact `{artifact}`" for artifact in missing)

            raw_payload = load_json(raw_path) if raw_path.is_file() else None
            report_payload = load_json(report_path) if report_path.is_file() else None
            head_payload = load_json(head_path) if head_path.is_file() else None

            if isinstance(raw_payload, dict):
                lane_errors.extend(config["baseline_validator"](raw_payload))
                required_fields = lane_entry.get("required_capture_fields")
                if isinstance(required_fields, list):
                    lane_errors.extend(_validate_required_fields(raw_payload, [str(item) for item in required_fields]))
                fastdis_host = lane_entry.get("fastdis_host") if isinstance(lane_entry.get("fastdis_host"), dict) else {}
                for host_key in ("system", "release", "machine"):
                    expected = fastdis_host.get(host_key)
                    observed = _read_nested_string(raw_payload, "host", host_key)
                    host_alignment[host_key] = {"expected": expected, "observed": observed, "matches": expected == observed if expected and observed else None}
                    if isinstance(expected, str) and expected and isinstance(observed, str) and observed and expected != observed:
                        lane_errors.append(f"{lane_name}: host.{host_key} mismatch: expected `{expected}`, got `{observed}`")
                expected_version = fastdis_host.get(config["manifest_version_key"]) if isinstance(fastdis_host, dict) else None
                observed_version = _read_nested_string(raw_payload, *config["version_path"])
                host_alignment["version"] = {
                    "expected": expected_version,
                    "observed": observed_version,
                    "matches": expected_version == observed_version if expected_version and observed_version else None,
                }
                if isinstance(expected_version, str) and expected_version and isinstance(observed_version, str) and observed_version and expected_version != observed_version:
                    lane_errors.append(f"{lane_name}: engine version mismatch: expected `{expected_version}`, got `{observed_version}`")

            if isinstance(report_payload, dict):
                lane_errors.extend(HEAD_TO_HEAD.validate_report(report_payload, str(lane_name)))
                if report_payload.get("surface") != config["surface"]:
                    lane_errors.append(f"{lane_name}: normalized report surface must equal `{config['surface']}`")
                report_scenarios = set(_collect_report_scenarios(report_payload))
                fastdis_scenarios = {str(item) for item in lane_entry.get("fastdis_scenarios", []) if isinstance(item, str)}
                shared_scenarios = sorted(report_scenarios & fastdis_scenarios)
                if not shared_scenarios:
                    lane_errors.append(f"{lane_name}: normalized report has no shared scenarios with current FastDIS lane")

            if isinstance(head_payload, dict):
                lane_errors.extend(_validate_head_to_head(head_payload, str(lane_name)))

        lane_results.append(
            {
                "lane": lane_name,
                "present": lane_present,
                "artifact_mode": artifact_mode,
                "present_artifacts": present_artifacts,
                "shared_scenarios": shared_scenarios,
                "host_alignment": host_alignment,
                "errors": lane_errors,
            }
        )

    active_lanes = [lane for lane in lane_results if lane["present"]]
    if workbench.get("status") != "pass" and active_lanes:
        global_errors.append("bundle failed embedded handoff workbench validation")
    if not active_lanes:
        if if_available:
            status = "skipped"
        else:
            global_errors.append("bundle does not contain any returned competitor lane artifacts")
            status = "fail"
    else:
        status = "pass" if not global_errors and all(not lane["errors"] for lane in active_lanes) else "fail"
    return {
        "schema": "fastdis.competitor_capture_validation.v1",
        "bundle_root": display_path(bundle_root),
        "manifest_schema": manifest_payload.get("schema"),
        "status": status,
        "active_lane_count": len(active_lanes),
        "errors": global_errors,
        "handoff_workbench": {
            "schema": workbench.get("schema"),
            "status": workbench.get("status"),
            "summary": workbench.get("summary"),
        },
        "lanes": lane_results,
    }


def render_markdown(validation: dict[str, Any]) -> str:
    lines = [
        "# Competitor Capture Validation",
        "",
        f"- status: `{validation['status']}`",
        f"- bundle_root: `{validation['bundle_root']}`",
        f"- active_lane_count: `{validation['active_lane_count']}`",
        "",
        "## Handoff Workbench",
        "",
        f"- status: `{validation['handoff_workbench']['status']}`",
        f"- bundle_kind: `{validation['handoff_workbench']['summary']['bundle_kind']}`",
        f"- self_describing_bundle: `{validation['handoff_workbench']['summary']['self_describing_bundle']}`",
        f"- manifest_present: `{validation['handoff_workbench']['summary']['manifest_present']}`",
        f"- manifest_valid: `{validation['handoff_workbench']['summary']['manifest_valid']}`",
        f"- checksum_mismatch_count: `{validation['handoff_workbench']['summary']['checksum_mismatch_count']}`",
        f"- missing_file_count: `{validation['handoff_workbench']['summary']['missing_file_count']}`",
        "",
        "## Global Errors",
        "",
    ]
    if validation["errors"]:
        for error in validation["errors"]:
            lines.append(f"- {error}")
    else:
        lines.append("- none")
    lines.extend(["", "## Lanes", ""])
    for lane in validation["lanes"]:
        lines.extend(
            [
                f"### {lane['lane']}",
                "",
                f"- present: `{lane['present']}`",
                f"- artifact_mode: `{lane.get('artifact_mode', 'unknown')}`",
                f"- shared_scenarios: `{', '.join(lane['shared_scenarios']) if lane['shared_scenarios'] else 'none'}`",
            ]
        )
        if lane["errors"]:
            lines.append("- errors:")
            for error in lane["errors"]:
                lines.append(f"  - {error}")
        else:
            lines.append("- errors: none")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_payload = load_json(args.manifest)
    bundle_root, tmp_dir = resolve_bundle_root(Path(args.bundle).expanduser().resolve())
    try:
        validation = validate_bundle_from_manifest(bundle_root, manifest_payload, if_available=bool(args.if_available))
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(validation) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0 if validation["status"] in {"pass", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
