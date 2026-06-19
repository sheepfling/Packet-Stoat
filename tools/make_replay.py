#!/usr/bin/env python3
"""Write a simple length-prefixed .fastdispkt replay file for native benchmarks.

Format:
    repeated records of uint32_be packet_length followed by packet bytes.

This intentionally avoids libpcap as a core dependency. For real captures, write
one UDP payload per record in this format and pass it to:

    fastdis_native_bench --packet-file capture.fastdispkt
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

HEADER_SIZE = 12
ENTITY_STATE_FIXED_SIZE = 144
ENTITY_INFORMATION_FAMILY = 1
ENTITY_STATE_PDU_TYPE = 1


def _put_header(packet: bytearray, index: int) -> None:
    packet[0] = 7
    packet[1] = 3
    packet[2] = ENTITY_STATE_PDU_TYPE
    packet[3] = ENTITY_INFORMATION_FAMILY
    packet[4:8] = (0x10000000 + (index & 0x00FFFFFF)).to_bytes(4, "big")
    packet[8:10] = ENTITY_STATE_FIXED_SIZE.to_bytes(2, "big")
    packet[10] = 0x80
    packet[11] = 0


def make_entity_state(index: int, *, entities: int = 1024) -> bytes:
    packet = bytearray(ENTITY_STATE_FIXED_SIZE)
    _put_header(packet, index)
    base = HEADER_SIZE
    entity = index % max(1, entities)
    force_id = (index % 4) + 1
    packet[base + 0 : base + 6] = struct.pack(">HHH", 100, 1, entity)
    packet[base + 6] = force_id
    packet[base + 7] = 0
    packet[base + 8 : base + 16] = struct.pack(">BBHBBBB", 1, 2, 840, 3, 4, 5, 6)
    packet[base + 16 : base + 24] = struct.pack(">BBHBBBB", 1, 2, 840, 3, 4, 5, 6)
    f = (index % 1000) * 0.001
    packet[base + 24 : base + 36] = struct.pack(">fff", 1.0 + f, 2.0 + f, 3.0 + f)
    packet[base + 36 : base + 60] = struct.pack(">ddd", 1000.0 + index, 2000.0, 3000.0)
    packet[base + 60 : base + 72] = struct.pack(">fff", 0.01 + f, 0.02 + f, 0.03 + f)
    packet[base + 72 : base + 76] = (0x01020304).to_bytes(4, "big")
    packet[base + 76] = 4
    packet[base + 77 : base + 92] = bytes(range(1, 16))
    packet[base + 92 : base + 104] = struct.pack(">fff", 0.1, 0.2, 0.3)
    packet[base + 104 : base + 116] = struct.pack(">fff", 0.4, 0.5, 0.6)
    packet[base + 116] = 1
    packet[base + 117 : base + 128] = f"E{entity:05d}".encode("ascii").ljust(11, b"\x00")
    packet[base + 128 : base + 132] = (1).to_bytes(4, "big")
    return bytes(packet)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    parser.add_argument("--packets", type=int, default=100_000)
    parser.add_argument("--entities", type=int, default=1024)
    args = parser.parse_args(argv)
    if args.packets <= 0:
        parser.error("--packets must be > 0")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("wb") as fh:
        for i in range(args.packets):
            packet = make_entity_state(i, entities=args.entities)
            fh.write(len(packet).to_bytes(4, "big"))
            fh.write(packet)
    print(f"wrote {args.packets} packets to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
