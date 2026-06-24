#!/usr/bin/env python3
"""Generate an honest Unreal Fab readiness report."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from artifacts import REPORTS_DIR
import release_metadata


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "examples" / "unreal" / "FastDis"


SOURCE_READY_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("plugin_descriptor", "FastDis.uplugin", "Plugin descriptor is present."),
    ("build_script", "Source/FastDisUnreal/FastDisUnreal.Build.cs", "Runtime module build rules are present."),
    ("live_udp_receiver", "Source/FastDisUnreal/Public/FastDisUdpReceiverComponent.h", "Live UDP receive component is present."),
    ("live_udp_sender", "Source/FastDisUnreal/Public/FastDisUdpSenderComponent.h", "Live UDP send component is present."),
    ("pdu_events", "Source/FastDisUnreal/Public/FastDisPduEvents.h", "Blueprint PDU event component is present."),
    ("pdu_debug_markers", "Source/FastDisUnreal/Public/FastDisPduDebugMarkerComponent.h", "Source-backed Fire/Detonation/Designator debug marker component is present."),
    ("entity_manager", "Source/FastDisUnreal/Public/FastDisEntityManagerComponent.h", "Auto-spawn entity manager is present."),
    ("entity_mapping", "Source/FastDisUnreal/Public/FastDisEntityMappingDataAsset.h", "Entity Type mapping data asset class is present."),
    ("demo_controller", "Source/FastDisUnreal/Public/FastDisDemoController.h", "Placeable demo controller is present."),
    ("runtime_monitor", "Source/FastDisUnreal/Public/FastDisRuntimeMonitorComponent.h", "Runtime monitor component is present."),
    ("runtime_status_widget", "Source/FastDisUnreal/Public/FastDisRuntimeStatusWidget.h", "Code-backed UMG status widget is present."),
    ("georeference_adapter", "Source/FastDisUnreal/Public/FastDisGeoreferenceAdapterComponent.h", "Optional georeference adapter is present."),
    (
        "demo_source_shell_automation",
        "examples/unreal/FastDisOrientationVerification/Source/FastDisOrientationTests/Private/FastDisFabShell.spec.cpp",
        "Automation test proves the source-backed demo controller/widget/georeference shell.",
    ),
    (
        "fab_asset_worklist",
        "docs/UNREAL_FAB_ASSET_WORKLIST.md",
        "Authoring and maintenance checklist for Fab demo assets and captures is present.",
    ),
    (
        "fab_demo_asset_generator",
        "tools/create_unreal_fab_demo_assets.py",
        "Host runner for generating the source-backed Unreal Fab demo map is present.",
    ),
    (
        "fab_demo_asset_generator_script",
        "tools/unreal/create_fab_demo_assets.py",
        "Unreal Editor Python script for creating the demo map shell is present.",
    ),
    (
        "fab_asset_helper_library",
        "Source/FastDisUnreal/Public/FastDisFabAssetLibrary.h",
        "Editor-safe helper for generating source-backed Fab demo assets is present.",
    ),
    (
        "fab_screenshot_capture_tool",
        "tools/capture_unreal_fab_screenshots.py",
        "Host runner for capturing real Unreal Fab demo screenshots is present.",
    ),
    (
        "fab_screenshot_capture_script",
        "tools/unreal/capture_fab_demo_screenshots.py",
        "Unreal Editor Python script for capturing Fab demo screenshots is present.",
    ),
    ("five_minute_setup", "Docs/FIVE_MINUTE_SETUP.md", "Five-minute setup doc is present."),
    ("fab_draft", "Docs/FAB_DRAFT.md", "Conservative Fab draft copy is present."),
    ("content_placeholder", "Content/Examples/README.md", "Content-capable example placeholder is present."),
)

ASSET_PENDING_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("binary_demo_map", "Content/Examples/FastDis_Demo.umap", "Authored Unreal demo map is present when ready."),
    ("blueprint_status_widget", "Content/Examples/WBP_FastDisRuntimeStatus.uasset", "Polished Blueprint widget asset is present when ready."),
    ("demo_controller_blueprint", "Content/Examples/BP_FastDisDemoController.uasset", "Blueprint wrapper for the demo controller is present when ready."),
    ("entity_mapping_asset", "Content/Examples/DA_FastDisEntityMappings.uasset", "Example Entity Type mapping data asset is present when ready."),
    ("fab_screenshot_live_udp", "Content/Examples/Screenshots/live_udp_status.png", "Real live UDP screenshot export is present when ready."),
    ("fab_screenshot_entity_spawn", "Content/Examples/Screenshots/entity_spawn.png", "Real entity spawn screenshot export is present when ready."),
    ("fab_screenshot_event_marker", "Content/Examples/Screenshots/pdu_event_marker.png", "Real event marker screenshot export is present when ready."),
    ("fab_screenshot_setup_view", "Content/Examples/Screenshots/setup_view.png", "Real setup/georeference screenshot export is present when ready."),
)

VISUAL_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("generic_storefront_hero", "media/storefront/fab/01_hero_1920x1080.svg", "Generic storefront hero source exists."),
    ("unreal_grill_parity_visual", "media/storefront/fab/07_unreal_grill_parity_1920x1080.svg", "Unreal parity visual source exists."),
    ("storefront_visuals_doc", "docs/STOREFRONT_VISUALS.md", "Storefront visuals doc exists."),
)


def _plugin_descriptor_path() -> Path:
    return PLUGIN / "FastDis.uplugin"


def _expected_plugin_version_name() -> str:
    return release_metadata.plugin_version_name_from_python_version(release_metadata.project_version(ROOT))


def _expected_plugin_version_number() -> int:
    return release_metadata.plugin_version_number_from_python_version(release_metadata.project_version(ROOT))


def _load_plugin_descriptor() -> tuple[dict[str, Any] | None, str | None]:
    descriptor = _plugin_descriptor_path()
    if not descriptor.exists():
        return None, "Plugin descriptor is missing."
    try:
        return json.loads(descriptor.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"Plugin descriptor is not valid JSON: {exc}"


def _row(name: str, rel_path: str, detail: str, *, required: bool, pending_ok: bool = False) -> dict[str, Any]:
    path = ROOT / rel_path if rel_path.startswith(("docs/", "media/", "examples/", "tools/")) else PLUGIN / rel_path
    exists = path.exists()
    if exists:
        status = "ready"
    elif pending_ok:
        status = "asset_pending"
    else:
        status = "missing"
    return {
        "name": name,
        "path": rel_path,
        "status": status,
        "required": required,
        "detail": detail,
    }


def _metadata_row(
    name: str,
    *,
    detail: str,
    ok: bool,
    actual: Any,
    expected: Any,
    required: bool = True,
) -> dict[str, Any]:
    status = "ready" if ok else "missing"
    return {
        "name": name,
        "path": "FastDis.uplugin",
        "status": status,
        "required": required,
        "detail": detail,
        "actual": actual,
        "expected": expected,
    }


def build_report() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    rows.extend(_row(name, path, detail, required=True) for name, path, detail in SOURCE_READY_CHECKS)
    rows.extend(_row(name, path, detail, required=False, pending_ok=True) for name, path, detail in ASSET_PENDING_CHECKS)
    rows.extend(_row(name, path, detail, required=True) for name, path, detail in VISUAL_CHECKS)
    descriptor, descriptor_error = _load_plugin_descriptor()
    expected_version_name = _expected_plugin_version_name()
    expected_version_number = _expected_plugin_version_number()
    if descriptor is None:
        rows.append(
            _metadata_row(
                "plugin_descriptor_version_name",
                detail=descriptor_error or "Plugin descriptor version metadata must match the release version.",
                ok=False,
                actual=None,
                expected=expected_version_name,
            )
        )
        rows.append(
            _metadata_row(
                "plugin_descriptor_version_number",
                detail=descriptor_error or "Plugin descriptor integer version must track the current alpha release.",
                ok=False,
                actual=None,
                expected=expected_version_number,
            )
        )
    else:
        actual_version_name = descriptor.get("VersionName")
        actual_version_number = descriptor.get("Version")
        rows.append(
            _metadata_row(
                "plugin_descriptor_version_name",
                detail="Plugin descriptor VersionName matches the current release version.",
                ok=actual_version_name == expected_version_name,
                actual=actual_version_name,
                expected=expected_version_name,
            )
        )
        rows.append(
            _metadata_row(
                "plugin_descriptor_version_number",
                detail="Plugin descriptor integer Version tracks the current alpha release.",
                ok=actual_version_number == expected_version_number,
                actual=actual_version_number,
                expected=expected_version_number,
            )
        )

    missing_required = [row for row in rows if row["required"] and row["status"] != "ready"]
    asset_pending = [row for row in rows if row["status"] == "asset_pending"]
    overall = "missing_required" if missing_required else ("source_ready_asset_pending" if asset_pending else "fab_ready")
    return {
        "schema": "fastdis.unreal_fab_readiness.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": overall,
        "summary": {
            "rows": len(rows),
            "ready": sum(1 for row in rows if row["status"] == "ready"),
            "asset_pending": len(asset_pending),
            "missing_required": len(missing_required),
        },
        "rows": rows,
        "interpretation": (
            "source_ready_asset_pending means the code/docs/package shell are present, "
            "but authored Unreal binary assets or real screenshots are still pending; "
            "fab_ready means the source shell and authored evidence assets are present."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Unreal Fab Readiness",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- ready: `{summary['ready']}`",
        f"- asset_pending: `{summary['asset_pending']}`",
        f"- missing_required: `{summary['missing_required']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Required | Path | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        detail = row["detail"]
        if "expected" in row or "actual" in row:
            detail = f"{detail} expected=`{row.get('expected')}` actual=`{row.get('actual')}`"
        lines.append(f"| {row['name']} | `{row['status']}` | `{row['required']}` | `{row['path']}` | {detail} |")
    lines.extend(["", "## Interpretation", "", str(report["interpretation"]), ""])
    return "\n".join(lines)


def write_report(out_dir: Path) -> dict[str, Path]:
    report = build_report()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "unreal_fab_readiness.json"
    md_path = out_dir / "unreal_fab_readiness.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--strict", action="store_true", help="Return nonzero while authored Fab assets are still pending.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = write_report(args.out_dir)
    report = json.loads(paths["json"].read_text(encoding="utf-8"))
    print(f"JSON: {paths['json']}")
    print(f"Markdown: {paths['markdown']}")
    print(f"overall_status: {report['overall_status']}")
    if report["overall_status"] == "missing_required":
        return 1
    if args.strict and report["overall_status"] != "fab_ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
