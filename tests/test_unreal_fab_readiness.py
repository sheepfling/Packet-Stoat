from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_unreal_fab_readiness


def test_unreal_fab_readiness_reports_current_fab_status() -> None:
    report = check_unreal_fab_readiness.build_report()

    assert report["schema"] == "fastdis.unreal_fab_readiness.v1"
    assert report["overall_status"] == "fab_ready"
    assert report["summary"]["missing_required"] == 0
    assert report["summary"]["asset_pending"] == 0


def test_unreal_fab_readiness_tracks_required_source_shell() -> None:
    rows = {row["name"]: row for row in check_unreal_fab_readiness.build_report()["rows"]}

    for name in [
        "live_udp_receiver",
        "live_udp_sender",
        "pdu_events",
        "pdu_debug_markers",
        "entity_manager",
        "demo_controller",
        "runtime_status_widget",
        "georeference_adapter",
        "demo_source_shell_automation",
        "fab_asset_worklist",
        "fab_demo_asset_generator",
        "fab_demo_asset_generator_script",
        "fab_asset_helper_library",
        "fab_screenshot_capture_tool",
        "fab_screenshot_capture_script",
        "fab_draft",
        "unreal_grill_parity_visual",
    ]:
        assert rows[name]["status"] == "ready"
        assert rows[name]["required"] is True

    assert rows["binary_demo_map"]["status"] == "ready"
    assert rows["binary_demo_map"]["required"] is False
    assert rows["entity_mapping_asset"]["status"] == "ready"
    assert rows["entity_mapping_asset"]["required"] is False
    assert rows["blueprint_status_widget"]["status"] == "ready"
    assert rows["blueprint_status_widget"]["required"] is False
    assert rows["demo_controller_blueprint"]["status"] == "ready"
    assert rows["demo_controller_blueprint"]["required"] is False

    for name in [
        "fab_screenshot_live_udp",
        "fab_screenshot_entity_spawn",
        "fab_screenshot_event_marker",
        "fab_screenshot_setup_view",
    ]:
        assert rows[name]["status"] == "ready"
        assert rows[name]["required"] is False


def test_unreal_fab_readiness_writes_json_and_markdown(tmp_path: Path) -> None:
    paths = check_unreal_fab_readiness.write_report(tmp_path)

    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    markdown = paths["markdown"].read_text(encoding="utf-8")

    assert payload["overall_status"] == "fab_ready"
    assert "# Unreal Fab Readiness" in markdown
    assert "binary_demo_map" in markdown
    assert "fab_asset_worklist" in markdown
    assert "source_ready_asset_pending means" in markdown
    assert "fab_ready means" in markdown
