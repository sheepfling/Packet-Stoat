from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import subprocess
import sys

import fastdis


ROOT = Path(__file__).resolve().parents[1]


def _packet(version: int, pdu_type: int, family: int, *, body: bytes = b"") -> bytes:
    length = 12 + len(body)
    return struct.pack(">BBBBIHH", version, 1, pdu_type, family, 0x10203040, length, 0) + body


def test_pdu_log_descriptors_cover_all_141_versioned_rows() -> None:
    descriptors = fastdis.PDU_LOG_DESCRIPTORS
    assert len(descriptors) == 141
    assert sum(1 for item in descriptors if item.version == 6) == 68
    assert sum(1 for item in descriptors if item.version == 7) == 73
    assert all(item.summary_template for item in descriptors)
    assert all(item.endpoint_unreal for item in descriptors)
    assert all(item.endpoint_godot for item in descriptors)
    assert all(item.endpoint_unity for item in descriptors)


def test_pdu_log_descriptor_exposes_engine_behavior() -> None:
    entity = fastdis.find_pdu_log_descriptor(7, 1)
    assert entity is not None
    assert entity.support_level == "production_supported"
    assert entity.endpoint_behavior("unreal") == "entity_state_adapter"
    assert entity.endpoint_behavior("godot") == "entity_state_signal"
    assert entity.endpoint_behavior("unity") == "entitystateevent"

    attribute = fastdis.find_pdu_log_descriptor(7, 72)
    assert attribute is not None
    assert attribute.support_level == "field_visitor"
    assert "dis7_only" in attribute.diagnostic_tags
    assert attribute.default_log_level == "debug"


def test_make_pdu_log_event_formats_human_and_jsonl_outputs() -> None:
    event = fastdis.make_pdu_log_event(_packet(7, 1, 1, body=b"\0" * 4), source="unity", endpoint="unity")
    assert event.schema == "fastdis.log.pdu.v1"
    assert event.code == "FDIS0100_PACKET_RECEIVED"
    assert event.version == 7
    assert event.pdu_type == 1
    assert event.endpoint_behavior == "entitystateevent"

    summary = fastdis.format_log_summary(event)
    assert summary.startswith("[FastDIS] rx DIS7 Entity State")
    assert "behavior=entitystateevent" in summary

    payload = json.loads(fastdis.log_event_to_json(event))
    assert payload["schema"] == "fastdis.log.pdu.v1"
    assert payload["translation"]["status"] == "not_requested"


def test_schema_gap_pdu_logs_as_warning_with_diagnostic() -> None:
    event = fastdis.make_pdu_log_event(_packet(7, 0, 0, body=b"\0" * 4), endpoint="unreal")
    assert event.level == "warning"
    assert event.code == "FDIS0202_PDU_SCHEMA_GAP"
    assert event.pdu_name == "Other"
    assert event.support_level == "enum_only"
    assert event.diagnostics
    assert "raw_preserved=true" in fastdis.format_log_summary(event)


def test_malformed_packet_logs_drop_event() -> None:
    event = fastdis.make_pdu_log_event(b"\x07\x01")
    assert event.event_kind == "pdu.dropped"
    assert event.level == "error"
    assert event.code == "FDIS0300_MALFORMED_TOO_SHORT"
    assert event.version is None
    assert "drop malformed packet" in fastdis.format_log_summary(event)


def test_log_aggregator_summarizes_counts() -> None:
    aggregate = fastdis.PduLogAggregator()
    aggregate.record(fastdis.make_pdu_log_event(_packet(7, 1, 1)))
    aggregate.record(fastdis.make_pdu_log_event(_packet(7, 0, 0)))
    aggregate.record(fastdis.make_pdu_log_event(b"\x01"))
    summary = aggregate.summary(interval_seconds=5)
    assert "rx=3" in summary
    assert "unsupported=1" in summary
    assert "malformed=1" in summary


def test_engine_descriptor_artifacts_are_generated() -> None:
    unreal = ROOT / "examples" / "unreal" / "FastDis" / "Source" / "FastDisUnreal" / "Public" / "FastDisPduLogCatalog.h"
    unity = ROOT / "integrations" / "unity" / "com.sheepfling.fastdis" / "Runtime" / "Logging" / "FastDisPduLogCatalog.cs"
    godot = ROOT / "examples" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "fastdis_pdu_log_catalog.gd"
    assert "FastDisPduLogCatalogCount = 141" in unreal.read_text(encoding="utf-8")
    assert "FastDisPduLogCatalog" in unity.read_text(encoding="utf-8")
    assert "const DESCRIPTORS = [" in godot.read_text(encoding="utf-8")


def test_logging_check_command_passes() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "fastdis", "logging", "check", "--json"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["overall_status"] == "pass"
    assert payload["summary"]["total_descriptors"] == 141


def test_generate_pdu_log_catalog_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_pdu_log_catalog.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
