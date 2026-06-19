from __future__ import annotations

import pathlib
import sys

import fastdis


def fixed_datagrams(path: pathlib.Path, datagram_size: int):
    data = path.read_bytes()
    for i in range(0, len(data), datagram_size):
        chunk = data[i : i + datagram_size]
        if chunk:
            yield chunk


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python examples/count_file.py PACKET_FILE DATAGRAM_SIZE")

    counts = fastdis.count_by_type(fixed_datagrams(pathlib.Path(sys.argv[1]), int(sys.argv[2])), versions={6, 7})
    for pdu_type, count in enumerate(counts):
        if count:
            print(f"pdu_type={pdu_type} count={count}")
