#!/usr/bin/env python3
"""Generate an Alpha 3 orientation pipeline inspection report."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import fastdis_orient


DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha3_current"
FIXTURES = ROOT / "tests" / "data" / "orientation_engine_cases.json"
UNREAL_CONFIG = ROOT / "configs" / "orientation" / "unreal_standalone_neu_cm.yaml"
GODOT_CONFIG = ROOT / "configs" / "orientation" / "godot_standalone_enu_m.yaml"
KNOWN_BAD = ROOT / "tests" / "orientation_known_bad" / "godot_forward_inverted.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Orientation Pipeline Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- fixtures: `{report['fixtures']}`",
        "",
        "## Good Configs",
        "",
        f"- Unreal pass cases: `{report['good_configs']['unreal']['pass_count']}` / `{report['good_configs']['unreal']['case_count']}`",
        f"- Godot pass cases: `{report['good_configs']['godot']['pass_count']}` / `{report['good_configs']['godot']['case_count']}`",
        "",
        "## Known Bad",
        "",
        f"- signature: `{report['known_bad']['most_likely_issue']}`",
        f"- suggestion: {report['known_bad']['suggestion']}",
        "",
        "## Solver",
        "",
    ]
    for index, candidate in enumerate(report["solver"]["top_candidates"], start=1):
        lines.append(
            f"{index}. forward={candidate['variant']['asset.forward_axis']} "
            f"up={candidate['variant']['asset.up_axis']} max_err={candidate['max_axis_error_deg']:.4f} "
            f"pass_count={candidate['pass_count']}"
        )
    lines.extend(
        [
            "",
            "## Config Snapshots",
            "",
            f"- unreal_good: `{report['good_configs']['unreal']['config_path']}` `{report['good_configs']['unreal']['config_hash']}`",
            f"- godot_good: `{report['good_configs']['godot']['config_path']}` `{report['good_configs']['godot']['config_hash']}`",
            f"- godot_known_bad: `{report['known_bad']['config_path']}` `{report['known_bad']['config_hash']}`",
            "",
            "## Trace Artifacts",
            "",
            f"- good_trace: `{report['trace_diff']['good_trace_artifact']}`",
            f"- bad_trace: `{report['trace_diff']['bad_trace_artifact']}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Trace Diff",
            "",
            f"- changed_vectors: `{report['trace_diff']['difference_count']}`",
            f"- diff_artifact: `{report['trace_diff']['diff_artifact']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    unreal_config = fastdis_orient.normalize_config_payload(fastdis_orient.load_structured(UNREAL_CONFIG))
    godot_config = fastdis_orient.normalize_config_payload(fastdis_orient.load_structured(GODOT_CONFIG))
    known_bad_wrapper = fastdis_orient.load_structured(KNOWN_BAD)
    known_bad_config = fastdis_orient.normalize_config_payload(known_bad_wrapper)

    unreal_compare = fastdis_orient.compare_payload(FIXTURES, unreal_config, "unreal")
    godot_compare = fastdis_orient.compare_payload(FIXTURES, godot_config, "godot")
    bad_compare = fastdis_orient.compare_payload(FIXTURES, known_bad_config, "godot")
    diagnosis = fastdis_orient.diagnose_payload(bad_compare)
    solver = fastdis_orient.solve_payload(FIXTURES, known_bad_config, "godot", "asset_axes")

    compare_unreal_path = out_dir / "orientation_compare_unreal.json"
    compare_godot_path = out_dir / "orientation_compare_godot.json"
    compare_bad_path = out_dir / "orientation_compare_godot_known_bad.json"
    diagnose_path = out_dir / "orientation_diagnose_godot_known_bad.json"
    solve_path = out_dir / "orientation_solve_godot_known_bad.json"
    fastdis_orient.dump_json(compare_unreal_path, unreal_compare)
    fastdis_orient.dump_json(compare_godot_path, godot_compare)
    fastdis_orient.dump_json(compare_bad_path, bad_compare)
    fastdis_orient.dump_json(diagnose_path, diagnosis)
    fastdis_orient.dump_json(solve_path, solver)
    (out_dir / "orientation_compare_godot_known_bad.md").write_text(
        fastdis_orient.format_compare_markdown(bad_compare),
        encoding="utf-8",
    )

    case = fastdis_orient.load_case(FIXTURES, "level_north")
    bad_trace = fastdis_orient.compute_trace(case, known_bad_config)
    good_trace = fastdis_orient.compute_trace(case, godot_config)
    diff = fastdis_orient.diff_trace_payload(bad_trace, good_trace)

    trace_good_path = out_dir / "orientation_trace_godot_good_level_north.json"
    trace_bad_path = out_dir / "orientation_trace_godot_bad_level_north.json"
    diff_path = out_dir / "orientation_diff_godot_level_north.json"
    fastdis_orient.dump_json(trace_good_path, good_trace)
    fastdis_orient.dump_json(trace_bad_path, bad_trace)
    fastdis_orient.dump_json(diff_path, diff)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "fixtures": display_path(FIXTURES),
        "good_configs": {
            "unreal": {
                "config_path": display_path(UNREAL_CONFIG),
                "config_hash": unreal_compare["config_hash"],
                "config": unreal_config,
                "pass_count": unreal_compare["summary"]["pass_count"],
                "case_count": unreal_compare["summary"]["case_count"],
                "report_artifact": display_path(compare_unreal_path),
            },
            "godot": {
                "config_path": display_path(GODOT_CONFIG),
                "config_hash": godot_compare["config_hash"],
                "config": godot_config,
                "pass_count": godot_compare["summary"]["pass_count"],
                "case_count": godot_compare["summary"]["case_count"],
                "report_artifact": display_path(compare_godot_path),
            },
        },
        "known_bad": {
            "config_path": display_path(KNOWN_BAD),
            "config_hash": bad_compare["config_hash"],
            "config": known_bad_config,
            "expected_signature": known_bad_wrapper["expected_signature"],
            "most_likely_issue": diagnosis["most_likely_issue"],
            "suggestion": diagnosis["suggestion"],
            "report_artifact": display_path(compare_bad_path),
            "diagnose_artifact": display_path(diagnose_path),
        },
        "solver": {
            "artifact": display_path(solve_path),
            "top_candidates": solver["candidates"][:5],
        },
        "trace_diff": {
            "good_trace_artifact": display_path(trace_good_path),
            "bad_trace_artifact": display_path(trace_bad_path),
            "diff_artifact": display_path(diff_path),
            "difference_count": len(diff["differences"]),
        },
    }

    json_path = out_dir / "orientation_pipeline_report.json"
    md_path = out_dir / "orientation_pipeline_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
