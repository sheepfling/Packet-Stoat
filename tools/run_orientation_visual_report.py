#!/usr/bin/env python3
"""Capture visual-scene style orientation proof from Unreal and Godot."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import re
from pathlib import Path
import subprocess
import tempfile

import godot_env
import load_local_env
import unreal_env
import run_unreal_orientation_verification


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "verification_reports" / "alpha2_sample"
SCENE_RE = re.compile(
    r"FASTDIS_ORIENTATION_SCENE\s+case=(?P<case>\S+)\s+status=(?P<status>PASS|FAIL)\s+"
    r"forward_angle_deg=(?P<forward_angle>[-+0-9.eE]+)\s+forward_dot=(?P<forward_dot>[-+0-9.eE]+)\s+"
    r"right_angle_deg=(?P<right_angle>[-+0-9.eE]+)\s+right_dot=(?P<right_dot>[-+0-9.eE]+)\s+"
    r"up_angle_deg=(?P<up_angle>[-+0-9.eE]+)\s+up_dot=(?P<up_dot>[-+0-9.eE]+)\s+"
    r"threshold_deg=(?P<threshold>[-+0-9.eE]+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown/raw log artifacts")
    parser.add_argument(
        "--engine-version",
        dest="engine_versions",
        action="append",
        help="Unreal engine version for the visual proof lane; pass multiple times for a host matrix",
    )
    parser.add_argument("--skip-unreal", action="store_true", help="Skip the Unreal visual proof lane")
    parser.add_argument("--skip-godot", action="store_true", help="Skip the Godot visual proof lane")
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_step(cmd: list[str]) -> tuple[int, str]:
    with tempfile.TemporaryFile(mode="w+b") as capture:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=capture,
            stderr=subprocess.STDOUT,
        )
        capture.seek(0)
        output = capture.read().decode("utf-8", errors="replace")
    return completed.returncode, output


def parse_scene_events(text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for match in SCENE_RE.finditer(text):
        events.append(
            {
                "case": match.group("case"),
                "status": match.group("status").lower(),
                "forward_angle_deg": float(match.group("forward_angle")),
                "forward_dot": float(match.group("forward_dot")),
                "right_angle_deg": float(match.group("right_angle")),
                "right_dot": float(match.group("right_dot")),
                "up_angle_deg": float(match.group("up_angle")),
                "up_dot": float(match.group("up_dot")),
                "threshold_deg": float(match.group("threshold")),
            }
        )
    deduped: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for event in events:
        key = (
            event["case"],
            event["status"],
            event["forward_angle_deg"],
            event["forward_dot"],
            event["right_angle_deg"],
            event["right_dot"],
            event["up_angle_deg"],
            event["up_dot"],
            event["threshold_deg"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def summarize_scene_events(events: list[dict[str, object]]) -> dict[str, object]:
    if not events:
        return {
            "event_count": 0,
            "case_count": 0,
            "failure_count": 0,
            "max_angle_deg": None,
            "min_dot": None,
        }
    return {
        "event_count": len(events),
        "case_count": len({event["case"] for event in events}),
        "failure_count": sum(1 for event in events if event["status"] != "pass"),
        "max_angle_deg": max(
            max(float(event["forward_angle_deg"]), float(event["right_angle_deg"]), float(event["up_angle_deg"]))
            for event in events
        ),
        "min_dot": min(
            min(float(event["forward_dot"]), float(event["right_dot"]), float(event["up_dot"]))
            for event in events
        ),
    }


def render_markdown(report: dict[str, object]) -> str:
    unreal_versions = report["unreal_engine_versions"]
    lines = [
        "# Orientation Visual Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- host_platform: `{report['host_platform']}`",
        f"- unreal_engine_versions: `{', '.join(unreal_versions) if unreal_versions else 'none'}`",
        "",
        "| Lane | Status | Cases | Max Angle (deg) | Min Dot | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for version in unreal_versions:
        lane = report["lanes"]["unreal"][version]
        summary = lane["summary"]
        notes = "; ".join(lane["notes"]) if lane["notes"] else "none"
        max_angle = "n/a" if summary["max_angle_deg"] is None else f"{summary['max_angle_deg']:.8f}"
        min_dot = "n/a" if summary["min_dot"] is None else f"{summary['min_dot']:.8f}"
        lines.append(f"| unreal-{version} | {lane['status']} | {summary['case_count']} | {max_angle} | {min_dot} | {notes} |")
    for lane_name in ("godot",):
        lane = report["lanes"][lane_name]
        summary = lane["summary"]
        notes = "; ".join(lane["notes"]) if lane["notes"] else "none"
        max_angle = "n/a" if summary["max_angle_deg"] is None else f"{summary['max_angle_deg']:.8f}"
        min_dot = "n/a" if summary["min_dot"] is None else f"{summary['min_dot']:.8f}"
        lines.append(f"| {lane_name} | {lane['status']} | {summary['case_count']} | {max_angle} | {min_dot} | {notes} |")
    lines.extend(["", "## Raw Artifacts", ""])
    for version in unreal_versions:
        lane = report["lanes"]["unreal"][version]
        if lane.get("raw_output_path"):
            lines.append(f"- unreal {version} raw output: `{lane['raw_output_path']}`")
        if lane.get("harness_log_path"):
            lines.append(f"- unreal {version} harness log: `{lane['harness_log_path']}`")
    for lane_name in ("godot",):
        lane = report["lanes"][lane_name]
        if lane.get("raw_output_path"):
            lines.append(f"- {lane_name} raw output: `{lane['raw_output_path']}`")
        if lane.get("harness_log_path"):
            lines.append(f"- {lane_name} harness log: `{lane['harness_log_path']}`")
    lines.append("")
    return "\n".join(lines)


def run_unreal_lane(engine_version: str, out_dir: Path) -> dict[str, object]:
    run_unreal_orientation_verification.clear_harness_log()
    cmd = unreal_env.python_command() + [
        "tools/run_unreal_orientation_verification.py",
        "--engine-version",
        engine_version,
    ]
    code, output = run_step(cmd)
    raw_path = out_dir / f"unreal_orientation_visual_{engine_version.replace('.', '_')}.log"
    raw_path.write_text(output, encoding="utf-8")
    combined = output
    harness_log_path: str | None = None
    if run_unreal_orientation_verification.HARNESS_LOG_PATH.is_file():
        log_text = run_unreal_orientation_verification.HARNESS_LOG_PATH.read_text(encoding="utf-8", errors="replace")
        staged = out_dir / f"unreal_orientation_visual_harness_{engine_version.replace('.', '_')}.log"
        staged.write_text(log_text, encoding="utf-8")
        harness_log_path = display_path(staged)
        combined = output + "\n" + log_text
    events = parse_scene_events(combined)
    status = "passed" if code == 0 and events else ("failed" if code != 0 else "needs-attention")
    notes: list[str] = []
    if code != 0:
        notes.append("Unreal visual proof lane exited non-zero")
    if not events:
        notes.append("no structured scene events parsed from Unreal output")
    return {
        "status": status,
        "returncode": code,
        "command": cmd,
        "notes": notes,
        "events": events,
        "summary": summarize_scene_events(events),
        "raw_output_path": display_path(raw_path),
        "harness_log_path": harness_log_path,
    }


def run_godot_lane(out_dir: Path) -> dict[str, object]:
    cmd = godot_env.python_command() + [
        "tools/run_godot_orientation_visual_scene.py",
        "--skip-build",
    ]
    code, output = run_step(cmd)
    raw_path = out_dir / "godot_orientation_visual.log"
    raw_path.write_text(output, encoding="utf-8")
    events = parse_scene_events(output)
    status = "passed" if code == 0 and events else ("failed" if code != 0 else "needs-attention")
    notes: list[str] = []
    if code != 0:
        notes.append("Godot visual proof lane exited non-zero")
    if not events:
        notes.append("no structured scene events parsed from Godot output")
    return {
        "status": status,
        "returncode": code,
        "command": cmd,
        "notes": notes,
        "events": events,
        "summary": summarize_scene_events(events),
        "raw_output_path": display_path(raw_path),
    }


def main() -> int:
    load_local_env.load()
    args = parse_args()
    engine_versions = args.engine_versions or ["5.8"]
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "host_platform": godot_env.host_platform_name(),
        "unreal_engine_versions": engine_versions,
        "lanes": {
            "unreal": {
                version: {"status": "skipped", "notes": [], "events": [], "summary": summarize_scene_events([])}
                for version in engine_versions
            },
            "godot": {"status": "skipped", "notes": [], "events": [], "summary": summarize_scene_events([])},
        },
    }
    overall_ok = True
    if not args.skip_unreal:
        for version in engine_versions:
            report["lanes"]["unreal"][version] = run_unreal_lane(version, out_dir)
            overall_ok = overall_ok and report["lanes"]["unreal"][version]["status"] == "passed"
    if not args.skip_godot:
        report["lanes"]["godot"] = run_godot_lane(out_dir)
        overall_ok = overall_ok and report["lanes"]["godot"]["status"] == "passed"

    json_path = out_dir / "orientation_visual_report.json"
    md_path = out_dir / "orientation_visual_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if overall_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
