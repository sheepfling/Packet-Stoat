#!/usr/bin/env python3
"""Benchmark FastDIS Python ctypes against OpenDIS Python on shared raw fixtures."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import sys
import time
from typing import Any

from report_envelope import write_json_report

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import fastdis.native as native


DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "python_opendis_benchmark"


def load_open_dis(open_dis_root: Path):
    if str(open_dis_root) not in sys.path:
        sys.path.insert(0, str(open_dis_root))
    from opendis.PduFactory import createPdu  # type: ignore

    return createPdu


def maybe_git_rev(path: Path) -> str | None:
    head = path / ".git"
    if not head.exists():
        return None
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def resolve_fixture_path(open_dis_root: Path, explicit_fixture: Path | None) -> Path:
    if explicit_fixture is not None:
        return explicit_fixture
    tests_dir = open_dis_root / "tests"
    preferred = sorted(tests_dir.glob("EntityStatePdu*.raw"))
    if preferred:
        return preferred[0]
    fallback = sorted(tests_dir.glob("*.raw"))
    if fallback:
        return fallback[0]
    return tests_dir / "EntityStatePdu.raw"


def resolve_fixture_paths(open_dis_root: Path, explicit_fixture: Path | None) -> list[Path]:
    if explicit_fixture is not None:
        return [explicit_fixture]
    tests_dir = open_dis_root / "tests"
    fixtures = sorted(tests_dir.glob("*.raw"))
    if fixtures:
        return fixtures
    return [tests_dir / "EntityStatePdu.raw"]


def build_packet_replay(fixtures: Sequence[Path], packets: int) -> list[bytes]:
    packets = max(1, packets)
    fixture_bytes = [path.read_bytes() for path in fixtures]
    if not fixture_bytes:
        return []
    return [fixture_bytes[index % len(fixture_bytes)] for index in range(packets)]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    clamped = max(0.0, min(100.0, pct))
    position = (clamped / 100.0) * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def summarize_rounds(round_seconds: list[float], parsed_packets: int, *, rounds: int, packets_per_round: int) -> dict[str, Any]:
    total_seconds = sum(round_seconds)
    avg_seconds = total_seconds / rounds if rounds > 0 else 0.0
    best_seconds = min(round_seconds) if round_seconds else 0.0
    round_ms = [seconds * 1000.0 for seconds in round_seconds]
    packets_per_sec = (parsed_packets / total_seconds) if total_seconds > 0 else 0.0
    return {
        "rounds": rounds,
        "packets_per_round": packets_per_round,
        "parsed_packets": parsed_packets,
        "total_seconds": total_seconds,
        "avg_ms": avg_seconds * 1000.0,
        "best_ms": best_seconds * 1000.0,
        "p50_ms": percentile(round_ms, 50.0),
        "p95_ms": percentile(round_ms, 95.0),
        "p99_ms": percentile(round_ms, 99.0),
        "worst_ms": max(round_ms) if round_ms else 0.0,
        "packets_per_sec": packets_per_sec,
        "mpps": packets_per_sec / 1_000_000.0,
    }


def run_fastdis_header_benchmark(lib: native.NativeFastDis, packets: list[bytes], rounds: int) -> dict[str, Any]:
    round_seconds: list[float] = []
    aggregate = {"seen": 0, "parsed": 0, "accepted": 0, "malformed": 0}
    for _ in range(rounds):
        started = time.perf_counter()
        stats = lib.scan_many(packets, None, return_stats=True)
        round_seconds.append(time.perf_counter() - started)
        aggregate["seen"] += int(stats.get("seen", len(packets)))
        aggregate["parsed"] += int(stats.get("accepted", 0)) + int(stats.get("rejected", 0))
        aggregate["accepted"] += int(stats.get("accepted", 0))
        aggregate["malformed"] += int(stats.get("malformed", 0))
    return {
        **summarize_rounds(round_seconds, aggregate["seen"], rounds=rounds, packets_per_round=len(packets)),
        "stats": aggregate,
        "measurement_meaning": "FastDIS native scan_many via Python ctypes with no Python callback.",
    }


def run_fastdis_entity_benchmark(lib: native.NativeFastDis, packets: list[bytes], rounds: int) -> dict[str, Any]:
    round_seconds: list[float] = []
    emitted_total = 0

    def on_entity(_entity: native.EntityStatePrefix, _packet: object) -> None:
        return None

    for _ in range(rounds):
        started = time.perf_counter()
        stats = lib.scan_entity_state_many(
            packets,
            on_entity,
            entity_state_fields=native.FASTDIS_ES_FIELD_ALL,
            return_stats=True,
        )
        round_seconds.append(time.perf_counter() - started)
        emitted_total += int(stats.get("emitted", 0))
    return {
        **summarize_rounds(round_seconds, emitted_total, rounds=rounds, packets_per_round=len(packets)),
        "stats": {"emitted": emitted_total},
        "measurement_meaning": "FastDIS Entity State typed-prefix extraction through the Python ctypes bridge.",
    }


def run_open_dis_benchmark(create_pdu, packets: list[bytes], rounds: int, *, extract_entity_fields: bool) -> dict[str, Any]:
    round_seconds: list[float] = []
    parsed_packets = 0
    entity_fields_read = 0
    for _ in range(rounds):
        started = time.perf_counter()
        for packet in packets:
            pdu = create_pdu(packet)
            if pdu is None:
                raise RuntimeError("OpenDIS failed to parse a benchmark fixture packet")
            parsed_packets += 1
            if extract_entity_fields:
                _ = (
                    pdu.entityID.simulationAddress.site,
                    pdu.entityID.simulationAddress.application,
                    pdu.entityID.entityNumber,
                    pdu.entityLocation.x,
                    pdu.entityLocation.y,
                    pdu.entityLocation.z,
                )
                entity_fields_read += 1
        round_seconds.append(time.perf_counter() - started)
    payload = {
        **summarize_rounds(round_seconds, parsed_packets, rounds=rounds, packets_per_round=len(packets)),
        "stats": {
            "parsed": parsed_packets,
            "entity_fields_read": entity_fields_read,
        },
        "measurement_meaning": (
            "OpenDIS Python createPdu full object parse plus selected Entity State field reads."
            if extract_entity_fields
            else "OpenDIS Python createPdu full object parse."
        ),
    }
    return payload


def summarize_comparison(fastdis_result: dict[str, Any], open_dis_result: dict[str, Any]) -> dict[str, Any]:
    fast_pps = float(fastdis_result.get("packets_per_sec", 0.0) or 0.0)
    open_pps = float(open_dis_result.get("packets_per_sec", 0.0) or 0.0)
    ratio = (fast_pps / open_pps) if open_pps > 0 else None
    return {
        "fastdis_packets_per_sec": fast_pps,
        "open_dis_packets_per_sec": open_pps,
        "fastdis_vs_open_dis_speedup": ratio,
        "claim_boundary": (
            "Same-host Python-route comparison on repeated shared raw fixture families. "
            "This is not a full object-model parity claim and should not be generalized beyond the measured scenario."
        ),
    }


def build_report(
    *,
    open_dis_root: Path,
    fixture_path: Path,
    fixture_paths: Sequence[Path],
    lib_path: str | None,
    packets: int,
    rounds: int,
) -> dict[str, Any]:
    packet = fixture_path.read_bytes()
    replay = [packet] * packets
    create_pdu = load_open_dis(open_dis_root)
    lib = native.load_native(lib_path)
    all_header_scenarios: list[dict[str, Any]] = []
    for path in fixture_paths:
        fixture_replay = build_packet_replay([path], packets)
        header_fastdis = run_fastdis_header_benchmark(lib, fixture_replay, rounds)
        header_open_dis = run_open_dis_benchmark(create_pdu, fixture_replay, rounds, extract_entity_fields=False)
        stem = path.stem.replace("-", "_").lower()
        all_header_scenarios.append(
            {
                "scenario": f"{stem}_header_scan",
                "comparison_axis": "python_runtime",
                "fastdis": header_fastdis,
                "open_dis": header_open_dis,
                "comparison": summarize_comparison(header_fastdis, header_open_dis),
            }
        )
    mixed_replay = build_packet_replay(fixture_paths, packets)
    mixed_fastdis = run_fastdis_header_benchmark(lib, mixed_replay, rounds)
    mixed_open_dis = run_open_dis_benchmark(create_pdu, mixed_replay, rounds, extract_entity_fields=False)
    entity_fastdis = run_fastdis_entity_benchmark(lib, replay, rounds)
    entity_open_dis = run_open_dis_benchmark(create_pdu, replay, rounds, extract_entity_fields=True)
    scenarios = [
        *all_header_scenarios,
        {
            "scenario": "mixed_fixture_header_scan",
            "comparison_axis": "python_runtime",
            "fastdis": mixed_fastdis,
            "open_dis": mixed_open_dis,
            "comparison": summarize_comparison(mixed_fastdis, mixed_open_dis),
        },
        {
            "scenario": "entity_state_fixture_entity_extract",
            "comparison_axis": "python_runtime",
            "fastdis": entity_fastdis,
            "open_dis": entity_open_dis,
            "comparison": summarize_comparison(entity_fastdis, entity_open_dis),
        },
    ]
    return {
        "schema": "fastdis.python_opendis_benchmark_report.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "host": {
            "platform": sys.platform,
            "python": sys.version.split()[0],
        },
        "oracle": {
            "name": "open-dis-python",
            "root": str(open_dis_root),
            "git_rev": maybe_git_rev(open_dis_root),
        },
        "fastdis": {
            "library_path": lib.path,
            "abi_version": lib.abi_version(),
            "library_version": lib.version_string(),
        },
        "fixture": {
            "path": str(fixture_path),
            "packet_bytes": len(packet),
            "packets_per_round": packets,
            "rounds": rounds,
            "fixture_count": len(fixture_paths),
            "fixture_names": [path.name for path in fixture_paths],
        },
        "scenarios": scenarios,
        "summary": {
            "scenario_count": len(scenarios),
            "measured_scenarios": len(scenarios),
            "best_speedup": max(
                (
                    row["comparison"]["fastdis_vs_open_dis_speedup"]
                    for row in scenarios
                    if row["comparison"]["fastdis_vs_open_dis_speedup"] is not None
                ),
                default=None,
            ),
            "notes": [
                "OpenDIS is measured here as a pure Python object-model parser oracle.",
                "FastDIS is measured here through the Python ctypes bridge, not as a direct native executable.",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Python vs OpenDIS benchmark",
        "",
        f"- fixture: `{report['fixture']['path']}`",
        f"- fixture_count: `{report['fixture']['fixture_count']}`",
        f"- packets_per_round: `{report['fixture']['packets_per_round']}`",
        f"- rounds: `{report['fixture']['rounds']}`",
        f"- open_dis_root: `{report['oracle']['root']}`",
        "",
    ]
    for scenario in report["scenarios"]:
        comparison = scenario["comparison"]
        lines.extend(
            [
                f"## {scenario['scenario']}",
                "",
                f"- FastDIS packets/sec: `{comparison['fastdis_packets_per_sec']:.2f}`",
                f"- OpenDIS packets/sec: `{comparison['open_dis_packets_per_sec']:.2f}`",
                f"- FastDIS/OpenDIS speedup: `{comparison['fastdis_vs_open_dis_speedup']}`",
                f"- boundary: {comparison['claim_boundary']}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open-dis-root", type=Path, required=True, help="Path to an open-dis-python checkout")
    parser.add_argument("--fixture", type=Path, help="Raw fixture to replay; defaults to open-dis-python/tests/EntityStatePdu.raw")
    parser.add_argument("--lib", help="Path to libfastdis.so/libfastdis.dylib/fastdis.dll")
    parser.add_argument("--packets", type=int, default=50_000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "python_vs_opendis.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "python_vs_opendis.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fixture = resolve_fixture_path(args.open_dis_root, args.fixture)
    fixture_paths = resolve_fixture_paths(args.open_dis_root, args.fixture)
    report = build_report(
        open_dis_root=args.open_dis_root.resolve(),
        fixture_path=fixture.resolve(),
        fixture_paths=[path.resolve() for path in fixture_paths],
        lib_path=args.lib,
        packets=args.packets,
        rounds=args.rounds,
    )
    write_json_report(
        args.json_out,
        report,
        schema="fastdis.python_opendis_benchmark_report.v1",
        producer="tools/run_opendis_python_benchmark.py",
    )
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {args.json_out}")
    print(f"md: {args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
