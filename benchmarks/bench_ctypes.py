#!/usr/bin/env python3
"""ctypes-level benchmark for the fastdis shared library.

This benchmark intentionally includes Python wrapper overhead: packet-view
construction, ctypes calls, and optional Python callbacks. For the native hot
path alone, build and run ``fastdis_native_bench``.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import struct
import sys
import time
from typing import Callable, Iterable

# Allow running from a source checkout without installation.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import fastdis.native as native  # noqa: E402


def _make_header(version: int = 7, pdu_type: int = 1, length: int = native.FASTDIS_ENTITY_STATE_FIXED_SIZE) -> bytearray:
    packet = bytearray(length)
    packet[0] = version
    packet[1] = 3
    packet[2] = pdu_type
    packet[3] = native.FASTDIS_ENTITY_INFORMATION_FAMILY
    packet[4:8] = (0x10000000).to_bytes(4, "big")
    packet[8:10] = length.to_bytes(2, "big")
    packet[10] = 0
    packet[11] = 0
    return packet


def make_entity_state(index: int, entities: int) -> bytearray:
    packet = _make_header()
    entity = index % max(1, entities)
    force_id = (index % 4) + 1
    base = native.FASTDIS_HEADER_SIZE
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
    return packet


def make_packets(count: int, entities: int) -> list[bytearray]:
    return [make_entity_state(i, entities) for i in range(count)]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    samples = sorted(values)
    if len(samples) == 1:
        return samples[0]
    clamped = max(0.0, min(100.0, pct))
    position = (clamped / 100.0) * (len(samples) - 1)
    lower = int(position)
    upper = min(lower + 1, len(samples) - 1)
    weight = position - lower
    return samples[lower] + (samples[upper] - samples[lower]) * weight


def run_case(name: str, notes: str, packets: list[bytearray], repeats: int, fn: Callable[[], dict[str, int]]) -> dict[str, object]:
    # Warmup.
    fn()
    totals = {"seen": 0, "malformed": 0, "accepted": 0, "emitted": 0, "callbacks": 0}
    round_seconds: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        stats = fn()
        elapsed = time.perf_counter() - started
        round_seconds.append(elapsed)
        for key in totals:
            totals[key] += int(stats.get(key, 0))
    total_seconds = sum(round_seconds)
    total_packets = len(packets) * repeats
    pps = total_packets / total_seconds if total_seconds > 0 else 0.0
    best_seconds = min(round_seconds) if round_seconds else 0.0
    avg_seconds = total_seconds / repeats if repeats > 0 else 0.0
    best_mpps = (len(packets) / best_seconds) / 1_000_000.0 if best_seconds > 0 else 0.0
    avg_mpps = (len(packets) / avg_seconds) / 1_000_000.0 if avg_seconds > 0 else 0.0
    round_ms = [seconds * 1000.0 for seconds in round_seconds]
    return {
        "case": name,
        "packets": len(packets),
        "repeats": repeats,
        **totals,
        "seconds": total_seconds,
        "total_seconds": total_seconds,
        "best_ms": best_seconds * 1000.0,
        "avg_ms": avg_seconds * 1000.0,
        "p50_ms": percentile(round_ms, 50.0),
        "p95_ms": percentile(round_ms, 95.0),
        "p99_ms": percentile(round_ms, 99.0),
        "worst_ms": max(round_ms) if round_ms else 0.0,
        "best_mpps": best_mpps,
        "avg_mpps": avg_mpps,
        "round_ms": round_ms,
        "packets_per_sec": pps,
        "mega_packets_per_sec": avg_mpps,
        "notes": notes,
    }


def write_table(results: Iterable[dict[str, object]]) -> None:
    print(
        f"{'case':42s} {'best Mpps':>10s} {'avg Mpps':>10s} {'p95 ms':>10s} "
        f"{'accepted':>12s} {'emitted':>12s} {'callbacks':>12s} {'seconds':>10s}  notes"
    )
    print("-" * 144)
    for item in results:
        print(
            f"{str(item['case']):42s} "
            f"{float(item['best_mpps']):10.3f} "
            f"{float(item['avg_mpps']):10.3f} "
            f"{float(item['p95_ms']):10.3f} "
            f"{int(item['accepted']):12d} "
            f"{int(item['emitted']):12d} "
            f"{int(item['callbacks']):12d} "
            f"{float(item['total_seconds']):10.3f}  "
            f"{item['notes']}"
        )


def write_csv(path: Path | None, results: list[dict[str, object]]) -> None:
    fields = [
        "case",
        "packets",
        "repeats",
        "seen",
        "malformed",
        "accepted",
        "emitted",
        "callbacks",
        "seconds",
        "total_seconds",
        "best_ms",
        "avg_ms",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "worst_ms",
        "best_mpps",
        "avg_mpps",
        "packets_per_sec",
        "mega_packets_per_sec",
        "notes",
    ]
    fh = path.open("w", newline="") if path else sys.stdout
    try:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in results:
            writer.writerow({k: item[k] for k in fields})
    finally:
        if path:
            fh.close()


def write_json(path: Path | None, lib: native.NativeFastDis, args: argparse.Namespace, results: list[dict[str, object]]) -> None:
    payload = {
        "abi_version": lib.abi_version(),
        "library_version": lib.version_string(),
        "packets": args.packets,
        "repeats": args.repeats,
        "entities": args.entities,
        "results": results,
    }
    text = json.dumps(payload, indent=2)
    if path:
        path.write_text(text + "\n")
    else:
        print(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lib", help="Path to libfastdis.so/libfastdis.dylib/fastdis.dll")
    parser.add_argument("--packets", type=int, default=50000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--entities", type=int, default=1024)
    parser.add_argument("--format", choices=("table", "csv", "json"), default="table")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.packets <= 0 or args.repeats <= 0:
        parser.error("--packets and --repeats must be > 0")

    lib = native.load_native(args.lib)
    packets = make_packets(args.packets, args.entities)
    callback_counter = {"count": 0}

    def packet_cb(*_args) -> None:
        callback_counter["count"] += 1

    def entity_cb(_entity: native.EntityStatePrefix, _packet: object) -> None:
        callback_counter["count"] += 1

    results: list[dict[str, object]] = []

    results.append(
        run_case(
            "ctypes_header_no_callback",
            "includes packet-view setup + one ctypes scan call",
            packets,
            args.repeats,
            lambda: lib.scan_many(packets, None, return_stats=True),
        )
    )

    callback_counter["count"] = 0
    results.append(
        run_case(
            "ctypes_header_callback_every_packet",
            "Python callback for every accepted packet",
            packets,
            args.repeats,
            lambda: (
                lambda before: {
                    **lib.scan_many(packets, packet_cb, return_stats=True),
                    "callbacks": callback_counter["count"] - before,
                }
            )(callback_counter["count"]),
        )
    )

    callback_counter["count"] = 0
    results.append(
        run_case(
            "ctypes_header_callback_sample_100",
            "downsample in C before Python callback",
            packets,
            args.repeats,
            lambda: (
                lambda before: {
                    **lib.scan_many(packets, packet_cb, sample_every=100, return_stats=True),
                    "callbacks": callback_counter["count"] - before,
                }
            )(callback_counter["count"]),
        )
    )

    results.append(
        run_case(
            "ctypes_entity_pose_no_callback",
            "Entity State pose-only decode through ctypes wrapper",
            packets,
            args.repeats,
            lambda: lib.scan_entity_state_many(
                packets,
                None,
                versions=7,
                entity_state_fields=native.FASTDIS_ES_FIELD_POSE,
                return_stats=True,
            ),
        )
    )

    results.append(
        run_case(
            "ctypes_entity_all_no_callback",
            "Entity State full fixed-prefix decode through ctypes wrapper",
            packets,
            args.repeats,
            lambda: lib.scan_entity_state_many(
                packets,
                None,
                versions=7,
                entity_state_fields=native.FASTDIS_ES_FIELD_ALL,
                return_stats=True,
            ),
        )
    )

    pose_config = lib.new_config(versions=7)
    lib.use_config_profile(pose_config, "pose")
    results.append(
        run_case(
            "ctypes_entity_pose_to_batch",
            "callback-free native batch, then Python value conversion",
            packets,
            args.repeats,
            lambda: (
                lambda pair: {
                    **pair[1],
                    "callbacks": 0,
                }
            )(lib.scan_entity_state_to_batch(packets, config=pose_config, return_stats=True)),
        )
    )

    transform_config = lib.new_config(versions=7)
    lib.use_config_profile(transform_config, "transform")
    results.append(
        run_case(
            "ctypes_entity_transform_to_batch",
            "compact transform batch output, then Python value conversion",
            packets,
            args.repeats,
            lambda: (
                lambda pair: {
                    **pair[1],
                    "callbacks": 0,
                }
            )(lib.scan_entity_transforms_to_batch(packets, config=transform_config, return_stats=True)),
        )
    )

    results.append(
        run_case(
            "ctypes_entity_force_reject_no_callback",
            "C-side force-ID filter rejects all after minimal decode",
            packets,
            args.repeats,
            lambda: lib.scan_entity_state_many(
                packets,
                None,
                versions=7,
                entity_force_ids=99,
                entity_state_fields=native.FASTDIS_ES_FIELD_ROUTING,
                return_stats=True,
            ),
        )
    )

    scanner = lib.create_scanner(versions=7, entity_state_fields=native.FASTDIS_ES_FIELD_POSE)
    try:
        scanner.allow_entity_ids((100, 1, 42 % args.entities))
        results.append(
            run_case(
                "ctypes_scanner_entity_id_allow_one",
                "reusable scanner + native entity-ID allowlist",
                packets,
                args.repeats,
                lambda: scanner.scan_entity_state_many(packets, None, return_stats=True),
            )
        )

        results.append(
            run_case(
                "ctypes_scanner_transform_batch_allow_one",
                "reusable scanner + entity allowlist + compact transform batch",
                packets,
                args.repeats,
                lambda: (
                    lambda pair: {
                        **pair[1],
                        "callbacks": 0,
                    }
                )(scanner.use_entity_transform_profile().scan_entity_transforms_to_batch(packets, return_stats=True)),
            )
        )

        scanner.disable_entity_id_filter().use_entity_transform_profile()
        table = lib.create_entity_table(reserve=args.entities)
        snapshot_buffer = lib.create_snapshot_buffer(args.entities)
        try:
            results.append(
                run_case(
                    "ctypes_entity_table_ingest_latest",
                    "ctypes wrapper updates native latest-state table",
                    packets,
                    args.repeats,
                    lambda: (
                        lambda stats: {
                            **stats["scan"],
                            "callbacks": 0,
                        }
                    )(table.ingest(scanner, packets, advance_tick=True)),
                )
            )

            results.append(
                run_case(
                    "ctypes_entity_table_ingest_publish_changed",
                    "ingest native latest-state table, publish changed snapshots into reusable native double buffer",
                    packets,
                    args.repeats,
                    lambda: (
                        lambda stats: (
                            snapshot_buffer.publish_changed(table, clear=True),
                            {
                                **stats["scan"],
                                "callbacks": 0,
                            },
                        )[1]
                    )(table.ingest(scanner, packets, advance_tick=True)),
                )
            )

            results.append(
                run_case(
                    "ctypes_snapshot_acquire_copy_release",
                    "publish changed snapshots, acquire latest view, copy to Python tuple, release",
                    packets,
                    args.repeats,
                    lambda: (
                        lambda stats: (
                            snapshot_buffer.publish_changed(table, clear=True),
                            (lambda read: (read.view, read.close()))(snapshot_buffer.acquire_latest()),
                            {
                                **stats["scan"],
                                "callbacks": 0,
                            },
                        )[2]
                    )(table.ingest(scanner, packets, advance_tick=True)),
                )
            )

            results.append(
                run_case(
                    "ctypes_ingest_publish_changed_combined",
                    "single ctypes ABI call: ingest table and publish changed snapshot buffer",
                    packets,
                    args.repeats,
                    lambda: (
                        lambda pair: {
                            **pair[1]["scan"],
                            "callbacks": 0,
                        }
                    )(snapshot_buffer.ingest_and_publish_changed(table, scanner, packets, return_stats=True)),
                )
            )
        finally:
            snapshot_buffer.close()
            table.close()

        scanner.only_entity_force_ids([1, 2]).set_sample(100).set_entity_state_fields(native.FASTDIS_ES_FIELD_POSE)
        callback_counter["count"] = 0
        results.append(
            run_case(
                "ctypes_scanner_chained_filters_callback",
                "chained filter API: force IDs [1,2] + sample 1/100 + Python callback",
                packets,
                args.repeats,
                lambda: (
                    lambda before: {
                        **scanner.scan_entity_state_many(packets, entity_cb, return_stats=True),
                        "callbacks": callback_counter["count"] - before,
                    }
                )(callback_counter["count"]),
            )
        )
    finally:
        scanner.close()

    if args.format == "table":
        if args.out:
            with args.out.open("w") as fh:
                old_stdout = sys.stdout
                try:
                    sys.stdout = fh
                    write_table(results)
                finally:
                    sys.stdout = old_stdout
        else:
            write_table(results)
    elif args.format == "csv":
        write_csv(args.out, results)
    else:
        write_json(args.out, lib, args, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
