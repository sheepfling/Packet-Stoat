#!/usr/bin/env python3
"""Scaffold a GRILL Unity benchmark baseline JSON from the tracked template."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.template.json"
DEFAULT_FASTDIS = ROOT / "build" / "benchmark_results" / "current" / "current.json"
DEFAULT_OUT = ROOT / "verification_reports" / "unity_grill_baseline" / "grill_unity_benchmark_baseline.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--fastdis", type=Path, default=DEFAULT_FASTDIS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--unity-version", default="REPLACE_ME_UNITY_VERSION")
    parser.add_argument("--scene", default="REPLACE_ME_SCENE_NAME")
    parser.add_argument("--traffic-mix", default="REPLACE_ME_TRAFFIC_MIX")
    parser.add_argument("--scripting-backend", default="REPLACE_ME_SCRIPTING_BACKEND")
    parser.add_argument("--commit", default="REPLACE_ME_COMMIT")
    parser.add_argument("--limit-cases", type=int, default=12)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def build_result_rows(fastdis_payload: dict[str, Any] | None, limit_cases: int) -> list[dict[str, Any]]:
    default_row = {
        "case": "REPLACE_ME_CASE_NAME_MATCHING_FASTDIS_WHEN_POSSIBLE",
        "entity_count": 1000,
        "update_hz": 60,
        "packets_per_sec": 0,
        "main_thread_ms_avg": 0.0,
        "gc_alloc_bytes_per_frame": 0,
        "notes": "Replace this template row with measured data. Use the same case name as the FastDIS comparison run when you want automatic matching in the side-by-side report.",
    }
    if fastdis_payload is None:
        return [default_row]
    native_rows = (fastdis_payload.get("native") or {}).get("results") or []
    if not isinstance(native_rows, list):
        return [default_row]
    scaffolded: list[dict[str, Any]] = []
    for row in native_rows[: max(1, limit_cases)]:
        if not isinstance(row, dict):
            continue
        case = row.get("case")
        if not isinstance(case, str):
            continue
        scaffolded.append(
            {
                "case": case,
                "entity_count": 1000,
                "update_hz": 60,
                "packets_per_sec": 0,
                "main_thread_ms_avg": 0.0,
                "gc_alloc_bytes_per_frame": 0,
                "notes": f"Populate this GRILL measurement for the FastDIS case `{case}`.",
            }
        )
    return scaffolded or [default_row]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.out.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {args.out}")
    payload = load_json(args.template)
    fastdis_payload = load_json(args.fastdis) if args.fastdis.exists() else None
    payload["captured_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["repository"]["commit"] = args.commit
    payload["unity"]["version"] = args.unity_version
    payload["unity"]["scripting_backend"] = args.scripting_backend
    payload["host"]["system"] = platform.system()
    payload["host"]["release"] = platform.release()
    payload["host"]["machine"] = platform.machine()
    payload["scenario"]["scene"] = args.scene
    payload["scenario"]["traffic_mix"] = args.traffic_mix
    payload["results"] = build_result_rows(fastdis_payload, args.limit_cases)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"unity grill baseline scaffold: {display_path(args.out)}")
    print(f"template: {display_path(args.template)}")
    print(f"fastdis benchmark source: {display_path(args.fastdis)} exists={args.fastdis.exists()}")
    print(f"scaffolded result rows: {len(payload['results'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
