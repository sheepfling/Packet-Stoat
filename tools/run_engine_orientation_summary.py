#!/usr/bin/env python3
"""Summarize Unreal, Godot, and Unity orientation visual verification status."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

from artifacts import REPORTS_DIR

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import compare_orientation_screenshots
import fastdis_orient


FIXTURES = ROOT / "tests" / "data" / "orientation_engine_cases.json"
VISUAL_CASES = ROOT / "tests" / "data" / "orientation_visual_cases.json"
DEFAULT_OUT_DIR = REPORTS_DIR / "engine_orientation_summary"

ENGINE_CONFIGS = {
    "unreal": {
        "positive_label": "standalone_neu",
        "known_bad_label": "known_bad",
        "config": ROOT / "configs" / "orientation" / "unreal_standalone_neu_cm.yaml",
        "known_bad": ROOT / "tests" / "orientation_known_bad" / "unreal_north_east_swap.yaml",
    },
    "godot": {
        "positive_label": "standalone_enu",
        "known_bad_label": "known_bad",
        "config": ROOT / "configs" / "orientation" / "godot_standalone_enu_m.yaml",
        "known_bad": ROOT / "tests" / "orientation_known_bad" / "godot_forward_inverted.yaml",
    },
    "unity": {
        "positive_label": "standalone_eun",
        "known_bad_label": "known_bad",
        "config": ROOT / "configs" / "orientation" / "unity_standalone_eun_m.yaml",
        "known_bad": ROOT / "tests" / "orientation_known_bad" / "unity_forward_inverted.yaml",
    },
}


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_config(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = fastdis_orient.load_structured(path)
    return payload, fastdis_orient.normalize_config_payload(payload)


def write_compare(fixtures: Path, config_path: Path, target: str, out_path: Path) -> dict[str, Any]:
    _raw, config = normalize_config(config_path)
    payload = fastdis_orient.compare_payload(fixtures, config, target)
    dump_json(out_path, payload)
    return payload


def write_projection(compare_path: Path, label: str, out_dir: Path) -> dict[str, Any]:
    args = argparse.Namespace(
        compare=str(compare_path),
        visual_cases=str(VISUAL_CASES),
        label=label,
        out_dir=str(out_dir),
    )
    compare_orientation_screenshots.run_from_namespace(args)
    payload = load_json(out_dir / f"{load_json(compare_path)['target']}_{label}_projection_report.json")
    return payload


def refresh_reports(out_dir: Path) -> dict[str, dict[str, Path]]:
    paths: dict[str, dict[str, Path]] = {}
    for engine, spec in ENGINE_CONFIGS.items():
        engine_dir = out_dir / engine
        visual_dir = engine_dir / "visual"
        positive_compare = engine_dir / "orientation_compare.json"
        known_bad_compare = engine_dir / "known_bad_compare.json"
        write_compare(FIXTURES, spec["config"], engine, positive_compare)
        write_projection(positive_compare, spec["positive_label"], visual_dir)
        write_compare(FIXTURES, spec["known_bad"], engine, known_bad_compare)
        write_projection(known_bad_compare, spec["known_bad_label"], visual_dir / "known_bad")
        paths[engine] = {
            "positive_compare": positive_compare,
            "positive_projection": visual_dir / f"{engine}_{spec['positive_label']}_projection_report.json",
            "known_bad_compare": known_bad_compare,
            "known_bad_projection": visual_dir / "known_bad" / f"{engine}_{spec['known_bad_label']}_projection_report.json",
        }
    return paths


def default_existing_paths(root: Path) -> dict[str, dict[str, Path]]:
    paths: dict[str, dict[str, Path]] = {}
    evidence_root = REPORTS_DIR / "engine_orientation_evidence"
    for engine, spec in ENGINE_CONFIGS.items():
        paths[engine] = {
            "positive_compare": evidence_root / engine / "orientation_compare.json",
            "positive_projection": evidence_root / engine / "visual" / f"{engine}_{spec['positive_label']}_projection_report.json",
            "known_bad_compare": root / engine / "known_bad_compare.json",
            "known_bad_projection": root / engine / "visual" / "known_bad" / f"{engine}_{spec['known_bad_label']}_projection_report.json",
        }
    return paths


def collect_compare_failures(payload: dict[str, Any], *, expected_pass: bool) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        passed = bool(item.get("pass"))
        if expected_pass and not passed:
            failures.append(
                {
                    "case": item.get("case"),
                    "failure_signature": item.get("failure_signature"),
                    "max_axis_error_deg": item.get("max_axis_error_deg"),
                    "engine_stage_max_axis_error_deg": item.get("engine_stage_max_axis_error_deg"),
                    "asset_stage_max_axis_error_deg": item.get("asset_stage_max_axis_error_deg"),
                }
            )
    return failures


def collect_projection_failures(payload: dict[str, Any], *, expected_pass: bool) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        passed = bool(item.get("pass"))
        if expected_pass and not passed:
            failures.append(
                {
                    "case": item.get("case"),
                    "camera": item.get("camera"),
                    "failure_signature": item.get("failure_signature"),
                    "visual_projection_error_px": item.get("visual_projection_error_px"),
                    "visual_projection_angle_error_deg": item.get("visual_projection_angle_error_deg"),
                    "actual_image": item.get("actual_image"),
                    "sidecar": item.get("sidecar"),
                }
            )
    return failures


def summarize_engine(engine: str, paths: dict[str, Path]) -> dict[str, Any]:
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {
            "engine": engine,
            "status": "missing_reports",
            "missing": missing,
            "paths": {name: display_path(path) for name, path in paths.items()},
        }

    positive_compare = load_json(paths["positive_compare"])
    positive_projection = load_json(paths["positive_projection"])
    known_bad_compare = load_json(paths["known_bad_compare"])
    known_bad_projection = load_json(paths["known_bad_projection"])

    positive_numeric_total = positive_compare["summary"]["case_count"]
    positive_numeric_pass = positive_compare["summary"]["pass_count"]
    positive_visual_total = positive_projection["summary"]["image_count"]
    positive_visual_pass = positive_projection["summary"]["pass_count"]

    known_bad_expected_signature = fastdis_orient.load_structured(ENGINE_CONFIGS[engine]["known_bad"]).get("expected_signature")
    known_bad_failed_cases = [item for item in known_bad_compare.get("results", []) if not item.get("pass")]
    known_bad_signatures = sorted({item.get("failure_signature") for item in known_bad_failed_cases if item.get("failure_signature")})
    known_bad_detected = bool(known_bad_failed_cases) and known_bad_expected_signature in known_bad_signatures
    known_bad_visual_failed = known_bad_projection["summary"]["pass_count"] < known_bad_projection["summary"]["image_count"]

    positive_failures = collect_compare_failures(positive_compare, expected_pass=True)
    positive_visual_failures = collect_projection_failures(positive_projection, expected_pass=True)
    undetected_known_bad: list[dict[str, Any]] = []
    if not known_bad_detected:
        undetected_known_bad.append(
            {
                "kind": "numeric_known_bad",
                "expected_signature": known_bad_expected_signature,
                "observed_signatures": known_bad_signatures,
            }
        )
    if not known_bad_visual_failed:
        undetected_known_bad.append(
            {
                "kind": "visual_known_bad",
                "expected": "at least one known-bad projection image must fail",
                "pass_count": known_bad_projection["summary"]["pass_count"],
                "image_count": known_bad_projection["summary"]["image_count"],
            }
        )

    return {
        "engine": engine,
        "status": "pass" if not positive_failures and not positive_visual_failures and not undetected_known_bad else "fail",
        "positive": {
            "numeric": {
                "pass_count": positive_numeric_pass,
                "total": positive_numeric_total,
                "pass_percent": 100.0 * positive_numeric_pass / positive_numeric_total if positive_numeric_total else 0.0,
                "max_axis_error_deg": positive_compare["summary"].get("max_axis_error_deg"),
                "failures": positive_failures,
                "report": display_path(paths["positive_compare"]),
            },
            "visual": {
                "pass_count": positive_visual_pass,
                "total": positive_visual_total,
                "pass_percent": 100.0 * positive_visual_pass / positive_visual_total if positive_visual_total else 0.0,
                "max_projection_error_px": positive_projection["summary"].get("max_projection_error_px"),
                "max_screen_angle_error_deg": positive_projection["summary"].get("max_screen_angle_error_deg"),
                "failures": positive_visual_failures,
                "report": display_path(paths["positive_projection"]),
            },
        },
        "known_bad_controls": {
            "expected_signature": known_bad_expected_signature,
            "observed_signatures": known_bad_signatures,
            "numeric_detected": known_bad_detected,
            "numeric_failed_cases": len(known_bad_failed_cases),
            "visual_detected": known_bad_visual_failed,
            "visual_failed_images": known_bad_projection["summary"]["image_count"] - known_bad_projection["summary"]["pass_count"],
            "total_visual_images": known_bad_projection["summary"]["image_count"],
            "undetected": undetected_known_bad,
            "numeric_report": display_path(paths["known_bad_compare"]),
            "visual_report": display_path(paths["known_bad_projection"]),
        },
    }


def aggregate(engines: list[dict[str, Any]]) -> dict[str, Any]:
    positive_pass = 0
    positive_total = 0
    known_bad_pass = 0
    known_bad_total = 0
    failing: list[dict[str, Any]] = []
    for engine in engines:
        if engine["status"] == "missing_reports":
            failing.append({"engine": engine["engine"], "kind": "missing_reports", "missing": engine["missing"]})
            continue
        positive_pass += engine["positive"]["numeric"]["pass_count"] + engine["positive"]["visual"]["pass_count"]
        positive_total += engine["positive"]["numeric"]["total"] + engine["positive"]["visual"]["total"]
        known_bad_total += 2
        if engine["known_bad_controls"]["numeric_detected"]:
            known_bad_pass += 1
        if engine["known_bad_controls"]["visual_detected"]:
            known_bad_pass += 1
        for item in engine["positive"]["numeric"]["failures"]:
            failing.append({"engine": engine["engine"], "kind": "positive_numeric", **item})
        for item in engine["positive"]["visual"]["failures"]:
            failing.append({"engine": engine["engine"], "kind": "positive_visual", **item})
        for item in engine["known_bad_controls"]["undetected"]:
            failing.append({"engine": engine["engine"], **item})
    return {
        "positive_pass_count": positive_pass,
        "positive_total": positive_total,
        "positive_pass_percent": 100.0 * positive_pass / positive_total if positive_total else 0.0,
        "known_bad_detection_count": known_bad_pass,
        "known_bad_total": known_bad_total,
        "known_bad_detection_percent": 100.0 * known_bad_pass / known_bad_total if known_bad_total else 0.0,
        "failing_count": len(failing),
        "failing": failing,
        "overall_status": "pass" if positive_total and positive_pass == positive_total and known_bad_pass == known_bad_total and not failing else "fail",
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Engine Orientation Summary",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{summary['overall_status']}`",
        f"- positive_pass_percent: `{summary['positive_pass_percent']:.2f}%` ({summary['positive_pass_count']}/{summary['positive_total']})",
        f"- known_bad_detection_percent: `{summary['known_bad_detection_percent']:.2f}%` ({summary['known_bad_detection_count']}/{summary['known_bad_total']})",
        "",
        "| Engine | Numeric Positive | Visual Positive | Known-Bad Numeric | Known-Bad Visual | Status |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for engine in report["engines"]:
        if engine["status"] == "missing_reports":
            lines.append(f"| {engine['engine']} | n/a | n/a | n/a | n/a | missing_reports |")
            continue
        numeric = engine["positive"]["numeric"]
        visual = engine["positive"]["visual"]
        kb = engine["known_bad_controls"]
        lines.append(
            f"| {engine['engine']} | {numeric['pass_count']}/{numeric['total']} ({numeric['pass_percent']:.2f}%) | "
            f"{visual['pass_count']}/{visual['total']} ({visual['pass_percent']:.2f}%) | "
            f"{'detected' if kb['numeric_detected'] else 'NOT DETECTED'} | "
            f"{'detected' if kb['visual_detected'] else 'NOT DETECTED'} | {engine['status']} |"
        )
    lines.extend(["", "## Failing Or Undetected Tests", ""])
    if not summary["failing"]:
        lines.append("_None. Positive lanes are 100%, and known-bad controls are detected._")
    else:
        for item in summary["failing"]:
            lines.append(f"- `{item['engine']}` `{item.get('kind', 'unknown')}`: `{json.dumps(item, sort_keys=True)}`")
    lines.extend(["", "## Triage Notes", ""])
    lines.append("- Positive Unreal/Godot/Unity orientation artifacts must pass at 100%.")
    lines.append("- Known-bad fixtures are negative controls. They must fail/detect the expected signature and are not counted against positive pass percentage.")
    lines.append("- If a known-bad fixture starts passing, the verifier is too weak or a fixture expectation is stale.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--refresh", action="store_true", help="Regenerate positive and known-bad projection reports before summarizing")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = refresh_reports(out_dir) if args.refresh else default_existing_paths(out_dir)
    engines = [summarize_engine(engine, engine_paths) for engine, engine_paths in paths.items()]
    report = {
        "schema": "fastdis.engine_orientation_summary.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "out_dir": display_path(out_dir),
        "refreshed": bool(args.refresh),
        "engines": engines,
        "summary": aggregate(engines),
    }
    json_path = out_dir / "engine_orientation_summary.json"
    md_path = out_dir / "engine_orientation_summary.md"
    dump_json(json_path, report)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
        print(f"JSON: {display_path(json_path)}")
        print(f"Markdown: {display_path(md_path)}")
    return 0 if report["summary"]["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
