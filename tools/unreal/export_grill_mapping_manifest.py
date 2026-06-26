"""Export a GRILL Unreal `UDISClassEnumMappings` asset to normalized JSON.

Run inside Unreal Editor Python via tools/run_grill_unreal_mapping_export.py.
"""

from __future__ import annotations

import json
import os

import unreal


SUCCESS_MARKER = "FASTDIS_GRILL_MAPPING_EXPORT complete"
DEFAULT_ASSET_PATH = "/Game/DISEnumerationMappings"


def _log(message: str) -> None:
    unreal.log(f"FASTDIS_GRILL_MAPPING_EXPORT {message}")


def _first_prop(obj: object, *names: str) -> object:
    last_error: Exception | None = None
    for name in names:
        try:
            return obj.get_editor_property(name)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Could not read any of {names} from {obj}: {last_error}")


def _bool_as_specific(entity_type: object, use_specific_name: str, value_name: str) -> int:
    use_specific = bool(_first_prop(entity_type, use_specific_name))
    value = int(_first_prop(entity_type, value_name))
    return value if use_specific else -1


def _entity_type_to_dict(entity_type: object) -> dict[str, int]:
    return {
        "kind": _bool_as_specific(entity_type, "bUseSpecific_EntityKind", "EntityKind"),
        "domain": _bool_as_specific(entity_type, "bUseSpecific_Domain", "Domain"),
        "country": _bool_as_specific(entity_type, "bUseSpecific_Country", "Country"),
        "category": _bool_as_specific(entity_type, "bUseSpecific_Category", "Category"),
        "subcategory": _bool_as_specific(entity_type, "bUseSpecific_Subcategory", "Subcategory"),
        "specific": _bool_as_specific(entity_type, "bUseSpecific_Specific", "Specific"),
        "extra": _bool_as_specific(entity_type, "bUseSpecific_Extra", "Extra"),
    }


def _soft_class_path(value: object) -> str:
    if value is None:
        return ""
    for method_name in ("get_asset_path_string", "get_editor_property"):
        if not hasattr(value, method_name):
            continue
        try:
            if method_name == "get_editor_property":
                path = value.get_editor_property("asset_path_name")
            else:
                path = getattr(value, method_name)()
            if path:
                return str(path)
        except Exception:
            continue
    for method_name in ("get_path_name", "to_string"):
        if hasattr(value, method_name):
            try:
                path = getattr(value, method_name)()
                if path:
                    return str(path)
            except Exception:
                continue
    return str(value)


def export_mapping_asset(asset_path: str, output_path: str) -> None:
    asset = unreal.load_asset(asset_path)
    if asset is None:
        raise RuntimeError(f"Could not load GRILL mapping asset {asset_path}")

    rows = []
    for mapping_row in _first_prop(asset, "DISClassEnumArray", "dis_class_enum_array"):
        rows.append(
            {
                "friendly_name": str(_first_prop(mapping_row, "FriendlyName", "friendly_name")),
                "dis_entity": _soft_class_path(_first_prop(mapping_row, "DISEntity", "disentity")),
                "associated_dis_enumerations": [
                    _entity_type_to_dict(entity_type)
                    for entity_type in _first_prop(mapping_row, "AssociatedDISEnumerations", "associated_dis_enumerations")
                ],
            }
        )

    payload = {
        "product": "GRILL DIS for Unreal",
        "asset_path": asset_path,
        "rows": rows,
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    _log(f"wrote {output_path}")


def main() -> None:
    asset_path = os.environ.get("FASTDIS_GRILL_MAPPING_ASSET", DEFAULT_ASSET_PATH)
    output_path = os.environ.get("FASTDIS_GRILL_EXPORT_JSON")
    if not output_path:
        raise RuntimeError("FASTDIS_GRILL_EXPORT_JSON is not set")
    export_mapping_asset(asset_path, output_path)
    _log("complete")
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
