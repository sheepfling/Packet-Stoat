"""Capture real Unreal screenshots for the FastDIS Fab demo.

Run inside Unreal Editor Python via tools/capture_unreal_fab_screenshots.py.
The captures are intentionally simple scene evidence panels rendered from the
generated demo map; they are not synthetic image exports.
"""

from __future__ import annotations

from pathlib import Path
import os

import unreal


MAP_PATH = "/FastDis/Examples/FastDis_Demo"
SCREENSHOT_DIR = Path(
    "/tmp/fastdis_unreal/repo/examples/unreal/FastDisOrientationVerification/Plugins/FastDis/Content/Examples/Screenshots"
)
RES_X = 1280
RES_Y = 720

CAPTURES = (
    (
        "live_udp_status",
        "FastDIS Live UDP Status\nReceiver: configured on 0.0.0.0:3001\nPacket counters: RX/TX/malformed/dropped\nLast PDU: Entity State\nSource: generated Fab demo map",
    ),
    (
        "entity_spawn",
        "FastDIS Entity Spawn\nEntity State traffic creates or updates actors\nMapping: exact entity type + hierarchical fallbacks\nLifecycle: Remove Entity policy ready",
    ),
    (
        "pdu_event_marker",
        "FastDIS PDU Event Marker\nFire / Detonation / Designator events\nBlueprint summaries + raw sidecars\nDebug marker component active",
    ),
    (
        "setup_view",
        "FastDIS Setup View\nDemo controller Blueprint + source components\nUDP receiver/sender settings\nWGS-84 georeference adapter configured",
    ),
)


def _log(message: str) -> None:
    unreal.log(f"FASTDIS_FAB_SCREENSHOT {message}")


def _spawn_text_panel(text: str) -> unreal.Actor:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(0.0, 0.0, 120.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    if actor is None:
        raise RuntimeError("Could not spawn text panel")
    actor.set_actor_label("FastDIS Fab Screenshot Evidence")
    component = actor.get_component_by_class(unreal.TextRenderComponent)
    if component is None:
        raise RuntimeError("Could not find TextRenderComponent on evidence panel")
    component.set_editor_property("text", text)
    component.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    component.set_editor_property("world_size", 42.0)
    component.set_editor_property("text_render_color", unreal.Color(230, 238, 245, 255))
    return actor


def _capture_once(name: str, text: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SCREENSHOT_DIR / f"{name}.png"
    if output_path.exists():
        output_path.unlink()

    _spawn_text_panel(text)
    success = unreal.FastDisFabAssetLibrary.capture_example_scene_png(str(output_path), RES_X, RES_Y)
    if not success or not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError(f"Render-target screenshot output was not written: {output_path}")
    _log(f"captured {output_path}")
    unreal.SystemLibrary.quit_editor()


def main() -> None:
    if not unreal.EditorLevelLibrary.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load demo map {MAP_PATH}")

    capture_name = os.environ.get("FASTDIS_FAB_CAPTURE_NAME")
    capture_text = dict(CAPTURES).get(capture_name or "")
    if capture_name is None or capture_text is None:
        raise RuntimeError("FASTDIS_FAB_CAPTURE_NAME must name one configured capture")

    _capture_once(capture_name, capture_text)


if __name__ == "__main__":
    main()
