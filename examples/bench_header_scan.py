from __future__ import annotations

import itertools
import time

import fastdis
from fastdis import _fallback


def pdu() -> bytes:
    header = bytearray(12)
    header[0] = 7
    header[1] = 1
    header[2] = 1
    header[3] = 1
    header[8:10] = (12).to_bytes(2, "big")
    return bytes(header)


def bench(label: str, fn, n: int) -> None:
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"{label:28s} {n / elapsed:12,.0f} packets/s  elapsed={elapsed:.3f}s  result={result!r}")


if __name__ == "__main__":
    n = 1_000_000
    packet = pdu()
    print("C accelerator:", fastdis.HAS_C_ACCELERATOR)
    bench("C scan_many no callback", lambda: fastdis.scan_many(itertools.repeat(packet, n), None, versions=7, pdu_types=1), n)
    bench("C count_by_type", lambda: fastdis.count_by_type(itertools.repeat(packet, n), versions=7), n)
    bench("Python scan_many no callback", lambda: _fallback.scan_many(itertools.repeat(packet, n), None, versions=7, pdu_types=1), n)
    bench("Python count_by_type", lambda: _fallback.count_by_type(itertools.repeat(packet, n), versions=7), n)
