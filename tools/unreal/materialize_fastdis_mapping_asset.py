"""Materialize a FastDIS enumeration mapping asset from imported JSON.

Run inside Unreal Editor Python via tools/run_unreal_grill_mapping_materialize.py.
"""

from __future__ import annotations

import json
import os

import unreal


SUCCESS_MARKER = "FASTDIS_GRILL_MAPPING_MATERIALIZE complete"
DEFAULT_ASSET_PATH = "/Game/FastDis/DA_ImportedGRILLMappings"


def _log(message: str) -> None:
    unreal.log(f"FASTDIS_GRILL_MAPPING_MATERIALIZE {message}")


def _write_result(path: str, payload: dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> None:
    asset_path = os.environ.get("FASTDIS_FASTDIS_MAPPING_ASSET_PATH", DEFAULT_ASSET_PATH)
    manifest_path = os.environ.get("FASTDIS_FASTDIS_MAPPING_JSON")
    result_path = os.environ.get("FASTDIS_FASTDIS_MAPPING_RESULT_JSON")
    if not manifest_path:
        raise RuntimeError("FASTDIS_FASTDIS_MAPPING_JSON is not set")
    if not result_path:
        raise RuntimeError("FASTDIS_FASTDIS_MAPPING_RESULT_JSON is not set")

    if not unreal.FastDisFabAssetLibrary.create_enumeration_mapping_asset_from_json(asset_path, manifest_path):
        raise RuntimeError(f"Could not create FastDIS enumeration mapping asset {asset_path} from {manifest_path}")

    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        raise RuntimeError(f"FastDIS enumeration mapping asset {asset_path} was not created")

    asset = unreal.load_asset(asset_path)
    rows = asset.get_editor_property("rows") if asset else []
    payload = {
        "status": "ok",
        "asset_path": asset_path,
        "manifest_path": manifest_path,
        "row_count": len(rows),
        "source_manifest_path": asset.get_editor_property("source_manifest_path") if asset else "",
    }
    _write_result(result_path, payload)
    _log("complete")
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
