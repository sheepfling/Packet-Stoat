#!/usr/bin/env python3
"""Run the Cesium plugin proof lanes with stable presets and rerunnable reports."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import shlex
import subprocess
import sys
import threading
from typing import Any

from artifacts import REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPORTS_DIR / "cesium_lane_runner"
DEFAULT_JSON_OUT = DEFAULT_OUT_DIR / "cesium_plugin_lanes.json"
DEFAULT_MD_OUT = DEFAULT_OUT_DIR / "cesium_plugin_lanes.md"
DEFAULT_LOG_DIR = DEFAULT_OUT_DIR / "logs"
DEFAULT_LANES = [
    "unreal-vendor",
    "unity-vendor",
    "godot-vendor",
    "godot-linux-docker",
]


def preferred_python() -> str:
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable or "python"


def _py(command: str) -> str:
    if not command.startswith("python "):
        return command
    return f"{shlex.quote(preferred_python())} {command[len('python '):]}"


@dataclass(frozen=True)
class LaneTask:
    id: str
    label: str
    commands: tuple[str, ...]
    artifacts: tuple[str, ...]
    accepted_returncodes: tuple[int, ...] = (0,)


@dataclass(frozen=True)
class LaneSpec:
    id: str
    label: str
    artifact_namespace: str
    lane_kind: str
    commands_source: str
    parallel_safe: bool
    tasks: tuple[LaneTask, ...]


def lane_catalog() -> dict[str, LaneSpec]:
    return {
        "unreal-vendor": LaneSpec(
            "unreal-vendor",
            "Cesium Unreal Vendor",
            "unreal_vendor_plugin",
            "vendor",
            "builtin:cesium-unreal-vendor",
            True,
            (
                LaneTask(
                    id="cesium-unreal-vendor-prepare-source",
                    label="Cesium Unreal Vendor Prepare Source",
                    commands=(_py("python tools/unreal_vendor_workflow.py prepare-source --vendor cesium --engine-version 5.8 --plugin-root external/cesium/cesium-unreal --clean-build"),),
                    artifacts=(),
                ),
                LaneTask(
                    id="cesium-unreal-vendor-doctor",
                    label="Cesium Unreal Vendor Doctor",
                    commands=(_py("python tools/unreal_vendor_workflow.py doctor --vendor cesium --plugin-root external/cesium/cesium-unreal"),),
                    artifacts=(),
                ),
                LaneTask(
                    id="cesium-unreal-vendor-install-smoke",
                    label="Cesium Unreal Vendor Install Smoke",
                    commands=(_py("python tools/unreal_vendor_workflow.py install-smoke --vendor cesium --engine-version 5.7 --plugin-root external/cesium/cesium-unreal"),),
                    artifacts=(
                        "artifacts/reports/unreal_vendor_plugin/cesium_5_7_install_smoke.json",
                        "artifacts/reports/unreal_vendor_plugin/cesium_5_7_install_smoke.md",
                    ),
                ),
                LaneTask(
                    id="cesium-unreal-vendor-matrix",
                    label="Cesium Unreal Vendor Matrix",
                    commands=(_py("python tools/unreal_vendor_workflow.py full --vendor cesium --plugin-root external/cesium/cesium-unreal"),),
                    artifacts=(
                        "artifacts/reports/unreal_vendor_plugin/cesium_matrix.json",
                        "artifacts/reports/unreal_vendor_plugin/cesium_matrix.md",
                    ),
                ),
            ),
        ),
        "unity-vendor": LaneSpec(
            "unity-vendor",
            "Cesium Unity Vendor",
            "unity_vendor_plugin",
            "vendor",
            "builtin:cesium-unity-vendor",
            True,
            (
                LaneTask(
                    id="cesium-unity-vendor-prepare-source",
                    label="Cesium Unity Vendor Prepare Source",
                    commands=(_py("python tools/unity_vendor_workflow.py prepare-source --vendor cesium-unity --plugin-root external/cesium/cesium-unity"),),
                    artifacts=(),
                ),
                LaneTask(
                    id="cesium-unity-vendor-doctor",
                    label="Cesium Unity Vendor Doctor",
                    commands=(_py("python tools/unity_vendor_workflow.py doctor --vendor cesium-unity --unity-version 6000.5 --plugin-root external/cesium/cesium-unity"),),
                    artifacts=(),
                ),
                LaneTask(
                    id="cesium-unity-vendor-build",
                    label="Cesium Unity Vendor Build",
                    commands=(_py("python tools/unity_vendor_workflow.py build --vendor cesium-unity --unity-version 6000.5 --plugin-root external/cesium/cesium-unity --clean-project"),),
                    artifacts=(
                        "artifacts/reports/unity_vendor_plugin/cesium-unity_6000_5.json",
                        "artifacts/reports/unity_vendor_plugin/cesium-unity_6000_5.md",
                    ),
                ),
            ),
        ),
        "godot-vendor": LaneSpec(
            "godot-vendor",
            "Cesium Godot Vendor",
            "godot_vendor_plugin",
            "vendor",
            "builtin:cesium-godot-vendor",
            True,
            (
                LaneTask(
                    id="cesium-godot-vendor-doctor",
                    label="Cesium Godot Vendor Doctor",
                    commands=(_py("python tools/godot_vendor_workflow.py doctor --vendor cesium-godot --plugin-root external/cesium/3D-Tiles-For-Godot"),),
                    artifacts=(),
                ),
                LaneTask(
                    id="cesium-godot-vendor-report",
                    label="Cesium Godot Vendor Report",
                    commands=(_py("python tools/godot_vendor_workflow.py report --vendor cesium-godot --plugin-root external/cesium/3D-Tiles-For-Godot"),),
                    artifacts=(),
                ),
                LaneTask(
                    id="cesium-godot-vendor-full",
                    label="Cesium Godot Vendor Full",
                    commands=(_py("python tools/godot_vendor_workflow.py full --vendor cesium-godot --plugin-root external/cesium/3D-Tiles-For-Godot"),),
                    artifacts=(
                        "artifacts/reports/godot_vendor_plugin/cesium-godot_build.json",
                        "artifacts/reports/godot_vendor_plugin/cesium-godot_build.md",
                    ),
                ),
            ),
        ),
        "godot-linux-docker": LaneSpec(
            id="godot-linux-docker",
            label="Cesium Godot Linux Docker",
            artifact_namespace="godot_vendor_plugin",
            lane_kind="vendor-docker",
            commands_source="custom:run_godot_vendor_linux_docker",
            parallel_safe=False,
            tasks=(
                LaneTask(
                    id="godot-linux-docker-proof",
                    label="Godot Linux Docker Proof",
                    commands=(
                        _py("python tools/run_godot_vendor_linux_docker.py ")
                        + (
                        "--docker-log-mode tee "
                        "--inner-log-mode tee "
                        "--log-tail-lines 120 "
                        "--timeout-seconds 3600 "
                        "--preserve "
                        "--preserve-label godot-4.7-green-long"
                        ),
                    ),
                    artifacts=(
                        "artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker.json",
                        "artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker.md",
                    ),
                ),
            ),
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes", nargs="+", default=DEFAULT_LANES, help="Lane ids to run, or 'all'")
    parser.add_argument("--parallel", action="store_true", help="Run compatible lanes in parallel when artifact namespaces do not overlap")
    parser.add_argument("--refresh-matrix", action="store_true", help="Run tools/build_cesium_engine_matrix.py after lane execution")
    parser.add_argument("--dry-run", action="store_true", help="Print the exact commands without executing them")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    return parser.parse_args(argv)


def resolve_lanes(selected: list[str]) -> list[LaneSpec]:
    catalog = lane_catalog()
    if selected == ["all"] or "all" in selected:
        return [catalog[lane_id] for lane_id in DEFAULT_LANES]
    missing = [lane_id for lane_id in selected if lane_id not in catalog]
    if missing:
        raise SystemExit(f"Unknown lane ids: {', '.join(missing)}")
    return [catalog[lane_id] for lane_id in selected]


def _command_log_path(log_dir: Path, lane: LaneSpec, task: LaneTask, command_index: int) -> Path:
    return log_dir / lane.id / f"{task.id}_{command_index + 1}.log"


def _run_command(command: str, *, log_path: Path, prefix: str) -> dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            shlex.split(command),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            print(f"[{prefix}] {line}", end="", flush=True)
        returncode = process.wait()
    return {
        "command": command,
        "log": str(log_path),
        "returncode": returncode,
    }


def run_lane(lane: LaneSpec, *, log_dir: Path, dry_run: bool) -> dict[str, Any]:
    started_at = datetime.now(UTC).isoformat()
    task_rows: list[dict[str, Any]] = []
    status = "pass"
    for task in lane.tasks:
        command_rows: list[dict[str, Any]] = []
        if dry_run:
            for command_index, command in enumerate(task.commands):
                command_rows.append(
                    {
                        "command": command,
                        "log": str(_command_log_path(log_dir, lane, task, command_index)),
                        "returncode": None,
                    }
                )
            task_rows.append(
                {
                    "id": task.id,
                    "label": task.label,
                    "status": "dry-run",
                    "commands": command_rows,
                    "artifacts": list(task.artifacts),
                }
            )
            continue
        task_status = "pass"
        for command_index, command in enumerate(task.commands):
            row = _run_command(
                command,
                log_path=_command_log_path(log_dir, lane, task, command_index),
                prefix=f"{lane.id}:{task.id}",
            )
            command_rows.append(row)
            if row["returncode"] not in task.accepted_returncodes:
                task_status = "fail"
                status = "fail"
                break
        task_rows.append(
            {
                "id": task.id,
                "label": task.label,
                "status": task_status,
                "commands": command_rows,
                "artifacts": list(task.artifacts),
            }
        )
        if task_status == "fail":
            break
    completed_at = datetime.now(UTC).isoformat()
    if dry_run:
        status = "dry-run"
    return {
        "id": lane.id,
        "label": lane.label,
        "lane_kind": lane.lane_kind,
        "artifact_namespace": lane.artifact_namespace,
        "commands_source": lane.commands_source,
        "parallel_safe": lane.parallel_safe,
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "tasks": task_rows,
    }


def _run_parallel_group(lanes: list[LaneSpec], *, log_dir: Path, dry_run: bool) -> list[dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    print_lock = threading.Lock()

    def run_one(lane: LaneSpec) -> dict[str, Any]:
        with print_lock:
            print(f"[lane] starting {lane.id}", flush=True)
        return run_lane(lane, log_dir=log_dir, dry_run=dry_run)

    with ThreadPoolExecutor(max_workers=len(lanes)) as executor:
        future_map = {executor.submit(run_one, lane): lane.id for lane in lanes}
        for future in as_completed(future_map):
            lane_id = future_map[future]
            results[lane_id] = future.result()
    return [results[lane.id] for lane in lanes]


def execute_lanes(lanes: list[LaneSpec], *, log_dir: Path, dry_run: bool, parallel: bool) -> list[dict[str, Any]]:
    if dry_run or not parallel:
        return [run_lane(lane, log_dir=log_dir, dry_run=dry_run) for lane in lanes]

    results: list[dict[str, Any]] = []
    pending: list[LaneSpec] = []
    active_namespaces: set[str] = set()

    def flush_pending() -> None:
        nonlocal pending, active_namespaces, results
        if not pending:
            return
        if len(pending) == 1:
            results.append(run_lane(pending[0], log_dir=log_dir, dry_run=False))
        else:
            results.extend(_run_parallel_group(pending, log_dir=log_dir, dry_run=False))
        pending = []
        active_namespaces = set()

    for lane in lanes:
        if not lane.parallel_safe or lane.artifact_namespace in active_namespaces:
            flush_pending()
            results.append(run_lane(lane, log_dir=log_dir, dry_run=False))
            continue
        pending.append(lane)
        active_namespaces.add(lane.artifact_namespace)
    flush_pending()
    return results


def maybe_refresh_matrix(*, dry_run: bool, log_dir: Path) -> dict[str, Any]:
    command = _py("python tools/build_cesium_engine_matrix.py")
    task = LaneTask(
        id="refresh-matrix",
        label="Refresh Cesium Engine Matrix",
        commands=(command,),
        artifacts=(
            "artifacts/reports/cesium_engine_matrix/cesium_engine_matrix.json",
            "artifacts/reports/cesium_engine_matrix/cesium_engine_matrix.md",
        ),
        accepted_returncodes=(0, 2),
    )
    lane = LaneSpec(
        id="matrix-refresh",
        label="Cesium Engine Matrix Refresh",
        artifact_namespace="cesium_engine_matrix",
        lane_kind="report",
        commands_source="custom:build_cesium_engine_matrix",
        parallel_safe=False,
        tasks=(task,),
    )
    return run_lane(lane, log_dir=log_dir, dry_run=dry_run)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    lanes = resolve_lanes(args.lanes)
    lane_results = execute_lanes(
        lanes,
        log_dir=args.log_dir.expanduser().resolve(),
        dry_run=args.dry_run,
        parallel=args.parallel,
    )
    if args.refresh_matrix:
        lane_results.append(maybe_refresh_matrix(dry_run=args.dry_run, log_dir=args.log_dir.expanduser().resolve()))
    statuses = [row["status"] for row in lane_results]
    if statuses and all(status == "pass" for status in statuses):
        overall_status = "pass"
    elif any(status == "fail" for status in statuses):
        overall_status = "fail"
    else:
        overall_status = "dry-run"
    return {
        "schema": "packet_stoat.cesium_plugin_lane_runner.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall_status,
        "parallel_requested": bool(args.parallel),
        "dry_run": bool(args.dry_run),
        "selected_lanes": [lane.id for lane in lanes],
        "log_dir": str(args.log_dir.expanduser().resolve()),
        "lanes": lane_results,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Cesium Plugin Lane Runner",
        "",
        f"- overall_status: `{payload['overall_status']}`",
        f"- dry_run: `{payload['dry_run']}`",
        f"- parallel_requested: `{payload['parallel_requested']}`",
        f"- generated_at: `{payload['generated_at']}`",
        f"- log_dir: `{payload['log_dir']}`",
        "",
        "## Lanes",
        "",
        "| Lane | Status | Kind | Source |",
        "| --- | --- | --- | --- |",
    ]
    for lane in payload.get("lanes", []):
        lines.append(
            f"| `{lane['id']}` | `{lane['status']}` | `{lane['lane_kind']}` | `{lane['commands_source']}` |"
        )
    lines.extend(["", "## Commands", ""])
    for lane in payload.get("lanes", []):
        lines.append(f"- `{lane['id']}`")
        for task in lane.get("tasks", []):
            lines.append(f"  - `{task['id']}`: `{task['status']}`")
            for command in task.get("commands", []):
                lines.append(f"    - `{command['command']}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["overall_status"] in {"pass", "dry-run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
