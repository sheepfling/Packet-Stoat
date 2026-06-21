from __future__ import annotations

import fastdis


def _minimal_packet(descriptor: fastdis.MessageDescriptor) -> bytes:
    length = 12
    status_or_padding = (0, 0) if descriptor.protocol_version >= 7 else (0x12, 0x34)
    return bytes(
        [
            descriptor.protocol_version,
            1,
            descriptor.pdu_type,
            descriptor.protocol_family,
            0,
            0,
            0,
            1,
            (length >> 8) & 0xFF,
            length & 0xFF,
            status_or_padding[0],
            status_or_padding[1],
        ]
    )


def test_generated_message_descriptors_cover_catalog() -> None:
    descriptor_keys = {(item.protocol_version, item.pdu_type) for item in fastdis.MESSAGE_DESCRIPTORS}
    catalog_keys = {(item.protocol_version, item.pdu_type) for item in fastdis.PDU_CATALOG}

    assert len(fastdis.MESSAGE_DESCRIPTORS) == len(fastdis.PDU_CATALOG)
    assert descriptor_keys == catalog_keys


def test_every_cataloged_pdu_has_generic_parse_visit_serialize_roundtrip() -> None:
    for descriptor in fastdis.MESSAGE_DESCRIPTORS:
        packet = _minimal_packet(descriptor)
        view = fastdis.parse_pdu(packet)

        assert view is not None
        assert view.descriptor == descriptor
        assert view.header[0] == descriptor.protocol_version
        assert view.header[2] == descriptor.pdu_type
        assert view.header[3] == descriptor.protocol_family
        assert fastdis.serialize_pdu(view) == packet
        assert fastdis.roundtrip_packet(packet) == packet

        fields = fastdis.visit_pdu_fields(view)
        assert any(field.path == "header.pdu_type" and field.value == descriptor.pdu_type for field in fields)
        assert any(field.path == "body" and field.length == 0 for field in fields)
        assert fastdis.walk_pdu_fields(view, lambda _field: None) == len(fields)


def test_unknown_pdu_is_rejected_in_strict_mode_and_skipped_in_lenient_mode() -> None:
    packet = bytes([7, 1, 250, 1, 0, 0, 0, 1, 0, 12, 0, 0])

    assert fastdis.parse_pdu(packet, strict=False) is None
    try:
        fastdis.parse_pdu(packet)
    except ValueError as exc:
        assert "unknown DIS PDU type" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("strict parse should reject unknown PDU type")
