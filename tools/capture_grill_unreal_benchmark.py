#!/usr/bin/env python3
"""Capture a GRILL Unreal benchmark baseline in the shared experiment/report shape."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import grill_harness_capture
import grill_paths
import normalize_grill_harness_capture


DEFAULT_PLUGIN_ROOT = grill_paths.UNREAL_PLUGIN
DEFAULT_MEASUREMENTS = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_measurements.json"
DEFAULT_RAW_OUT = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_benchmark_baseline.json"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "engine_benchmarks"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _git_output(path: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value or None


def _as_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    rows: list[int] = []
    for item in value:
        if isinstance(item, bool):
            rows.append(int(item))
        elif isinstance(item, int):
            rows.append(item)
    return rows


def _host_summary() -> dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }


def _scenario_block(measurements: dict[str, Any], *, map_name: str, traffic_mix: str) -> dict[str, Any]:
    source = measurements.get("scenario")
    scenario = source if isinstance(source, dict) else {}
    return {
        "environment_name": str(scenario.get("environment_name") or map_name),
        "traffic_mix": str(scenario.get("traffic_mix") or traffic_mix),
        "entity_counts": _as_int_list(scenario.get("entity_counts")),
        "update_hz": _as_int_list(scenario.get("update_hz")),
        "notes": scenario.get("notes") if isinstance(scenario.get("notes"), str) else None,
    }


def _runtime_block(measurements: dict[str, Any], *, engine_version: str, plugin_commit: str | None) -> dict[str, Any]:
    source = measurements.get("runtime")
    runtime = source if isinstance(source, dict) else {}
    return {
        "engine_family": "unreal",
        "version": str(runtime.get("version") or engine_version),
        "render_pipeline": runtime.get("render_pipeline") if isinstance(runtime.get("render_pipeline"), str) else None,
        "scripting_backend": runtime.get("scripting_backend") if isinstance(runtime.get("scripting_backend"), str) else None,
        "build_configuration": runtime.get("build_configuration") if isinstance(runtime.get("build_configuration"), str) else None,
        "plugin_commit": runtime.get("plugin_commit") if isinstance(runtime.get("plugin_commit"), str) else plugin_commit,
        "plugin_version": runtime.get("plugin_version") if isinstance(runtime.get("plugin_version"), str) else None,
    }


def _results_block(measurements: dict[str, Any]) -> list[dict[str, Any]]:
    results = measurements.get("results")
    if not isinstance(results, list):
        raise ValueError("measurements JSON must contain a non-empty `results` array")
    rows = [row for row in results if isinstance(row, dict)]
    if not rows:
        raise ValueError("measurements JSON must contain at least one object row in `results`")
    return rows


def build_baseline_payload(
    measurements: dict[str, Any],
    *,
    plugin_root: Path,
    engine_version: str,
    map_name: str,
    traffic_mix: str,
) -> dict[str, Any]:
    repo_url = _git_output(plugin_root, "remote", "get-url", "origin") or "https://github.com/AF-GRILL/DISPluginForUnreal"
    repo_commit = _git_output(plugin_root, "rev-parse", "HEAD") or "unknown"
    runtime = _runtime_block(measurements, engine_version=engine_version, plugin_commit=repo_commit)
    scenario = _scenario_block(measurements, map_name=map_name, traffic_mix=traffic_mix)
    return {
        "schema": "fastdis.unreal_grill_benchmark_baseline.v1",
        "product": "GRILL DIS for Unreal",
        "captured_at_utc": _utc_now(),
        "repository": {
            "url": repo_url,
            "commit": repo_commit,
        },
        "engine": {
            "version": runtime["version"],
        },
        "host": _host_summary(),
        "scenario": {
            "map": scenario["environment_name"],
            "traffic_mix": scenario["traffic_mix"],
            "entity_counts": scenario["entity_counts"],
            "update_hz": scenario["update_hz"],
            "notes": scenario["notes"],
        },
        "results": _results_block(measurements),
    }


def build_capture_payload(
    measurements: dict[str, Any],
    *,
    plugin_root: Path,
    engine_version: str,
    map_name: str,
    traffic_mix: str,
) -> dict[str, Any]:
    baseline = build_baseline_payload(
        measurements,
        plugin_root=plugin_root,
        engine_version=engine_version,
        map_name=map_name,
        traffic_mix=traffic_mix,
    )
    runtime = _runtime_block(
        measurements,
        engine_version=str((baseline.get("engine") or {}).get("version") or engine_version),
        plugin_commit=(baseline.get("repository") or {}).get("commit") if isinstance(baseline.get("repository"), dict) else None,
    )
    payload = {
        "schema": "fastdis.grill_harness_capture.v1",
        "lane": "unreal_vs_grill",
        "product": "GRILL DIS for Unreal",
        "captured_at_utc": baseline["captured_at_utc"],
        "repository": {
            **baseline["repository"],
            "plugin_version": runtime.get("plugin_version"),
        },
        "host": baseline["host"],
        "runtime": runtime,
        "scenario": {
            "environment_name": baseline["scenario"]["map"],
            "traffic_mix": baseline["scenario"]["traffic_mix"],
            "entity_counts": baseline["scenario"]["entity_counts"],
            "update_hz": baseline["scenario"]["update_hz"],
            "notes": baseline["scenario"]["notes"],
        },
        "results": baseline["results"],
    }
    errors = grill_harness_capture.validate_payload(payload, expected_lane="unreal_vs_grill")
    if errors:
        raise ValueError("; ".join(errors))
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", type=Path, default=DEFAULT_MEASUREMENTS, help="Measured Unreal GRILL row payload JSON")
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    parser.add_argument("--engine-version", default="5.8")
    parser.add_argument("--map", default="LoopbackBench")
    parser.add_argument("--traffic-mix", default="100% Entity State")
    parser.add_argument("--raw-out", type=Path, default=DEFAULT_RAW_OUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    measurements_path = args.measurements.expanduser().resolve()
    plugin_root = args.plugin_root.expanduser().resolve()
    raw_out = args.raw_out.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()

    if not measurements_path.is_file():
        print(f"missing measurements: {_display_path(measurements_path)}")
        return 2
    if raw_out.exists() and not args.overwrite:
        print(f"refusing to overwrite existing raw capture: {_display_path(raw_out)}")
        return 3

    baseline = build_baseline_payload(
        _load_json(measurements_path),
        plugin_root=plugin_root,
        engine_version=args.engine_version,
        map_name=args.map,
        traffic_mix=args.traffic_mix,
    )
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    raw_out.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    print(f"raw: {_display_path(raw_out)}")

    normalize_code = normalize_grill_harness_capture.main(
        ["--input", str(raw_out), "--out-dir", str(out_dir)]
    )
    return normalize_code


if __name__ == "__main__":
    raise SystemExit(main())
