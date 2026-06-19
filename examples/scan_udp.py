from __future__ import annotations

import socket

import fastdis


def datagrams(host: str = "0.0.0.0", port: int = 3000, size: int = 65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    while True:
        data, _addr = sock.recvfrom(size)
        yield data


def on_entity_state(version, exercise_id, pdu_type, protocol_family, timestamp, length, status, packet):
    print(
        f"DIS v{version} exercise={exercise_id} type={pdu_type} "
        f"family={protocol_family} len={length} status={status} bytes={len(packet)}"
    )


if __name__ == "__main__":
    print("C accelerator:", fastdis.HAS_C_ACCELERATOR)
    fastdis.scan_many(
        datagrams(port=3000),
        on_entity_state,
        versions={6, 7},
        pdu_types={1},
        sample_every=1,
        strict=False,
    )
