"""Create source-backed FastDIS Unreal Fab demo assets.

Run inside Unreal Editor Python via tools/create_unreal_fab_demo_assets.py.
The first generated asset is the demo map shell; authored Blueprint polish can
build on top of this instead of starting from an empty level.
"""

from __future__ import annotations

import unreal


MAP_PATH = "/FastDis/Examples/FastDis_Demo"
MAPPING_ASSET_PATH = "/FastDis/Examples/DA_FastDisEntityMappings"
DEMO_CONTROLLER_BLUEPRINT_NAME = "BP_FastDisDemoController"
STATUS_WIDGET_BLUEPRINT_NAME = "WBP_FastDisRuntimeStatus"
EXAMPLES_PACKAGE_PATH = "/FastDis/Examples"
DEMO_CONTROLLER_CLASS = "/Script/FastDisUnreal.FastDisDemoController"
STATUS_WIDGET_CLASS = "/Script/FastDisUnreal.FastDisRuntimeStatusWidget"


def _log(message: str) -> None:
    unreal.log(f"FASTDIS_FAB_ASSET_GEN {message}")


def _load_class(path: str) -> type:
    cls = unreal.load_class(None, path)
    if cls is None:
        raise RuntimeError(f"Could not load Unreal class {path}")
    return cls


def _set_first_property(obj: object, names: tuple[str, ...], value: object) -> None:
    last_error: Exception | None = None
    for name in names:
        try:
            obj.set_editor_property(name, value)
            return
        except Exception as exc:  # Unreal raises generic Exception for missing reflected properties.
            last_error = exc
    raise RuntimeError(f"Could not set any of {names} on {obj}: {last_error}")


def _configure_demo_controller(actor: unreal.Actor) -> None:
    actor.set_actor_label("FastDIS Demo Controller")
    actor.set_actor_location(unreal.Vector(0.0, 0.0, 120.0), False, False)

    receiver = actor.get_component_by_class(unreal.load_class(None, "/Script/FastDisUnreal.FastDisUdpReceiverComponent"))
    if receiver:
        _set_first_property(receiver, ("port", "Port"), 3001)
        _set_first_property(receiver, ("bind_address", "BindAddress"), "0.0.0.0")
        _set_first_property(receiver, ("auto_start", "b_auto_start", "bAutoStart"), False)

    sender = actor.get_component_by_class(unreal.load_class(None, "/Script/FastDisUnreal.FastDisUdpSenderComponent"))
    if sender:
        _set_first_property(sender, ("remote_address", "RemoteAddress"), "127.0.0.1")
        _set_first_property(sender, ("remote_port", "RemotePort"), 3001)

    sample = actor.get_component_by_class(unreal.load_class(None, "/Script/FastDisUnreal.FastDisSampleTrafficComponent"))
    if sample:
        _set_first_property(sample, ("inject_on_begin_play", "b_inject_on_begin_play", "bInjectOnBeginPlay"), False)


def create_demo_map() -> None:
    _log(f"creating demo map {MAP_PATH}")
    if not unreal.EditorLevelLibrary.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create level {MAP_PATH}")

    demo_class = _load_class(DEMO_CONTROLLER_CLASS)
    demo_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(demo_class, unreal.Vector(0.0, 0.0, 120.0))
    if demo_actor is None:
        raise RuntimeError("Could not spawn AFastDisDemoController")
    _configure_demo_controller(demo_actor)

    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError(f"Could not save level {MAP_PATH}")
    _log(f"saved demo map {MAP_PATH}")


def create_mapping_asset() -> None:
    _log(f"creating entity mapping asset {MAPPING_ASSET_PATH}")
    library = unreal.FastDisFabAssetLibrary
    if not library.create_example_entity_mapping_asset(MAPPING_ASSET_PATH):
        raise RuntimeError(f"Could not create entity mapping asset {MAPPING_ASSET_PATH}")
    _log(f"saved entity mapping asset {MAPPING_ASSET_PATH}")


def _delete_asset_if_exists(package_path: str) -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        if not unreal.EditorAssetLibrary.delete_asset(package_path):
            raise RuntimeError(f"Could not delete stale asset {package_path}")


def create_actor_blueprint(name: str, parent_class_path: str) -> None:
    asset_path = f"{EXAMPLES_PACKAGE_PATH}/{name}"
    _log(f"creating actor Blueprint {asset_path}")
    _delete_asset_if_exists(asset_path)

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", _load_class(parent_class_path))
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(name, EXAMPLES_PACKAGE_PATH, unreal.Blueprint, factory)
    if asset is None:
        raise RuntimeError(f"Could not create Blueprint {asset_path}")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    _log(f"saved actor Blueprint {asset_path}")


def create_widget_blueprint(name: str, parent_class_path: str) -> None:
    asset_path = f"{EXAMPLES_PACKAGE_PATH}/{name}"
    _log(f"creating widget Blueprint {asset_path}")
    _delete_asset_if_exists(asset_path)

    factory = unreal.WidgetBlueprintFactory()
    factory.set_editor_property("parent_class", _load_class(parent_class_path))
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(name, EXAMPLES_PACKAGE_PATH, unreal.WidgetBlueprint, factory)
    if asset is None:
        raise RuntimeError(f"Could not create Widget Blueprint {asset_path}")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    _log(f"saved widget Blueprint {asset_path}")


def main() -> None:
    create_mapping_asset()
    create_actor_blueprint(DEMO_CONTROLLER_BLUEPRINT_NAME, DEMO_CONTROLLER_CLASS)
    create_widget_blueprint(STATUS_WIDGET_BLUEPRINT_NAME, STATUS_WIDGET_CLASS)
    create_demo_map()
    _log("complete")
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
