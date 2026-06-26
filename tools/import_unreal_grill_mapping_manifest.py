#!/usr/bin/env python3
"""Import a GRILL Unreal mapping manifest into a FastDIS-ready intermediate manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENUM_KEYS = ("kind", "domain", "country", "category", "subcategory", "specific", "extra")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Exported GRILL Unreal mapping manifest JSON")
    parser.add_argument("--fastdis-out", type=Path, default=ROOT / "build" / "reports" / "unreal_grill_swap" / "fastdis_mapping_manifest.json")
    parser.add_argument("--json-out", type=Path, default=ROOT / "build" / "reports" / "unreal_grill_swap" / "grill_mapping_import_report.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "build" / "reports" / "unreal_grill_swap" / "grill_mapping_import_report.md")
    parser.add_argument("--source-route", default="AF-GRILL/DISPluginForUnreal@ue5")
    parser.add_argument(
        "--search-root",
        dest="search_roots",
        action="append",
        type=Path,
        help="Host project or plugin root to validate imported actor-class paths against. May be repeated.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_enum(raw: dict[str, object], *, row_index: int, enum_index: int, errors: list[str]) -> dict[str, int] | None:
    normalized: dict[str, int] = {}
    for key in REQUIRED_ENUM_KEYS:
        value = raw.get(key)
        if not isinstance(value, int):
            errors.append(f"row {row_index} enumeration {enum_index} field `{key}` must be an integer")
            return None
        normalized[key] = value
    return normalized


def _specificity(entity_type: dict[str, int]) -> int:
    return sum(1 for key in REQUIRED_ENUM_KEYS if entity_type[key] >= 0)


def _enum_key(entity_type: dict[str, int]) -> tuple[int, ...]:
    return tuple(entity_type[key] for key in REQUIRED_ENUM_KEYS)


def _enum_to_fastdis(entity_type: dict[str, int]) -> dict[str, int]:
    return {
        "Kind": entity_type["kind"],
        "Domain": entity_type["domain"],
        "Country": entity_type["country"],
        "Category": entity_type["category"],
        "Subcategory": entity_type["subcategory"],
        "Specific": entity_type["specific"],
        "Extra": entity_type["extra"],
    }


def _candidate_asset_files(actor_class_path: str, search_root: Path) -> list[Path]:
    object_path = actor_class_path.strip()
    if not object_path.startswith("/"):
        return []

    package_path = object_path.split(":", 1)[0]
    if "." in package_path:
        package_path = package_path.split(".", 1)[0]
    segments = [segment for segment in package_path.split("/") if segment]
    if not segments:
        return []

    mount = segments[0]
    relative_segments = segments[1:]
    if not relative_segments:
        return []
    asset_file = relative_segments[-1] + ".uasset"
    relative_path = Path(*relative_segments[:-1]) / asset_file if len(relative_segments) > 1 else Path(asset_file)

    candidates: list[Path] = []
    if mount == "Game":
        candidates.append(search_root / "Content" / relative_path)
    else:
        candidates.append(search_root / "Plugins" / mount / "Content" / relative_path)
        if (search_root / "Content").exists():
            candidates.append(search_root / "Content" / relative_path)
    return candidates


def _resolve_actor_class(actor_class_path: str, search_roots: list[Path]) -> dict[str, object]:
    checked_paths: list[str] = []
    for root in search_roots:
        for candidate in _candidate_asset_files(actor_class_path, root):
            checked_paths.append(str(candidate))
            if candidate.exists():
                return {
                    "status": "resolved",
                    "resolved_path": str(candidate),
                    "checked_paths": checked_paths,
                }
    return {
        "status": "unresolved",
        "resolved_path": None,
        "checked_paths": checked_paths,
    }


def _markdown_report(report: dict[str, object]) -> str:
    lines = [
        "# Unreal GRILL Mapping Import",
        "",
        f"- status: `{report['status']}`",
        f"- source_route: `{report['source_route']}`",
        f"- input_manifest: `{report['input_manifest']}`",
        f"- imported_rows: `{report['imported_rows']}`",
        f"- imported_enumerations: `{report['imported_enumerations']}`",
        f"- wildcard_enumerations: `{report['wildcard_enumerations']}`",
        f"- duplicate_exact_enumerations: `{report['duplicate_exact_enumerations']}`",
        f"- duplicate_wildcard_enumerations: `{report['duplicate_wildcard_enumerations']}`",
        f"- resolved_actor_classes: `{report['resolved_actor_classes']}`",
        f"- unresolved_actor_classes: `{report['unresolved_actor_classes']}`",
        "",
        "## Notes",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Imported Rows"])
    for row in report["rows"]:
        lines.append(
            f"- `{row['friendly_name']}` -> `{row['actor_class']}` "
            f"(primary specificity `{row['primary_specificity']}`, aliases `{row['alias_count']}`, priority `{row['priority']}`, actor `{row['actor_resolution_status']}`)"
        )
    return "\n".join(lines) + "\n"


def import_manifest(
    payload: dict[str, object],
    *,
    source_route: str,
    input_manifest: str,
    search_roots: list[Path] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    errors: list[str] = []
    normalized_search_roots = [root.resolve() for root in (search_roots or [])]
    if payload.get("product") != "GRILL DIS for Unreal":
        errors.append("`product` must equal `GRILL DIS for Unreal`")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        errors.append("`rows` must be a list")
    if errors:
        raise ValueError("; ".join(errors))

    imported_rows: list[dict[str, object]] = []
    report_rows: list[dict[str, object]] = []
    exact_seen: dict[tuple[int, ...], dict[str, object]] = {}
    wildcard_seen: dict[tuple[int, ...], dict[str, object]] = {}
    imported_enumerations = 0
    wildcard_enumerations = 0
    duplicate_exact = 0
    duplicate_wildcard = 0
    resolved_actor_classes = 0
    unresolved_actor_classes = 0

    for row_index, raw_row in enumerate(rows):
        if not isinstance(raw_row, dict):
            errors.append(f"row {row_index} must be an object")
            continue
        friendly_name = raw_row.get("friendly_name")
        actor_class = raw_row.get("dis_entity")
        enum_rows = raw_row.get("associated_dis_enumerations")
        if not isinstance(friendly_name, str) or not friendly_name.strip():
            errors.append(f"row {row_index} `friendly_name` must be a non-empty string")
            continue
        if not isinstance(actor_class, str) or not actor_class.strip():
            errors.append(f"row {row_index} `dis_entity` must be a non-empty string")
            continue
        if not isinstance(enum_rows, list) or not enum_rows:
            errors.append(f"row {row_index} `associated_dis_enumerations` must be a non-empty list")
            continue

        normalized_enums: list[dict[str, int]] = []
        for enum_index, raw_enum in enumerate(enum_rows):
            if not isinstance(raw_enum, dict):
                errors.append(f"row {row_index} enumeration {enum_index} must be an object")
                continue
            normalized = _normalize_enum(raw_enum, row_index=row_index, enum_index=enum_index, errors=errors)
            if normalized is None:
                continue
            normalized_enums.append(normalized)
            imported_enumerations += 1
            is_wildcard = any(normalized[key] < 0 for key in REQUIRED_ENUM_KEYS)
            target_seen = wildcard_seen if is_wildcard else exact_seen
            enum_key = _enum_key(normalized)
            if is_wildcard:
                wildcard_enumerations += 1
            if enum_key in target_seen:
                if is_wildcard:
                    duplicate_wildcard += 1
                else:
                    duplicate_exact += 1
            target_seen[enum_key] = {"row_index": row_index, "friendly_name": friendly_name, "actor_class": actor_class}

        if not normalized_enums:
            continue

        # FastDIS priorities preserve GRILL's later-row duplicate override behavior.
        priority = row_index + 1
        sorted_enums = sorted(normalized_enums, key=lambda item: (-_specificity(item), _enum_key(item)))
        primary = sorted_enums[0]
        aliases = sorted_enums[1:]
        actor_resolution = _resolve_actor_class(actor_class, normalized_search_roots) if normalized_search_roots else {
            "status": "not_checked",
            "resolved_path": None,
            "checked_paths": [],
        }
        if actor_resolution["status"] == "resolved":
            resolved_actor_classes += 1
        elif actor_resolution["status"] == "unresolved":
            unresolved_actor_classes += 1
        imported_rows.append(
            {
                "DisplayName": friendly_name,
                "ActorClassPath": actor_class,
                "ActorClassSoftPath": actor_class,
                "Priority": priority,
                "EntityType": _enum_to_fastdis(primary),
                "AliasEntityTypes": [_enum_to_fastdis(alias) for alias in aliases],
                "SourceRowIndex": row_index,
                "SourceRouteLabel": source_route,
                "SourceActorClassPath": actor_class,
                "ActorResolution": actor_resolution,
            }
        )
        report_rows.append(
            {
                "friendly_name": friendly_name,
                "actor_class": actor_class,
                "priority": priority,
                "primary_specificity": _specificity(primary),
                "alias_count": len(aliases),
                "source_row_index": row_index,
                "actor_resolution_status": actor_resolution["status"],
                "resolved_path": actor_resolution["resolved_path"],
            }
        )

    if errors:
        raise ValueError("; ".join(errors))

    notes: list[str] = []
    if duplicate_exact:
        notes.append("Exact duplicate enumerations were present; FastDIS row priorities preserve GRILL's later-row override behavior.")
    if duplicate_wildcard:
        notes.append("Wildcard duplicate enumerations were present; FastDIS row priorities preserve GRILL's later-row override behavior.")
    if wildcard_enumerations:
        notes.append("Wildcard enumerations were imported using negative enum fields, matching FastDIS wildcard semantics.")
    if normalized_search_roots:
        notes.append("Actor-class validation was performed against the supplied search roots.")
    else:
        notes.append("Actor-class validation was not run because no search roots were supplied.")
    notes.append("This tool imports an exported GRILL manifest, not the raw Unreal `.uasset`; keep the source export with the benchmark evidence.")

    fastdis_manifest = {
        "product": "FastDIS Unreal Mapping Import",
        "source_product": "GRILL DIS for Unreal",
        "source_route": source_route,
        "input_manifest": input_manifest,
        "search_roots": [str(root) for root in normalized_search_roots],
        "rows": imported_rows,
    }
    report = {
        "status": "ok",
        "source_route": source_route,
        "input_manifest": input_manifest,
        "search_roots": [str(root) for root in normalized_search_roots],
        "imported_rows": len(imported_rows),
        "imported_enumerations": imported_enumerations,
        "wildcard_enumerations": wildcard_enumerations,
        "duplicate_exact_enumerations": duplicate_exact,
        "duplicate_wildcard_enumerations": duplicate_wildcard,
        "resolved_actor_classes": resolved_actor_classes,
        "unresolved_actor_classes": unresolved_actor_classes,
        "rows": report_rows,
        "notes": notes,
    }
    return fastdis_manifest, report


def main() -> int:
    args = parse_args()
    payload = _read_json(args.input)
    try:
        fastdis_manifest, report = import_manifest(
            payload,
            source_route=args.source_route,
            input_manifest=str(args.input),
            search_roots=args.search_roots,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    args.fastdis_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.fastdis_out.write_text(json.dumps(fastdis_manifest, indent=2) + "\n", encoding="utf-8")
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(_markdown_report(report), encoding="utf-8")
    print(f"wrote {args.fastdis_out}")
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
