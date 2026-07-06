from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_cesium_plugin_lanes


def test_dry_run_expands_named_lanes() -> None:
    args = run_cesium_plugin_lanes.parse_args(
        [
            "--dry-run",
            "--lanes",
            "unreal-vendor",
            "godot-linux-docker",
        ]
    )

    payload = run_cesium_plugin_lanes.build_payload(args)

    assert payload["overall_status"] == "dry-run"
    assert payload["selected_lanes"] == ["unreal-vendor", "godot-linux-docker"]
    unreal = payload["lanes"][0]
    docker = payload["lanes"][1]
    assert unreal["tasks"][0]["commands"][0]["command"].endswith("tools/unreal_vendor_workflow.py prepare-source --vendor cesium --engine-version 5.8 --plugin-root external/cesium/cesium-unreal --clean-build")
    assert unreal["tasks"][1]["commands"][0]["command"].endswith("tools/unreal_vendor_workflow.py doctor --vendor cesium --plugin-root external/cesium/cesium-unreal")
    assert unreal["tasks"][-1]["commands"][0]["command"].endswith("tools/unreal_vendor_workflow.py full --vendor cesium --plugin-root external/cesium/cesium-unreal")
    assert "--timeout-seconds 3600" in docker["tasks"][0]["commands"][0]["command"]
    assert "--preserve" in docker["tasks"][0]["commands"][0]["command"]
    assert "external/cesium/cesium-unreal" in unreal["tasks"][0]["commands"][0]["command"]


def test_unreal_linux_docker_lane_uses_dedicated_wrapper() -> None:
    args = run_cesium_plugin_lanes.parse_args(
        [
            "--dry-run",
            "--lanes",
            "unreal-linux-docker",
        ]
    )

    payload = run_cesium_plugin_lanes.build_payload(args)

    lane = payload["lanes"][0]
    command = lane["tasks"][0]["commands"][0]["command"]
    assert "tools/run_unreal_vendor_linux_docker.py" in command
    assert "--timeout-seconds 7200" in command
    assert "--preserve-label unreal-5.8-linux-docker" in command


def test_parallel_plan_keeps_conflicting_godot_lanes_serial(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, str]] = []

    def fake_run_lane(lane, *, log_dir, dry_run):
        calls.append(("single", lane.id))
        return {
            "id": lane.id,
            "label": lane.label,
            "lane_kind": lane.lane_kind,
            "artifact_namespace": lane.artifact_namespace,
            "commands_source": lane.commands_source,
            "parallel_safe": lane.parallel_safe,
            "status": "pass",
            "started_at": "now",
            "completed_at": "later",
            "tasks": [],
        }

    def fake_run_parallel_group(lanes, *, log_dir, dry_run):
        calls.append(("parallel", ",".join(lane.id for lane in lanes)))
        return [fake_run_lane(lane, log_dir=log_dir, dry_run=dry_run) for lane in lanes]

    monkeypatch.setattr(run_cesium_plugin_lanes, "run_lane", fake_run_lane)
    monkeypatch.setattr(run_cesium_plugin_lanes, "_run_parallel_group", fake_run_parallel_group)
    args = run_cesium_plugin_lanes.parse_args(
        [
            "--lanes",
            "unity-vendor",
            "godot-vendor",
            "godot-linux-docker",
            "--parallel",
            "--json-out",
            str(tmp_path / "runner.json"),
            "--md-out",
            str(tmp_path / "runner.md"),
        ]
    )

    payload = run_cesium_plugin_lanes.build_payload(args)

    assert payload["overall_status"] == "pass"
    assert payload["selected_lanes"] == ["unity-vendor", "godot-vendor", "godot-linux-docker"]
    assert calls[0] == ("parallel", "unity-vendor,godot-vendor")
    assert calls[-1] == ("single", "godot-linux-docker")


def test_main_writes_report_files(tmp_path: Path) -> None:
    json_out = tmp_path / "runner.json"
    md_out = tmp_path / "runner.md"

    rc = run_cesium_plugin_lanes.main(
        [
            "--dry-run",
            "--lanes",
            "unity-vendor",
            "--refresh-matrix",
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )

    assert rc == 0
    assert json_out.is_file()
    assert md_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["selected_lanes"] == ["unity-vendor"]
    assert payload["lanes"][-1]["id"] == "matrix-refresh"
    unity = payload["lanes"][0]
    assert unity["tasks"][0]["commands"][0]["command"].endswith("tools/unity_vendor_workflow.py prepare-source --vendor cesium-unity --plugin-root external/cesium/cesium-unity")
