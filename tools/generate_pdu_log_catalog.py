#!/usr/bin/env python3
"""Generate the FastDIS all-PDU logging contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, ROOT
from generate_pdu_coverage import build_manifests


DIAGNOSTIC_CODES = {
    "FDIS0001_SOCKET_OPEN": "Socket opened.",
    "FDIS0002_SOCKET_BIND_FAILED": "Socket bind failed.",
    "FDIS0100_PACKET_RECEIVED": "Packet received.",
    "FDIS0101_PACKET_DROPPED_FILTER": "Packet dropped by filter.",
    "FDIS0200_PDU_UNSUPPORTED_KNOWN": "Known PDU has no specialized endpoint behavior.",
    "FDIS0201_PDU_UNKNOWN_TYPE": "Unknown PDU type for the observed DIS version.",
    "FDIS0202_PDU_SCHEMA_GAP": "Known PDU is present in the standard backbone but missing XML/IR schema.",
    "FDIS0300_MALFORMED_TOO_SHORT": "Packet is shorter than the DIS header.",
    "FDIS0301_MALFORMED_DECLARED_LENGTH_EXCEEDS_DATAGRAM": "Declared PDU length exceeds datagram size.",
    "FDIS0302_MALFORMED_LENGTH_TOO_SMALL": "Declared PDU length is smaller than the DIS header.",
    "FDIS0400_TRANSLATION_EXACT": "Translation is exact or same-version.",
    "FDIS0401_TRANSLATION_RENAMED": "Translation uses a documented PDU name alias.",
    "FDIS0402_TRANSLATION_DEFAULTED_FIELD": "Translation defaulted a target-version field.",
    "FDIS0403_TRANSLATION_DROPPED_FIELD": "Translation dropped a source-only field.",
    "FDIS0404_TRANSLATION_DROPPED_PDU": "Translation dropped a source-only PDU.",
    "FDIS0500_ENTITY_SPAWNED": "Entity spawned.",
    "FDIS0501_ENTITY_UPDATED": "Entity updated.",
    "FDIS0502_ENTITY_REMOVED": "Entity removed.",
    "FDIS0503_ENTITY_STALE": "Entity became stale.",
    "FDIS0600_ORIENTATION_PROFILE_APPLIED": "Orientation profile applied.",
    "FDIS0601_ORIENTATION_VALIDATION_FAILED": "Orientation validation failed.",
    "FDIS0700_DEAD_RECKONING_ENABLED": "Dead reckoning enabled.",
    "FDIS0701_DEAD_RECKONING_UNSUPPORTED_ALGORITHM": "Dead reckoning algorithm unsupported.",
}

FAMILY_TAGS = {
    1: ("entity",),
    2: ("warfare", "event"),
    3: ("logistics",),
    4: ("radio",),
    5: ("simulation_management",),
    6: ("sensor", "ew"),
    7: ("aggregate",),
    8: ("minefield",),
    9: ("synthetic_environment",),
    10: ("reliable_simulation_management",),
    11: ("live_entity",),
    13: ("information_operations",),
}


def _slug(name: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", name.strip().lower()).strip("_")
    return slug or "pdu"


def _default_log_level(row: dict[str, Any]) -> str:
    if row["schema_status"] == "SCHEMA_GAP" or row["catalog_status"] == "ENUM_ONLY":
        return "warning"
    if row["typed_parser"]:
        return "debug"
    return "debug"


def _support_level(row: dict[str, Any]) -> str:
    if row["typed_parser"]:
        return "production_supported"
    if row["field_visitor"]:
        return "field_visitor"
    if row["schema_status"] == "PRESENT_BUT_MISSING_PDU_TYPE_INITIAL_VALUE":
        return "schema_patch_required"
    if row["schema_status"] == "SCHEMA_GAP":
        return "enum_only"
    return str(row["support_level"]).lower()


def _summary_template(row: dict[str, Any]) -> str:
    name = str(row["standard_name"])
    support = _support_level(row)
    if int(row["pdu_type"]) == 1:
        return "rx {version_label} Entity State pdu=1 ex={exercise_id} len={declared_length} behavior={endpoint_behavior}"
    if support in {"enum_only", "schema_patch_required"}:
        return (
            "rx {version_label} "
            + name
            + " pdu={pdu_type} ex={exercise_id} len={declared_length} "
            + "behavior={endpoint_behavior} support={support_level} raw_preserved=true"
        )
    return "rx {version_label} " + name + " pdu={pdu_type} ex={exercise_id} len={declared_length} behavior={endpoint_behavior}"


def _field_hints(row: dict[str, Any]) -> tuple[str, ...]:
    pdu_type = int(row["pdu_type"])
    if pdu_type in {1, 67}:
        return ("entity_id", "force_id", "location", "orientation", "linear_velocity", "marking")
    if pdu_type in {2, 3, 49, 50, 68, 69}:
        return ("firing_entity_id", "target_entity_id", "munition_id", "event_id")
    if pdu_type in {11, 12, 51, 52}:
        return ("originating_entity_id", "receiving_entity_id", "request_id")
    if pdu_type in {23, 24, 25, 26, 27, 28, 29, 30, 31, 32}:
        return ("entity_id", "radio_id", "emitter_id", "encoding_scheme")
    return ()


def _diagnostic_tags(row: dict[str, Any]) -> tuple[str, ...]:
    tags = list(FAMILY_TAGS.get(int(row["protocol_family"]), ()))
    if row["schema_status"] == "SCHEMA_GAP":
        tags.append("schema_gap")
    if row["catalog_status"] == "ENUM_ONLY":
        tags.append("enum_only")
    if int(row["standard_version"]) == 7 and int(row["pdu_type"]) >= 68:
        tags.append("dis7_only")
    if row["alias"]:
        tags.append("alias")
    if int(row["pdu_type"]) == 1:
        tags.append("entity_transform")
    return tuple(dict.fromkeys(tags))


def log_rows(dis6: Path, dis7: Path) -> list[dict[str, Any]]:
    _backbone, coverage = build_manifests(dis6, dis7)
    rows: list[dict[str, Any]] = []
    for row in coverage["rows"]:
        version = int(row["standard_version"])
        pdu_type = int(row["pdu_type"])
        name = str(row["standard_name"])
        aliases: tuple[str, ...] = ()
        if row["alias"]:
            generated = row["generated_catalog_record"]
            generated_name = generated["name"] if generated else name
            aliases = tuple(item for item in (generated_name,) if item and item != name)
        endpoint_behavior = {
            key: str(value).lower()
            for key, value in dict(row["endpoint_behavior"]).items()
            if key in {"python", "unreal", "godot", "unity", "lattice_lab"}
        }
        support = _support_level(row)
        rows.append(
            {
                "version": version,
                "pdu_type": pdu_type,
                "canonical_name": name,
                "descriptor_key": f"dis{version}_pdu{pdu_type:03d}_{_slug(name)}",
                "aliases": aliases,
                "protocol_family": int(row["protocol_family"]),
                "family_name": str(row["family_name"]),
                "support_level": support,
                "endpoint_behavior": endpoint_behavior,
                "default_log_level": _default_log_level(row),
                "summary_template": _summary_template(row),
                "diagnostic_tags": _diagnostic_tags(row),
                "field_hints": _field_hints(row),
            }
        )
    return sorted(rows, key=lambda item: (item["version"], item["pdu_type"]))


def _py_tuple(values: tuple[str, ...]) -> str:
    return repr(tuple(values))


def _py_descriptor(row: dict[str, Any]) -> str:
    endpoints = dict(row["endpoint_behavior"])
    return (
        "    FastDisPduLogDescriptor(\n"
        f"        version={row['version']},\n"
        f"        pdu_type={row['pdu_type']},\n"
        f"        canonical_name={row['canonical_name']!r},\n"
        f"        aliases={_py_tuple(tuple(row['aliases']))},\n"
        f"        protocol_family={row['protocol_family']},\n"
        f"        family_name={row['family_name']!r},\n"
        f"        support_level={row['support_level']!r},\n"
        f"        endpoint_python={endpoints['python']!r},\n"
        f"        endpoint_unreal={endpoints['unreal']!r},\n"
        f"        endpoint_godot={endpoints['godot']!r},\n"
        f"        endpoint_unity={endpoints['unity']!r},\n"
        f"        endpoint_lattice_lab={endpoints['lattice_lab']!r},\n"
        f"        default_log_level={row['default_log_level']!r},\n"
        f"        summary_template={row['summary_template']!r},\n"
        f"        diagnostic_tags={_py_tuple(tuple(row['diagnostic_tags']))},\n"
        f"        field_hints={_py_tuple(tuple(row['field_hints']))},\n"
        "    ),"
    )


def generate_python(rows: list[dict[str, Any]]) -> str:
    descriptors = "\n".join(_py_descriptor(row) for row in rows)
    codes = "\n".join(f"    {key!r}: {value!r}," for key, value in sorted(DIAGNOSTIC_CODES.items()))
    return (
        '"""Generated FastDIS PDU logging contract.\n\n'
        "Every standard DIS 6/7 PDU row has a descriptor, default log level,\n"
        "endpoint behavior, summary template, and JSONL-compatible event shape.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from dataclasses import asdict, dataclass\n"
        "import json\n"
        "import time\n"
        "from typing import Any\n\n"
        "from . import _fallback\n\n\n"
        "HeaderTuple = tuple[int, int, int, int, int, int, int, int]\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class FastDisPduLogDescriptor:\n"
        "    version: int\n"
        "    pdu_type: int\n"
        "    canonical_name: str\n"
        "    aliases: tuple[str, ...]\n"
        "    protocol_family: int\n"
        "    family_name: str\n"
        "    support_level: str\n"
        "    endpoint_python: str\n"
        "    endpoint_unreal: str\n"
        "    endpoint_godot: str\n"
        "    endpoint_unity: str\n"
        "    endpoint_lattice_lab: str\n"
        "    default_log_level: str\n"
        "    summary_template: str\n"
        "    diagnostic_tags: tuple[str, ...]\n"
        "    field_hints: tuple[str, ...]\n\n"
        "    def endpoint_behavior(self, endpoint: str) -> str:\n"
        "        normalized = endpoint.lower()\n"
        "        if normalized == 'python':\n"
        "            return self.endpoint_python\n"
        "        if normalized == 'unreal':\n"
        "            return self.endpoint_unreal\n"
        "        if normalized == 'godot':\n"
        "            return self.endpoint_godot\n"
        "        if normalized == 'unity':\n"
        "            return self.endpoint_unity\n"
        "        if normalized in {'lattice', 'lattice_lab'}:\n"
        "            return self.endpoint_lattice_lab\n"
        "        return 'generic_event'\n\n\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class FastDisLogEvent:\n"
        "    schema: str\n"
        "    time_unix_ns: int\n"
        "    source: str\n"
        "    stream_id: str\n"
        "    event_kind: str\n"
        "    level: str\n"
        "    code: str\n"
        "    version: int | None\n"
        "    exercise_id: int | None\n"
        "    pdu_type: int | None\n"
        "    pdu_name: str | None\n"
        "    protocol_family: int | None\n"
        "    declared_length: int | None\n"
        "    packet_size: int\n"
        "    support_level: str\n"
        "    endpoint_behavior: str\n"
        "    diagnostics: tuple[str, ...]\n"
        "    rate_limited_count: int = 0\n"
        "    translation_status: str = 'not_requested'\n"
        "    entity_id: dict[str, int] | None = None\n\n\n"
        "DIAGNOSTIC_CODES: dict[str, str] = {\n"
        + codes
        + "\n}\n\n"
        "PDU_LOG_DESCRIPTORS: tuple[FastDisPduLogDescriptor, ...] = (\n"
        + descriptors
        + "\n)\n\n"
        "_DESCRIPTORS_BY_KEY = {(item.version, item.pdu_type): item for item in PDU_LOG_DESCRIPTORS}\n\n\n"
        "def find_pdu_log_descriptor(version: int, pdu_type: int) -> FastDisPduLogDescriptor | None:\n"
        "    return _DESCRIPTORS_BY_KEY.get((version, pdu_type))\n\n\n"
        "def _now_ns() -> int:\n"
        "    return time.time_ns()\n\n\n"
        "def _malformed_event(data: bytes | bytearray | memoryview, message: str, source: str, stream_id: str) -> FastDisLogEvent:\n"
        "    text = message.lower()\n"
        "    if 'shorter than the 12-byte header' in text:\n"
        "        code = 'FDIS0300_MALFORMED_TOO_SHORT'\n"
        "    elif 'exceeds supplied buffer' in text:\n"
        "        code = 'FDIS0301_MALFORMED_DECLARED_LENGTH_EXCEEDS_DATAGRAM'\n"
        "    elif 'smaller than the header' in text:\n"
        "        code = 'FDIS0302_MALFORMED_LENGTH_TOO_SMALL'\n"
        "    else:\n"
        "        code = 'FDIS0300_MALFORMED_TOO_SHORT'\n"
        "    return FastDisLogEvent(\n"
        "        schema='fastdis.log.pdu.v1',\n"
        "        time_unix_ns=_now_ns(),\n"
        "        source=source,\n"
        "        stream_id=stream_id,\n"
        "        event_kind='pdu.dropped',\n"
        "        level='error',\n"
        "        code=code,\n"
        "        version=None,\n"
        "        exercise_id=None,\n"
        "        pdu_type=None,\n"
        "        pdu_name=None,\n"
        "        protocol_family=None,\n"
        "        declared_length=None,\n"
        "        packet_size=len(memoryview(data).cast('B')),\n"
        "        support_level='malformed',\n"
        "        endpoint_behavior='drop',\n"
        "        diagnostics=(message,),\n"
        "    )\n\n\n"
        "def make_pdu_log_event(\n"
        "    data: bytes | bytearray | memoryview,\n"
        "    *,\n"
        "    source: str = 'python',\n"
        "    endpoint: str = 'python',\n"
        "    stream_id: str = '',\n"
        "    event_kind: str = 'pdu.received',\n"
        "    level: str | None = None,\n"
        ") -> FastDisLogEvent:\n"
        "    try:\n"
        "        header = _fallback.parse_header(data, strict=True)\n"
        "    except ValueError as exc:\n"
        "        return _malformed_event(data, str(exc), source, stream_id)\n"
        "    assert header is not None\n"
        "    descriptor = find_pdu_log_descriptor(header[0], header[2])\n"
        "    if descriptor is None:\n"
        "        return FastDisLogEvent(\n"
        "            schema='fastdis.log.pdu.v1',\n"
        "            time_unix_ns=_now_ns(),\n"
        "            source=source,\n"
        "            stream_id=stream_id,\n"
        "            event_kind=event_kind,\n"
        "            level=level or 'warning',\n"
        "            code='FDIS0201_PDU_UNKNOWN_TYPE',\n"
        "            version=header[0],\n"
        "            exercise_id=header[1],\n"
        "            pdu_type=header[2],\n"
        "            pdu_name=None,\n"
        "            protocol_family=header[3],\n"
        "            declared_length=header[5],\n"
        "            packet_size=len(memoryview(data).cast('B')),\n"
        "            support_level='unknown',\n"
        "            endpoint_behavior='generic_event',\n"
        "            diagnostics=('unknown PDU type for protocol version',),\n"
        "        )\n"
        "    diagnostics: list[str] = []\n"
        "    code = 'FDIS0100_PACKET_RECEIVED'\n"
        "    if descriptor.support_level in {'enum_only', 'schema_patch_required'}:\n"
        "        code = 'FDIS0202_PDU_SCHEMA_GAP'\n"
        "        diagnostics.append('known PDU has no generated schema-backed parser')\n"
        "    elif descriptor.endpoint_behavior(endpoint) in {'generic_pdu_event', 'generic_event', 'pdureceived'}:\n"
        "        code = 'FDIS0200_PDU_UNSUPPORTED_KNOWN'\n"
        "        diagnostics.append('known PDU is routed through generic endpoint behavior')\n"
        "    return FastDisLogEvent(\n"
        "        schema='fastdis.log.pdu.v1',\n"
        "        time_unix_ns=_now_ns(),\n"
        "        source=source,\n"
        "        stream_id=stream_id,\n"
        "        event_kind=event_kind,\n"
        "        level=level or descriptor.default_log_level,\n"
        "        code=code,\n"
        "        version=header[0],\n"
        "        exercise_id=header[1],\n"
        "        pdu_type=header[2],\n"
        "        pdu_name=descriptor.canonical_name,\n"
        "        protocol_family=header[3],\n"
        "        declared_length=header[5],\n"
        "        packet_size=len(memoryview(data).cast('B')),\n"
        "        support_level=descriptor.support_level,\n"
        "        endpoint_behavior=descriptor.endpoint_behavior(endpoint),\n"
        "        diagnostics=tuple(diagnostics),\n"
        "    )\n\n\n"
        "def log_event_to_dict(event: FastDisLogEvent) -> dict[str, Any]:\n"
        "    payload = asdict(event)\n"
        "    payload['translation'] = {'status': payload.pop('translation_status')}\n"
        "    return payload\n\n\n"
        "def log_event_to_json(event: FastDisLogEvent) -> str:\n"
        "    return json.dumps(log_event_to_dict(event), separators=(',', ':'), sort_keys=True)\n\n\n"
        "def format_log_summary(event: FastDisLogEvent) -> str:\n"
        "    if event.version is None or event.pdu_type is None:\n"
        "        reason = event.diagnostics[0] if event.diagnostics else event.code\n"
        "        return f'[FastDIS] drop malformed packet reason={reason} size={event.packet_size}'\n"
        "    descriptor = find_pdu_log_descriptor(event.version, event.pdu_type)\n"
        "    version_label = f'DIS{event.version}'\n"
        "    if descriptor is None:\n"
        "        return f'[FastDIS] rx {version_label} unknown pdu={event.pdu_type} ex={event.exercise_id} len={event.declared_length}'\n"
        "    text = descriptor.summary_template.format(\n"
        "        version_label=version_label,\n"
        "        pdu_name=event.pdu_name,\n"
        "        pdu_type=event.pdu_type,\n"
        "        exercise_id=event.exercise_id,\n"
        "        declared_length=event.declared_length,\n"
        "        endpoint_behavior=event.endpoint_behavior,\n"
        "        support_level=event.support_level,\n"
        "    )\n"
        "    if event.rate_limited_count:\n"
        "        text = f'{text} rate_limited_count={event.rate_limited_count}'\n"
        "    return f'[FastDIS] {text}'\n\n\n"
        "class PduLogAggregator:\n"
        "    def __init__(self) -> None:\n"
        "        self.total = 0\n"
        "        self.malformed = 0\n"
        "        self.unsupported = 0\n"
        "        self.counts: dict[tuple[int, int], int] = {}\n\n"
        "    def record(self, event: FastDisLogEvent) -> None:\n"
        "        self.total += 1\n"
        "        if event.version is None or event.pdu_type is None:\n"
        "            self.malformed += 1\n"
        "            return\n"
        "        key = (event.version, event.pdu_type)\n"
        "        self.counts[key] = self.counts.get(key, 0) + 1\n"
        "        if event.code in {'FDIS0200_PDU_UNSUPPORTED_KNOWN', 'FDIS0201_PDU_UNKNOWN_TYPE', 'FDIS0202_PDU_SCHEMA_GAP'}:\n"
        "            self.unsupported += 1\n\n"
        "    def summary(self, *, interval_seconds: int = 5) -> str:\n"
        "        top = sorted(self.counts.items(), key=lambda item: item[1], reverse=True)[:5]\n"
        "        pdu_counts = ' '.join(f'DIS{version}/pdu{pdu_type}={count}' for (version, pdu_type), count in top)\n"
        "        if not pdu_counts:\n"
        "            pdu_counts = 'none'\n"
        "        return (\n"
        "            f'[FastDIS] {interval_seconds}s summary rx={self.total} '\n"
        "            f'unsupported={self.unsupported} malformed={self.malformed} {pdu_counts}'\n"
        "        )\n"
    )


def generate_manifest(rows: list[dict[str, Any]]) -> str:
    payload = {
        "schema": "fastdis.pdu_log_catalog.v1",
        "policy": {
            "coverage": "Every standard DIS 6/7 PDU row has one generated log descriptor.",
            "runtime": "Engine adapters consume FastDisLogEvent and do not hand-code per-PDU log paths.",
            "rate_limiting": "Per-packet trace logging is opt-in; summary and first-occurrence diagnostics are the default product posture.",
        },
        "diagnostic_codes": DIAGNOSTIC_CODES,
        "summary": {
            "records": len(rows),
            "dis6_rows": sum(1 for row in rows if row["version"] == 6),
            "dis7_rows": sum(1 for row in rows if row["version"] == 7),
            "unreal_descriptors": len(rows),
            "godot_descriptors": len(rows),
            "unity_descriptors": len(rows),
            "summary_templates": sum(1 for row in rows if row["summary_template"]),
            "jsonl_schema": "schemas/json/fastdis.log.pdu.v1.schema.json",
        },
        "rows": rows,
    }
    return json.dumps(payload, indent=2) + "\n"


def _escape_c(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def generate_unreal_header(rows: list[dict[str, Any]]) -> str:
    entries = []
    for row in rows:
        entries.append(
            "    {"
            f"{row['version']}, {row['pdu_type']}, {row['protocol_family']}, "
            f"TEXT(\"{_escape_c(row['canonical_name'])}\"), "
            f"TEXT(\"{row['support_level']}\"), "
            f"TEXT(\"{row['endpoint_behavior']['unreal']}\"), "
            f"TEXT(\"{row['default_log_level']}\")"
            "},"
        )
    return (
        "// Generated by tools/generate_pdu_log_catalog.py. Do not edit.\n"
        "#pragma once\n\n"
        "#include \"CoreMinimal.h\"\n\n"
        "struct FFastDisPduLogDescriptor\n"
        "{\n"
        "    int32 Version;\n"
        "    int32 PduType;\n"
        "    int32 ProtocolFamily;\n"
        "    const TCHAR* CanonicalName;\n"
        "    const TCHAR* SupportLevel;\n"
        "    const TCHAR* EndpointBehavior;\n"
        "    const TCHAR* DefaultLogLevel;\n"
        "};\n\n"
        "static constexpr int32 FastDisPduLogCatalogCount = 141;\n"
        "static const FFastDisPduLogDescriptor FastDisPduLogCatalog[] = {\n"
        + "\n".join(entries)
        + "\n};\n"
    )


def generate_unity_cs(rows: list[dict[str, Any]]) -> str:
    entries = []
    for row in rows:
        entries.append(
            "            new FastDisPduLogDescriptor("
            f"{row['version']}, {row['pdu_type']}, {row['protocol_family']}, "
            f"\"{_escape_c(row['canonical_name'])}\", "
            f"\"{row['support_level']}\", "
            f"\"{row['endpoint_behavior']['unity']}\", "
            f"\"{row['default_log_level']}\"),"
        )
    return (
        "// Generated by tools/generate_pdu_log_catalog.py. Do not edit.\n\n"
        "namespace FastDIS.Unity.Logging\n"
        "{\n"
        "    public readonly struct FastDisPduLogDescriptor\n"
        "    {\n"
        "        public readonly int Version;\n"
        "        public readonly int PduType;\n"
        "        public readonly int ProtocolFamily;\n"
        "        public readonly string CanonicalName;\n"
        "        public readonly string SupportLevel;\n"
        "        public readonly string EndpointBehavior;\n"
        "        public readonly string DefaultLogLevel;\n\n"
        "        public FastDisPduLogDescriptor(int version, int pduType, int protocolFamily, string canonicalName, string supportLevel, string endpointBehavior, string defaultLogLevel)\n"
        "        {\n"
        "            Version = version;\n"
        "            PduType = pduType;\n"
        "            ProtocolFamily = protocolFamily;\n"
        "            CanonicalName = canonicalName;\n"
        "            SupportLevel = supportLevel;\n"
        "            EndpointBehavior = endpointBehavior;\n"
        "            DefaultLogLevel = defaultLogLevel;\n"
        "        }\n"
        "    }\n\n"
        "    public static class FastDisPduLogCatalog\n"
        "    {\n"
        "        public static readonly FastDisPduLogDescriptor[] Descriptors =\n"
        "        {\n"
        + "\n".join(entries)
        + "\n        };\n"
        "    }\n"
        "}\n"
    )


def generate_godot_gd(rows: list[dict[str, Any]]) -> str:
    entries = []
    for row in rows:
        entries.append(
            "    {"
            f"\"version\": {row['version']}, "
            f"\"pdu_type\": {row['pdu_type']}, "
            f"\"protocol_family\": {row['protocol_family']}, "
            f"\"canonical_name\": \"{_escape_c(row['canonical_name'])}\", "
            f"\"support_level\": \"{row['support_level']}\", "
            f"\"endpoint_behavior\": \"{row['endpoint_behavior']['godot']}\", "
            f"\"default_log_level\": \"{row['default_log_level']}\""
            "},"
        )
    return (
        "# Generated by tools/generate_pdu_log_catalog.py. Do not edit.\n"
        "extends RefCounted\n\n"
        "const DESCRIPTORS = [\n"
        + "\n".join(entries)
        + "\n]\n"
    )


def generate_schema() -> str:
    payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://fastdis.dev/schemas/fastdis.log.pdu.v1.schema.json",
        "title": "FastDIS PDU log event",
        "type": "object",
        "required": [
            "schema",
            "time_unix_ns",
            "source",
            "stream_id",
            "event_kind",
            "level",
            "code",
            "packet_size",
            "support_level",
            "endpoint_behavior",
            "diagnostics",
        ],
        "properties": {
            "schema": {"const": "fastdis.log.pdu.v1"},
            "time_unix_ns": {"type": "integer", "minimum": 0},
            "source": {"type": "string"},
            "stream_id": {"type": "string"},
            "event_kind": {"type": "string"},
            "level": {"enum": ["trace", "debug", "info", "warning", "error", "fatal"]},
            "code": {"type": "string", "pattern": "^FDIS[0-9]{4}_[A-Z0-9_]+$"},
            "version": {"type": ["integer", "null"]},
            "exercise_id": {"type": ["integer", "null"]},
            "pdu_type": {"type": ["integer", "null"]},
            "pdu_name": {"type": ["string", "null"]},
            "protocol_family": {"type": ["integer", "null"]},
            "declared_length": {"type": ["integer", "null"]},
            "packet_size": {"type": "integer", "minimum": 0},
            "support_level": {"type": "string"},
            "endpoint_behavior": {"type": "string"},
            "diagnostics": {"type": "array", "items": {"type": "string"}},
            "rate_limited_count": {"type": "integer", "minimum": 0},
            "translation": {"type": "object"},
            "entity_id": {"type": ["object", "null"]},
        },
        "additionalProperties": True,
    }
    return json.dumps(payload, indent=2) + "\n"


def generate_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# PDU Logging Coverage",
        "",
        "This document is generated by `tools/generate_pdu_log_catalog.py`.",
        "",
        "FastDIS uses one generated PDU logging catalog for all engines. Every DIS 6/7 PDU row has a descriptor, support level, endpoint behavior, default severity, and summary template. Unreal, Godot, and Unity adapters map FastDIS log events into each engine logging system instead of hand-writing per-PDU log code.",
        "",
        "## Summary",
        "",
        f"- DIS 6 descriptors: `{sum(1 for row in rows if row['version'] == 6)} / 68`",
        f"- DIS 7 descriptors: `{sum(1 for row in rows if row['version'] == 7)} / 73`",
        f"- Total descriptors: `{len(rows)} / 141`",
        f"- Unreal descriptors: `{len(rows)} / 141`",
        f"- Godot descriptors: `{len(rows)} / 141`",
        f"- Unity descriptors: `{len(rows)} / 141`",
        f"- Summary templates: `{sum(1 for row in rows if row['summary_template'])} / 141`",
        "- JSONL schema: `schemas/json/fastdis.log.pdu.v1.schema.json`",
        "",
        "## Diagnostic Codes",
        "",
    ]
    for code, meaning in sorted(DIAGNOSTIC_CODES.items()):
        lines.append(f"- `{code}`: {meaning}")
    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| DIS | PDU | Name | Level | Support | Unreal | Godot | Unity | Summary |",
            "| ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['version']} | {row['pdu_type']} | {row['canonical_name']} | "
            f"`{row['default_log_level']}` | `{row['support_level']}` | "
            f"`{row['endpoint_behavior']['unreal']}` | `{row['endpoint_behavior']['godot']}` | "
            f"`{row['endpoint_behavior']['unity']}` | `{row['summary_template']}` |"
        )
    return "\n".join(lines) + "\n"


def outputs(dis6: Path, dis7: Path) -> dict[Path, str]:
    rows = log_rows(dis6, dis7)
    return {
        ROOT / "generated" / "pdu_log_catalog.json": generate_manifest(rows),
        ROOT / "src" / "fastdis" / "pdu_logging.py": generate_python(rows),
        ROOT / "docs" / "PDU_LOGGING_COVERAGE.md": generate_markdown(rows),
        ROOT / "schemas" / "json" / "fastdis.log.pdu.v1.schema.json": generate_schema(),
        ROOT
        / "examples"
        / "unreal"
        / "FastDis"
        / "Source"
        / "FastDisUnreal"
        / "Public"
        / "FastDisPduLogCatalog.h": generate_unreal_header(rows),
        ROOT
        / "integrations"
        / "unity"
        / "com.sheepfling.fastdis"
        / "Runtime"
        / "Logging"
        / "FastDisPduLogCatalog.cs": generate_unity_cs(rows),
        ROOT
        / "examples"
        / "godot"
        / "fastdis_demo"
        / "addons"
        / "fastdis"
        / "fastdis_pdu_log_catalog.gd": generate_godot_gd(rows),
    }


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dis6", type=Path, default=DEFAULT_DIS6)
    parser.add_argument("--dis7", type=Path, default=DEFAULT_DIS7)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = outputs(args.dis6, args.dis7)
    if args.check:
        stale: list[Path] = []
        for path, content in rendered.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("stale generated PDU logging artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    for path, content in rendered.items():
        write(path, content)
    rows = log_rows(args.dis6, args.dis7)
    print(
        "generated PDU log catalog "
        f"DIS6={sum(1 for row in rows if row['version'] == 6)} "
        f"DIS7={sum(1 for row in rows if row['version'] == 7)} "
        f"total={len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
