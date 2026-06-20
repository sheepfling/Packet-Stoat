#!/usr/bin/env python3
"""Build a machine-readable fastdis vs Open-DIS differential report.

This compares:

1. DIS7 catalog identity and decoder overlap against Open-DIS Python.
2. Header parsing on the raw Open-DIS fixture packets.
3. Entity State fixed-prefix fields on the Open-DIS EntityState fixture,
   where fastdis already has typed support.

Open-DIS is used as a practical independent implementation oracle, not an
authoritative standard source.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import fastdis
import fastdis.native as native


def load_open_dis(open_dis_root: Path):
    if str(open_dis_root) not in sys.path:
        sys.path.insert(0, str(open_dis_root))
    from opendis.PduFactory import PduTypeDecoders, createPdu  # type: ignore

    return PduTypeDecoders, createPdu


def maybe_git_rev(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def compare_fields(lhs: dict[str, Any], rhs: dict[str, Any], fields: list[str], *, abs_tol: float = 1e-5) -> list[str]:
    mismatches: list[str] = []
    for field in fields:
        left = lhs.get(field)
        right = rhs.get(field)
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            if len(left) != len(right):
                mismatches.append(field)
                continue
            failed = False
            for l_item, r_item in zip(left, right):
                if isinstance(l_item, float) or isinstance(r_item, float):
                    if abs(float(l_item) - float(r_item)) > abs_tol:
                        failed = True
                        break
                elif l_item != r_item:
                    failed = True
                    break
            if failed:
                mismatches.append(field)
            continue
        if isinstance(left, float) or isinstance(right, float):
            if abs(float(left) - float(right)) > abs_tol:
                mismatches.append(field)
        elif left != right:
            mismatches.append(field)
    return mismatches


def build_catalog_report(open_dis_decoders: dict[int, Any]) -> dict[str, Any]:
    fastdis_dis7 = {
        entry.pdu_type: entry
        for entry in fastdis.PDU_CATALOG
        if int(entry.protocol_version) == 7
    }
    open_dis = {int(pdu_type): decoder.__name__ for pdu_type, decoder in open_dis_decoders.items()}

    overlap: list[dict[str, Any]] = []
    name_mismatches: list[dict[str, Any]] = []
    for pdu_type in sorted(set(fastdis_dis7) & set(open_dis)):
        fast_entry = fastdis_dis7[pdu_type]
        fast_name = fast_entry.class_name
        open_name = open_dis[pdu_type]
        item = {
            "pdu_type": pdu_type,
            "fastdis_name": fast_name,
            "open_dis_name": open_name,
            "same_name": fast_name == open_name,
        }
        overlap.append(item)
        if fast_name != open_name:
            name_mismatches.append(item)

    fastdis_only = [
        {
            "pdu_type": pdu_type,
            "fastdis_name": fastdis_dis7[pdu_type].class_name,
        }
        for pdu_type in sorted(set(fastdis_dis7) - set(open_dis))
    ]
    open_dis_only = [
        {
            "pdu_type": pdu_type,
            "open_dis_name": open_dis[pdu_type],
        }
        for pdu_type in sorted(set(open_dis) - set(fastdis_dis7))
    ]

    return {
        "fastdis_dis7_catalog_count": len(fastdis_dis7),
        "open_dis_decoder_count": len(open_dis),
        "overlap_count": len(overlap),
        "name_mismatch_count": len(name_mismatches),
        "overlap": overlap,
        "fastdis_only": fastdis_only,
        "open_dis_only": open_dis_only,
        "name_mismatches": name_mismatches,
    }


def _header_from_fastdis(lib: native.NativeFastDis, packet: bytes) -> dict[str, Any]:
    observed: list[dict[str, Any]] = []

    def on_header(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, _original):
        observed.append(
            {
                "version": int(version),
                "exercise_id": int(exercise_id),
                "pdu_type": int(pdu_type),
                "protocol_family": int(protocol_family),
                "timestamp": int(timestamp),
                "length": int(length),
                "status": int(status),
            }
        )

    lib.scan_many([packet], on_header, return_stats=True)
    if not observed:
        raise RuntimeError("fastdis did not emit a header callback")
    return observed[0]


def _header_from_open_dis(pdu: Any) -> dict[str, Any]:
    return {
        "version": int(getattr(pdu, "protocolVersion")),
        "exercise_id": int(getattr(pdu, "exerciseID")),
        "pdu_type": int(getattr(pdu, "pduType")),
        "protocol_family": int(getattr(pdu, "protocolFamily")),
        "timestamp": int(getattr(pdu, "timestamp", 0)),
        "length": int(getattr(pdu, "length")),
        "status": int(getattr(pdu, "pduStatus", -1)) if hasattr(pdu, "pduStatus") else -1,
    }


def _entity_from_fastdis(lib: native.NativeFastDis, packet: bytes) -> dict[str, Any]:
    observed: list[native.EntityStatePrefix] = []

    def on_entity(entity: native.EntityStatePrefix, _original: object) -> None:
        observed.append(entity)

    lib.scan_entity_state_many([packet], on_entity, entity_state_fields=native.FASTDIS_ES_FIELD_ALL, return_stats=True)
    if not observed:
        raise RuntimeError("fastdis did not emit an Entity State callback")
    entity = observed[0]
    return {
        "entity_id": list(entity.entity_id),
        "force_id": entity.force_id,
        "variable_parameter_count": entity.variable_parameter_count,
        "entity_type": list(entity.entity_type),
        "alternate_entity_type": list(entity.alternate_entity_type),
        "location": list(entity.location),
        "orientation": list(entity.orientation),
        "marking": entity.marking_text,
    }


def _entity_from_open_dis(pdu: Any) -> dict[str, Any]:
    return {
        "entity_id": [
            int(pdu.entityID.simulationAddress.site),
            int(pdu.entityID.simulationAddress.application),
            int(pdu.entityID.entityNumber),
        ],
        "force_id": int(pdu.forceId),
        "variable_parameter_count": int(pdu.numberOfVariableParameters),
        "entity_type": [
            int(pdu.entityType.entityKind),
            int(pdu.entityType.domain),
            int(pdu.entityType.country),
            int(pdu.entityType.category),
            int(pdu.entityType.subcategory),
            int(pdu.entityType.specific),
            int(pdu.entityType.extra),
        ],
        "alternate_entity_type": [
            int(pdu.alternativeEntityType.entityKind),
            int(pdu.alternativeEntityType.domain),
            int(pdu.alternativeEntityType.country),
            int(pdu.alternativeEntityType.category),
            int(pdu.alternativeEntityType.subcategory),
            int(pdu.alternativeEntityType.specific),
            int(pdu.alternativeEntityType.extra),
        ],
        "location": [
            float(pdu.entityLocation.x),
            float(pdu.entityLocation.y),
            float(pdu.entityLocation.z),
        ],
        "orientation": [
            float(pdu.entityOrientation.psi),
            float(pdu.entityOrientation.theta),
            float(pdu.entityOrientation.phi),
        ],
        "marking": str(pdu.marking.charactersString()),
    }


def build_fixture_report(lib: native.NativeFastDis, open_dis_root: Path, create_pdu) -> dict[str, Any]:
    fixtures: list[dict[str, Any]] = []
    raw_files = sorted((open_dis_root / "tests").glob("*.raw"))
    for path in raw_files:
        data = path.read_bytes()
        pdu = create_pdu(data)
        fixture: dict[str, Any] = {
            "file": path.name,
            "byte_length": len(data),
            "open_dis_parsed": pdu is not None,
        }
        if pdu is None:
            fixture["header_match"] = False
            fixture["header_mismatches"] = ["open_dis_parse_failed"]
            fixtures.append(fixture)
            continue

        fast_header = _header_from_fastdis(lib, data)
        open_header = _header_from_open_dis(pdu)
        header_mismatches = compare_fields(
            fast_header,
            open_header,
            ["version", "exercise_id", "pdu_type", "protocol_family", "length"],
        )
        fixture["header_match"] = not header_mismatches
        fixture["header_mismatches"] = header_mismatches
        fixture["fastdis_header"] = fast_header
        fixture["open_dis_header"] = open_header

        if int(getattr(pdu, "pduType")) == native.FASTDIS_ENTITY_STATE_PDU_TYPE:
            fast_entity = _entity_from_fastdis(lib, data)
            open_entity = _entity_from_open_dis(pdu)
            entity_mismatches = compare_fields(
                fast_entity,
                open_entity,
                [
                    "entity_id",
                    "force_id",
                    "variable_parameter_count",
                    "entity_type",
                    "alternate_entity_type",
                    "location",
                    "orientation",
                    "marking",
                ],
                abs_tol=1e-4,
            )
            fixture["entity_state_match"] = not entity_mismatches
            fixture["entity_state_mismatches"] = entity_mismatches
            fixture["fastdis_entity_state"] = fast_entity
            fixture["open_dis_entity_state"] = open_entity
        else:
            fixture["entity_state_match"] = None
            fixture["entity_state_mismatches"] = []
        fixtures.append(fixture)

    entity_fixtures = [item for item in fixtures if item["entity_state_match"] is not None]
    return {
        "fixture_count": len(fixtures),
        "header_match_count": sum(1 for item in fixtures if item["header_match"]),
        "entity_fixture_count": len(entity_fixtures),
        "entity_match_count": sum(1 for item in entity_fixtures if item["entity_state_match"]),
        "fixtures": fixtures,
    }


def render_markdown(report: dict[str, Any]) -> str:
    catalog = report["catalog"]
    fixtures = report["fixtures"]
    lines = [
        "# fastdis differential report",
        "",
        "This report compares fastdis against Open-DIS Python as an independent implementation oracle.",
        "Open-DIS is treated as a practical reference implementation, not as the normative DIS standard.",
        "",
        "## Catalog overlap",
        "",
        f"- fastdis DIS7 catalog entries: `{catalog['fastdis_dis7_catalog_count']}`",
        f"- Open-DIS Python decoder entries: `{catalog['open_dis_decoder_count']}`",
        f"- overlapping PDU types: `{catalog['overlap_count']}`",
        f"- name mismatches on overlapping types: `{catalog['name_mismatch_count']}`",
        f"- fastdis-only DIS7 entries: `{len(catalog['fastdis_only'])}`",
        f"- Open-DIS-only decoder entries: `{len(catalog['open_dis_only'])}`",
        "",
        "## Fixture comparisons",
        "",
        f"- raw fixtures checked: `{fixtures['fixture_count']}`",
        f"- header matches: `{fixtures['header_match_count']}`",
        f"- Entity State fixtures checked: `{fixtures['entity_fixture_count']}`",
        f"- Entity State matches: `{fixtures['entity_match_count']}`",
        "",
    ]
    for item in fixtures["fixtures"]:
        header = "PASS" if item["header_match"] else "FAIL"
        entity = item["entity_state_match"]
        entity_text = "n/a" if entity is None else ("PASS" if entity else "FAIL")
        lines.append(f"- `{item['file']}`: header `{header}`, Entity State `{entity_text}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open-dis-root", type=Path, required=True, help="path to an open-dis-python checkout")
    parser.add_argument("--lib", help="path to libfastdis.so/libfastdis.dylib/fastdis.dll")
    parser.add_argument("--out", type=Path, required=True, help="write machine-readable JSON report here")
    parser.add_argument("--md-out", type=Path, help="write Markdown summary here")
    args = parser.parse_args(argv)

    open_dis_root = args.open_dis_root.resolve()
    pdu_decoders, create_pdu = load_open_dis(open_dis_root)
    lib = native.load_native(args.lib)

    report = {
        "schema_version": 1,
        "oracle": {
            "name": "open-dis-python",
            "root": str(open_dis_root),
            "git_rev": maybe_git_rev(open_dis_root),
        },
        "catalog": build_catalog_report(pdu_decoders),
        "fixtures": build_fixture_report(lib, open_dis_root, create_pdu),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(report) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
