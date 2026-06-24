#!/usr/bin/env python3
"""Generate the Epic 2 cross-engine/Lattice parity report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CROSS_LANGUAGE = ROOT / "docs" / "message_cross_language_set.json"
ENDPOINT_MAPPING = ROOT / "generated" / "endpoint_mapping_manifest.json"
LOGGING_CATALOG = ROOT / "generated" / "pdu_log_catalog.json"
LATTICE_MAPPING = ROOT / "generated" / "lattice_dis_mapping_plan.json"
JSON_OUT = ROOT / "generated" / "epic2_parity_report.json"
MD_OUT = ROOT / "docs" / "EPIC2_PARITY.md"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _index(rows: list[dict[str, Any]], version_key: str = "protocol_version", type_key: str = "pdu_type") -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(row[version_key]), int(row[type_key])): row for row in rows}


def build_report() -> dict[str, Any]:
    cross = _load(CROSS_LANGUAGE)
    endpoint = _load(ENDPOINT_MAPPING)
    logging = _load(LOGGING_CATALOG)
    lattice = _load(LATTICE_MAPPING)

    endpoint_by_key = _index(endpoint["records"])
    logging_by_key = _index(logging["rows"], version_key="version")
    lattice_by_key = _index(lattice["records"])

    records: list[dict[str, Any]] = []
    for row in cross["records"]:
        key = (int(row["protocol_version"]), int(row["pdu_type"]))
        endpoint_row = endpoint_by_key[key]
        logging_row = logging_by_key[key]
        lattice_row = lattice_by_key[key]
        deep_surfaces = {
            "c": bool(row["c_body_decoder"]),
            "cpp": bool(row["cpp_body_decoder"]),
            "python": bool(row["python_body_decoder"]),
            "unreal": bool(row["unreal_adapter"]),
            "godot": bool(row["godot_adapter"]),
            "unity": bool(row["unity_adapter"]),
        }
        catalog_surfaces = {
            "c": bool(row["c_catalog"]),
            "cpp": bool(row["cpp_catalog"]),
            "python": bool(row["python_catalog"]),
            "unreal": bool(row["unreal_catalog"]),
            "godot": bool(row["godot_catalog"]),
            "unity": bool(row["unity_catalog"]),
        }
        all_catalog = all(catalog_surfaces.values())
        all_deep = all(deep_surfaces.values())
        records.append(
            {
                "protocol_version": int(row["protocol_version"]),
                "pdu_type": int(row["pdu_type"]),
                "name": str(row["name"]),
                "family_name": str(row["family_name"]),
                "catalog_surfaces": catalog_surfaces,
                "deep_surfaces": deep_surfaces,
                "all_catalog_surfaces": all_catalog,
                "all_deep_surfaces": all_deep,
                "endpoint_support_level": str(endpoint_row["support_level"]),
                "logging_support_level": str(logging_row["support_level"]),
                "lattice_bucket": str(lattice_row["strict_lattice_bucket"]),
                "lattice_lossy_mode_class": str(lattice_row["lossy_mode_class"]),
                "lattice_proof_depth": str(lattice_row["proof_depth"]),
            }
        )

    records.sort(key=lambda item: (item["protocol_version"], item["pdu_type"]))
    deep_rows = [row for row in records if any(row["deep_surfaces"].values())]
    representative_keys = {(6, 1), (6, 67), (7, 1), (7, 67)}
    representative_rows = [row for row in records if (row["protocol_version"], row["pdu_type"]) in representative_keys]

    surface_catalog_counts = {
        surface: sum(1 for row in records if row["catalog_surfaces"][surface])
        for surface in ("c", "cpp", "python", "unreal", "godot", "unity")
    }
    surface_deep_counts = {
        surface: sum(1 for row in records if row["deep_surfaces"][surface])
        for surface in ("c", "cpp", "python", "unreal", "godot", "unity")
    }

    return {
        "schema": "fastdis.epic2.parity_report.v1",
        "generated_from": [
            display_path(CROSS_LANGUAGE),
            display_path(ENDPOINT_MAPPING),
            display_path(LOGGING_CATALOG),
            display_path(LATTICE_MAPPING),
        ],
        "policy": {
            "catalog": "A surface can identify the row through generated descriptors or metadata.",
            "deep": "A surface has a proved typed body decoder or engine/runtime adapter path for that row.",
            "lattice": "Lattice/Zorn parity is classified by strict bucket and lossy mode rather than implied by parser depth.",
        },
        "summary": {
            "records": len(records),
            "all_catalog_surfaces_rows": sum(1 for row in records if row["all_catalog_surfaces"]),
            "all_deep_surfaces_rows": sum(1 for row in records if row["all_deep_surfaces"]),
            "surface_catalog_counts": surface_catalog_counts,
            "surface_deep_counts": surface_deep_counts,
            "representative_typed_rows": len(representative_rows),
            "lattice_direct_rows": sum(1 for row in lattice["records"] if row["surface_confidence"] == "direct"),
            "lattice_projected_rows": sum(1 for row in lattice["records"] if row["surface_confidence"] == "projected"),
        },
        "representative_rows": representative_rows,
        "records": records,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Epic 2 Parity Report",
        "",
        "This generated report keeps the current cross-engine/Lattice parity claim honest.",
        "",
        "## Summary",
        "",
        f"- records: `{report['summary']['records']}`",
        f"- rows with catalog visibility on all tracked surfaces: `{report['summary']['all_catalog_surfaces_rows']}`",
        f"- rows with deep/runtime support on all tracked surfaces: `{report['summary']['all_deep_surfaces_rows']}`",
        f"- surface catalog counts: `{json.dumps(report['summary']['surface_catalog_counts'], sort_keys=True)}`",
        f"- surface deep/runtime counts: `{json.dumps(report['summary']['surface_deep_counts'], sort_keys=True)}`",
        f"- lattice direct rows: `{report['summary']['lattice_direct_rows']}`",
        f"- lattice projected rows: `{report['summary']['lattice_projected_rows']}`",
        "",
        "Current honest state: catalog visibility is broad, but deep/runtime support is still concentrated in Entity State and Entity State Update. Unity currently has generated catalog visibility for all rows and runtime/deep support for none.",
        "",
        "## Representative Typed Rows",
        "",
        "| DIS | PDU | Name | Catalog surfaces | Deep/runtime surfaces | Lattice bucket | Lattice mode |",
        "| ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in report["representative_rows"]:
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['name']} | "
            f"`{json.dumps(row['catalog_surfaces'], sort_keys=True)}` | "
            f"`{json.dumps(row['deep_surfaces'], sort_keys=True)}` | "
            f"{row['lattice_bucket']} | {row['lattice_lossy_mode_class']} |"
        )
    lines.extend(
        [
            "",
            "## Deep/Runtime Rows",
            "",
            "| DIS | PDU | Name | C | C++ | Python | Unreal | Godot | Unity |",
            "| ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in [item for item in report["records"] if any(item["deep_surfaces"].values())]:
        deep = row["deep_surfaces"]
        lines.append(
            f"| {row['protocol_version']} | {row['pdu_type']} | {row['name']} | "
            f"{'yes' if deep['c'] else 'no'} | {'yes' if deep['cpp'] else 'no'} | {'yes' if deep['python'] else 'no'} | "
            f"{'yes' if deep['unreal'] else 'no'} | {'yes' if deep['godot'] else 'no'} | {'yes' if deep['unity'] else 'no'} |"
        )
    lines.append("")
    return "\n".join(lines)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def outputs() -> dict[Path, str]:
    report = build_report()
    return {
        JSON_OUT: json.dumps(report, indent=2, sort_keys=True) + "\n",
        MD_OUT: render_markdown(report) + "\n",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered = outputs()
    if args.check:
        stale: list[Path] = []
        for path, content in rendered.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("stale Epic 2 parity artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {display_path(path)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("generated Epic 2 parity report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
