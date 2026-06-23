from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys

import fastdis


ROOT = Path(__file__).resolve().parents[1]


def _ensure_manifest() -> dict[str, object]:
    path = ROOT / "generated" / "semantic_pdu_parser_manifest.json"
    if not path.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_semantic_pdu_parsers.py")],
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


def test_semantic_parser_manifest_has_141_entry_points() -> None:
    manifest = _ensure_manifest()
    summary = manifest["summary"]
    assert summary["records"] == 141
    assert summary["semantic_parsers"] == 141
    assert summary["semantic_observation"] == 137
    assert summary["semantic_prefix"] == 4
    assert summary["fully_domain_decoded"] == 4
    assert len(fastdis.SEMANTIC_PDU_DESCRIPTORS) == 141


def test_every_standard_pdu_dispatches_to_a_semantic_slotted_class() -> None:
    for descriptor in fastdis.SEMANTIC_PDU_DESCRIPTORS:
        packet = _packet(descriptor.protocol_version, descriptor.pdu_type, descriptor.protocol_family, body=b"\x01\x02")
        view = fastdis.parse_semantic_pdu(packet)
        assert view is not None
        assert view.descriptor == descriptor
        assert view.header[0] == descriptor.protocol_version
        assert view.header[2] == descriptor.pdu_type
        assert view.header[3] == descriptor.protocol_family
        assert view.body == b"\x01\x02"
        assert view.semantic_level == descriptor.semantic_level
        assert fastdis.serialize_semantic_pdu(view) == packet
        assert not hasattr(view, "__dict__")
        assert hasattr(type(view), "__slots__")
        assert type(view).__name__ == descriptor.semantic_class


def test_semantic_observation_rows_are_explicit_and_diagnostic() -> None:
    fire = fastdis.parse_semantic_pdu(_packet(7, 2, 2, body=b"abc"))
    assert fire is not None
    assert fire.semantic_level == "semantic_observation"
    assert not fire.descriptor.fully_domain_decoded
    assert fire.semantic_fields["standard_name"] == "Fire"
    assert fire.semantic_fields["raw_body"] == b"abc"
    assert any("full domain semantics not yet implemented" in item for item in fire.diagnostics)


def test_semantic_prefix_rows_remain_marked_for_entity_state() -> None:
    entity_state = fastdis.parse_semantic_pdu(_packet(7, 1, 1, body=b"\x00" * 132))
    assert entity_state is not None
    assert entity_state.semantic_level == "semantic_prefix"
    assert entity_state.descriptor.fully_domain_decoded
    assert entity_state.semantic_fields["semantic_prefix_available"] is True


def test_generate_semantic_pdu_parsers_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_semantic_pdu_parsers.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
