from __future__ import annotations

import struct

import fastdis.native as native


def make_entity_state(site: int = 100, application: int = 1, entity: int = 42) -> bytes:
    packet = bytearray(144)
    packet[0] = 7
    packet[1] = 1
    packet[2] = native.FASTDIS_ENTITY_STATE_PDU_TYPE
    packet[3] = native.FASTDIS_ENTITY_INFORMATION_FAMILY
    packet[8:10] = (144).to_bytes(2, "big")
    packet[10] = 0x80
    b = 12
    packet[b + 0 : b + 6] = struct.pack(">HHH", site, application, entity)
    packet[b + 6] = 2
    packet[b + 36 : b + 60] = struct.pack(">ddd", 10.0, 20.0, 30.0)
    packet[b + 60 : b + 72] = struct.pack(">fff", 0.1, 0.2, 0.3)
    return bytes(packet)


lib = native.load_native()
print("ABI", lib.abi_version(), "version", lib.version_string())

packet = make_entity_state()
print("header", lib.parse_header_tuple(packet))

entity = lib.parse_entity_state_fields(
    packet,
    fields=native.FASTDIS_ES_FIELD_LOCATION | native.FASTDIS_ES_FIELD_ORIENTATION,
)
print("pose-only", entity.location, entity.orientation, "fields", hex(entity.fields_present))

scanner = lib.create_scanner(
    versions=7,
    entity_state_fields=native.FASTDIS_ES_FIELD_POSE,
)
scanner.allow_entity_ids((100, 1, 42))
stats = scanner.scan_entity_state_many(
    [packet, make_entity_state(site=999)],
    lambda entity, raw: print("kept", entity.entity_id, entity.location),
    return_stats=True,
)
print("stats", stats)
scanner.close()
