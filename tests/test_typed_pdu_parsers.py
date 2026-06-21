from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys

import fastdis


ROOT = Path(__file__).resolve().parents[1]


def _ensure_manifest() -> dict[str, object]:
    path = ROOT / "generated" / "typed_pdu_parser_manifest.json"
    if not path.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_typed_pdu_parsers.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return json.loads(path.read_text(encoding="utf-8"))


def _packet(version: int, pdu_type: int, family: int, *, body: bytes = b"") -> bytes:
    length = 12 + len(body)
    return struct.pack(">BBBBIHH", version, 1, pdu_type, family, 0x10203040, length, 0) + body


def test_typed_parser_manifest_has_141_slotted_envelopes() -> None:
    manifest = _ensure_manifest()
    summary = manifest["summary"]
    assert summary["records"] == 141
    assert summary["typed_envelope"] == 141
    assert summary["typed_structural"] == 114
    assert summary["typed_semantic"] == 2
    assert summary["byte_preserving_serializer"] == 141
    assert len(fastdis.TYPED_PDU_DESCRIPTORS) == 141


def test_every_standard_pdu_dispatches_to_a_typed_slotted_class() -> None:
    for descriptor in fastdis.TYPED_PDU_DESCRIPTORS:
        packet = _packet(descriptor.protocol_version, descriptor.pdu_type, descriptor.protocol_family, body=b"\x01\x02")
        view = fastdis.parse_typed_pdu(packet)
        assert view is not None
        assert view.descriptor == descriptor
        assert view.header[0] == descriptor.protocol_version
        assert view.header[2] == descriptor.pdu_type
        assert view.header[3] == descriptor.protocol_family
        assert view.body == b"\x01\x02"
        assert view.parse_level == descriptor.parse_level
        assert fastdis.serialize_typed_pdu(view) == packet
        assert not hasattr(view, "__dict__")
        assert hasattr(type(view), "__slots__")
        assert type(view).__name__ == descriptor.parser_class


def test_schema_backed_typed_pdus_expose_declared_field_mapping() -> None:
    fire = fastdis.parse_typed_pdu(_packet(7, 2, 2, body=b"\x00" * 8))
    assert fire is not None
    assert fire.descriptor.parse_level == "typed_structural"
    assert fire.fields["protocolVersion"] == 7
    assert fire.fields["pduType"] == 2
    assert fire.fields["rawBody"] == b"\x00" * 8
    assert "firingEntityID" in fire.fields
    assert fire.fields["firingEntityID"] is None


def test_schema_gap_typed_pdus_are_explicit_typed_envelopes() -> None:
    info_ops = fastdis.parse_typed_pdu(_packet(7, 70, 13, body=b"abc"))
    assert info_ops is not None
    assert info_ops.descriptor.standard_class_name == "InformationOperationsActionPdu"
    assert info_ops.descriptor.schema_status == "SCHEMA_GAP"
    assert info_ops.parse_level == "typed_envelope"
    assert info_ops.fields["rawBody"] == b"abc"


def test_generate_typed_pdu_parsers_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_typed_pdu_parsers.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
