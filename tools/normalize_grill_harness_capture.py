#!/usr/bin/env python3
"""Normalize a typed GRILL harness capture into the shared engine-benchmark report shape."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import grill_harness_capture
import normalize_unity_grill_baseline
import normalize_unreal_grill_baseline


DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_benchmarks"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"skip: missing {display_path(args.input)}")
        return 0
    payload = load_json(args.input)
    lane = grill_harness_capture.detect_lane(payload)
    errors = grill_harness_capture.validate_payload(payload, expected_lane=lane)
    if errors:
        for error in errors:
            print(error)
        return 1
    if lane == "unity_vs_grill":
        report = normalize_unity_grill_baseline.normalize_payload(payload, source_payload=display_path(args.input))
        stem = "grill_unity_engine_benchmark_report"
        markdown = normalize_unity_grill_baseline.render_markdown(report)
    elif lane == "unreal_vs_grill":
        report = normalize_unreal_grill_baseline.normalize_payload(payload, source_payload=display_path(args.input))
        stem = "grill_unreal_engine_benchmark_report"
        markdown = normalize_unreal_grill_baseline.render_markdown(report)
    else:
        print(f"unsupported lane: {lane}")
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"{stem}.json"
    md_path = args.out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown + "\n", encoding="utf-8")
    print(f"json: {display_path(json_path)}")
    print(f"md: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
