#!/usr/bin/env python3
"""Create human-readable and machine-readable benchmark reports from fastdis JSON outputs.

Typical use:

    python tools/run_benchmarks.py --format json --out-dir benchmark_results
    python tools/summarize_benchmarks.py \
      --native benchmark_results/native.json \
      --ctypes benchmark_results/ctypes.json \
      --out benchmark_results/summary.md \
      --json-out benchmark_results/qualification.json

The native benchmark measures the DLL/shared-object hot path. The ctypes
benchmark intentionally includes Python packet-view setup and Python callback
costs, so treat it as interoperability overhead rather than core throughput.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


def _load(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text())


def _native_mpps(row: dict[str, Any]) -> float:
    return float(row.get("best_mpps", row.get("avg_mpps", 0.0)))


def _ctypes_mpps(row: dict[str, Any]) -> float:
    return float(row.get("best_mpps", row.get("mega_packets_per_sec", 0.0)))


def _avg_mpps(row: dict[str, Any], fallback: Callable[[dict[str, Any]], float]) -> float:
    return float(row.get("avg_mpps", fallback(row)))


def _by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("case", "")): row for row in rows}


def _fmt_ratio(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}x"


def _fmt_ms(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "—"


def _fmt_float(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "—"


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "—"


def _rel(row: dict[str, Any], baseline_mpps: float, mpps_fn: Callable[[dict[str, Any]], float]) -> str:
    if baseline_mpps <= 0:
        return "—"
    return _fmt_ratio(mpps_fn(row) / baseline_mpps)


def _markdown_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    out = []
    header = rows[0]
    out.append("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(header)) + " |")
    out.append("| " + " | ".join("-" * widths[i] for i in range(len(widths))) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |")
    return out


def _ratio(cases: dict[str, dict[str, Any]], a: str, b: str, mpps_fn: Callable[[dict[str, Any]], float]) -> float | None:
    if a not in cases or b not in cases:
        return None
    denom = mpps_fn(cases[b])
    return mpps_fn(cases[a]) / denom if denom > 0 else None


def _case_metrics(row: dict[str, Any], mpps_fn: Callable[[dict[str, Any]], float]) -> dict[str, Any]:
    return {
        "case": str(row.get("case", "")),
        "packets": int(row.get("packets", 0)),
        "best_mpps": mpps_fn(row),
        "avg_mpps": _avg_mpps(row, mpps_fn),
        "best_ms": float(row.get("best_ms", 0.0)),
        "avg_ms": float(row.get("avg_ms", 0.0)),
        "p50_ms": float(row.get("p50_ms", row.get("avg_ms", 0.0))),
        "p95_ms": float(row.get("p95_ms", row.get("avg_ms", 0.0))),
        "p99_ms": float(row.get("p99_ms", row.get("avg_ms", 0.0))),
        "worst_ms": float(row.get("worst_ms", row.get("avg_ms", 0.0))),
        "accepted": int(row.get("accepted", 0)),
        "emitted": int(row.get("emitted", 0)),
        "malformed": int(row.get("malformed", 0)),
        "callbacks": int(row.get("callbacks", 0)),
        "notes": str(row.get("notes", "")),
    }


def _extract_cases(
    cases: dict[str, dict[str, Any]],
    names: list[tuple[str, str]],
    mpps_fn: Callable[[dict[str, Any]], float],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, case_name in names:
        row = cases.get(case_name)
        if row is not None:
            out[key] = _case_metrics(row, mpps_fn)
    return out


def _native_section(payload: dict[str, Any]) -> list[str]:
    rows = list(payload.get("results", []))
    cases = _by_case(rows)
    baseline = _native_mpps(cases.get("header_all_no_callback", {}))
    out = [
        "## Native shared-library benchmark",
        "",
        f"ABI: `{payload.get('abi', 'unknown')}`; library version: `{payload.get('version', 'unknown')}`.",
        "",
    ]
    table = [[
        "case",
        "best Mpps",
        "avg Mpps",
        "p50 ms",
        "p95 ms",
        "p99 ms",
        "vs header-only",
        "accepted",
        "emitted",
        "malformed",
        "notes",
    ]]
    for row in rows:
        table.append([
            str(row.get("case", "")),
            _fmt_float(_native_mpps(row), 2),
            _fmt_float(_avg_mpps(row, _native_mpps), 2),
            _fmt_ms(row.get("p50_ms", row.get("avg_ms", 0.0))),
            _fmt_ms(row.get("p95_ms", row.get("avg_ms", 0.0))),
            _fmt_ms(row.get("p99_ms", row.get("avg_ms", 0.0))),
            _rel(row, baseline, _native_mpps),
            _fmt_int(row.get("accepted")),
            _fmt_int(row.get("emitted")),
            _fmt_int(row.get("malformed")),
            str(row.get("notes", "")),
        ])
    out.extend(_markdown_table(table))
    out.append("")
    out.extend([
        "### Native readout",
        "",
        f"- Header callback-every-packet throughput vs header-only: `{_fmt_ratio(_ratio(cases, 'header_all_callback_every', 'header_all_no_callback', _native_mpps))}`.",
        f"- Header downsample-before-callback throughput vs callback-every-packet: `{_fmt_ratio(_ratio(cases, 'header_downsample_1pct_cb', 'header_all_callback_every', _native_mpps))}`.",
        f"- Entity pose-only decode vs full fixed-prefix decode: `{_fmt_ratio(_ratio(cases, 'entity_pose_no_callback', 'entity_all_no_callback', _native_mpps))}`.",
        f"- Reused scanner pose decode vs one-shot pose decode: `{_fmt_ratio(_ratio(cases, 'scanner_reuse_pose_no_callback', 'entity_pose_no_callback', _native_mpps))}`.",
        f"- Native entity-ID allowlist throughput vs routing-only decode: `{_fmt_ratio(_ratio(cases, 'scanner_entity_id_allow_32', 'entity_routing_no_callback', _native_mpps))}`.",
        f"- Callback-free pose batch throughput vs pose callback-every-packet: `{_fmt_ratio(_ratio(cases, 'entity_pose_to_batch', 'entity_pose_callback_every', _native_mpps))}`.",
        f"- Compact transform batch throughput vs pose batch throughput: `{_fmt_ratio(_ratio(cases, 'entity_transform_to_batch', 'entity_pose_to_batch', _native_mpps))}`.",
        f"- Entity-table ingest + changed publish vs ingest-only: `{_fmt_ratio(_ratio(cases, 'entity_table_ingest_publish_changed', 'entity_table_ingest_latest', _native_mpps))}`.",
        f"- Combined ingest+publish ABI call vs separate ingest+publish: `{_fmt_ratio(_ratio(cases, 'entity_table_ingest_publish_combined', 'entity_table_ingest_publish_changed', _native_mpps))}`.",
        f"- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `{_fmt_ratio(_ratio(cases, 'entity_snapshot_publish_all', 'entity_snapshot_publish_changed_dirty', _native_mpps))}`.",
        f"- Triple-slot delayed reader vs double-slot delayed reader: `{_fmt_ratio(_ratio(cases, 'snapshot_delayed_reader_triple', 'snapshot_delayed_reader_double', _native_mpps))}`.",
        f"- Frame transform on vs frame transform off: `{_fmt_ratio(_ratio(cases, 'frame_transform_on', 'frame_transform_off', _native_mpps))}`.",
        "",
    ])
    return out


def _ctypes_section(payload: dict[str, Any]) -> list[str]:
    rows = list(payload.get("results", []))
    cases = _by_case(rows)
    baseline = _ctypes_mpps(cases.get("ctypes_header_no_callback", {}))
    out = [
        "## Python ctypes benchmark",
        "",
        f"ABI: `{payload.get('abi_version', 'unknown')}`; library version: `{payload.get('library_version', 'unknown')}`.",
        "",
    ]
    table = [[
        "case",
        "best Mpps",
        "avg Mpps",
        "p50 ms",
        "p95 ms",
        "p99 ms",
        "vs ctypes header-only",
        "accepted",
        "emitted",
        "callbacks",
        "notes",
    ]]
    for row in rows:
        table.append([
            str(row.get("case", "")),
            _fmt_float(_ctypes_mpps(row), 3),
            _fmt_float(_avg_mpps(row, _ctypes_mpps), 3),
            _fmt_ms(row.get("p50_ms", row.get("avg_ms", 0.0))),
            _fmt_ms(row.get("p95_ms", row.get("avg_ms", 0.0))),
            _fmt_ms(row.get("p99_ms", row.get("avg_ms", 0.0))),
            _rel(row, baseline, _ctypes_mpps),
            _fmt_int(row.get("accepted")),
            _fmt_int(row.get("emitted")),
            _fmt_int(row.get("callbacks")),
            str(row.get("notes", "")),
        ])
    out.extend(_markdown_table(table))
    out.append("")
    out.extend([
        "### ctypes readout",
        "",
        f"- Python callback-every-packet throughput vs ctypes header-only: `{_fmt_ratio(_ratio(cases, 'ctypes_header_callback_every_packet', 'ctypes_header_no_callback', _ctypes_mpps))}`.",
        f"- C-side downsample before Python callback vs callback-every-packet: `{_fmt_ratio(_ratio(cases, 'ctypes_header_callback_sample_100', 'ctypes_header_callback_every_packet', _ctypes_mpps))}`.",
        f"- ctypes pose-only Entity State decode vs full fixed-prefix decode: `{_fmt_ratio(_ratio(cases, 'ctypes_entity_pose_no_callback', 'ctypes_entity_all_no_callback', _ctypes_mpps))}`.",
        f"- chained filters + downsample callback vs callback-every-packet: `{_fmt_ratio(_ratio(cases, 'ctypes_scanner_chained_filters_callback', 'ctypes_header_callback_every_packet', _ctypes_mpps))}`.",
        f"- ctypes transform batch vs ctypes pose callback-free scan: `{_fmt_ratio(_ratio(cases, 'ctypes_entity_transform_to_batch', 'ctypes_entity_pose_no_callback', _ctypes_mpps))}`.",
        f"- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `{_fmt_ratio(_ratio(cases, 'ctypes_entity_table_ingest_publish_changed', 'ctypes_entity_table_ingest_latest', _ctypes_mpps))}`.",
        f"- ctypes combined ingest+publish vs separate ingest+publish: `{_fmt_ratio(_ratio(cases, 'ctypes_ingest_publish_changed_combined', 'ctypes_entity_table_ingest_publish_changed', _ctypes_mpps))}`.",
        "",
    ])
    return out


def build_qualification(native_payload: dict[str, Any] | None, ctypes_payload: dict[str, Any] | None) -> dict[str, Any]:
    native_rows = [] if native_payload is None else list(native_payload.get("results", []))
    ctypes_rows = [] if ctypes_payload is None else list(ctypes_payload.get("results", []))
    native_cases = _by_case(native_rows)
    ctypes_cases = _by_case(ctypes_rows)

    qualification: dict[str, Any] = {
        "schema_version": 1,
        "summary": {
            "native_case_count": len(native_rows),
            "ctypes_case_count": len(ctypes_rows),
            "native_has_latency_quantiles": all("p95_ms" in row for row in native_rows) if native_rows else False,
            "ctypes_has_latency_quantiles": all("p95_ms" in row for row in ctypes_rows) if ctypes_rows else False,
        },
        "native": {
            "abi": None if native_payload is None else native_payload.get("abi"),
            "version": None if native_payload is None else native_payload.get("version"),
            "core_cases": _extract_cases(
                native_cases,
                [
                    ("header_scan", "header_all_no_callback"),
                    ("mixed_noise", "mixed_pdu_noise"),
                    ("entity_pose", "entity_pose_no_callback"),
                    ("entity_transform_batch", "entity_transform_to_batch"),
                    ("table_ingest_latest", "entity_table_ingest_latest"),
                    ("publish_changed_dirty", "entity_snapshot_publish_changed_dirty"),
                    ("publish_all", "entity_snapshot_publish_all"),
                    ("ingest_publish_changed", "entity_table_ingest_publish_changed"),
                    ("snapshot_delayed_reader_double", "snapshot_delayed_reader_double"),
                    ("snapshot_delayed_reader_triple", "snapshot_delayed_reader_triple"),
                    ("frame_transform_off", "frame_transform_off"),
                    ("frame_transform_on", "frame_transform_on"),
                ],
                _native_mpps,
            ),
            "ratios": {
                "callback_vs_header_only": _ratio(native_cases, "header_all_callback_every", "header_all_no_callback", _native_mpps),
                "downsample_vs_callback_every": _ratio(native_cases, "header_downsample_1pct_cb", "header_all_callback_every", _native_mpps),
                "transform_batch_vs_pose_batch": _ratio(native_cases, "entity_transform_to_batch", "entity_pose_to_batch", _native_mpps),
                "publish_changed_vs_ingest_latest": _ratio(native_cases, "entity_table_ingest_publish_changed", "entity_table_ingest_latest", _native_mpps),
                "frame_transform_on_vs_off": _ratio(native_cases, "frame_transform_on", "frame_transform_off", _native_mpps),
                "triple_vs_double_delayed_reader": _ratio(native_cases, "snapshot_delayed_reader_triple", "snapshot_delayed_reader_double", _native_mpps),
            },
        },
        "ctypes": {
            "abi": None if ctypes_payload is None else ctypes_payload.get("abi_version"),
            "version": None if ctypes_payload is None else ctypes_payload.get("library_version"),
            "core_cases": _extract_cases(
                ctypes_cases,
                [
                    ("header_scan", "ctypes_header_no_callback"),
                    ("header_callback_every", "ctypes_header_callback_every_packet"),
                    ("entity_pose", "ctypes_entity_pose_no_callback"),
                    ("entity_transform_batch", "ctypes_entity_transform_to_batch"),
                    ("table_ingest_latest", "ctypes_entity_table_ingest_latest"),
                    ("table_ingest_publish_changed", "ctypes_entity_table_ingest_publish_changed"),
                    ("snapshot_copy_release", "ctypes_snapshot_acquire_copy_release"),
                    ("combined_ingest_publish", "ctypes_ingest_publish_changed_combined"),
                ],
                _ctypes_mpps,
            ),
            "ratios": {
                "callback_vs_header_only": _ratio(ctypes_cases, "ctypes_header_callback_every_packet", "ctypes_header_no_callback", _ctypes_mpps),
                "downsample_vs_callback_every": _ratio(ctypes_cases, "ctypes_header_callback_sample_100", "ctypes_header_callback_every_packet", _ctypes_mpps),
                "transform_batch_vs_pose_scan": _ratio(ctypes_cases, "ctypes_entity_transform_to_batch", "ctypes_entity_pose_no_callback", _ctypes_mpps),
                "publish_changed_vs_ingest_latest": _ratio(ctypes_cases, "ctypes_entity_table_ingest_publish_changed", "ctypes_entity_table_ingest_latest", _ctypes_mpps),
                "combined_vs_separate": _ratio(ctypes_cases, "ctypes_ingest_publish_changed_combined", "ctypes_entity_table_ingest_publish_changed", _ctypes_mpps),
            },
        },
        "allocation_expectations": [
            {
                "scope": "native header/entity scan cases",
                "expectation": "Hot-path scanning should remain allocation-free after packet buffers, config, and scanners are constructed.",
            },
            {
                "scope": "native batch output and frame-transform cases",
                "expectation": "Output uses caller-owned or pre-sized native buffers; overflow should be reported without heap growth in the scan loop.",
            },
            {
                "scope": "entity table and snapshot publication",
                "expectation": "Allocation is bounded by create-time capacity and snapshot slot count; publish/acquire/release should not resize at runtime.",
            },
            {
                "scope": "Python ctypes cases",
                "expectation": "Python-facing runs include wrapper and conversion overhead, so they are interoperability measurements rather than pure hot-path allocation proofs.",
            },
        ],
        "regression_guard_cases": {
            "native": [
                "header_all_no_callback",
                "entity_pose_no_callback",
                "entity_transform_to_batch",
                "entity_table_ingest_latest",
                "entity_table_ingest_publish_changed",
                "frame_transform_off",
                "frame_transform_on",
            ],
            "ctypes": [
                "ctypes_header_no_callback",
                "ctypes_entity_pose_no_callback",
                "ctypes_entity_transform_to_batch",
                "ctypes_entity_table_ingest_latest",
                "ctypes_entity_table_ingest_publish_changed",
            ],
        },
    }
    return qualification


def render(native_payload: dict[str, Any] | None, ctypes_payload: dict[str, Any] | None) -> str:
    qualification = build_qualification(native_payload, ctypes_payload)
    out = [
        "# fastdis benchmark report",
        "",
        "This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters, latest-state tables, snapshot publication, and engine-facing transform conversion.",
        "",
        "> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.",
        "",
        "## Qualification summary",
        "",
        f"- Native cases reported: `{qualification['summary']['native_case_count']}`; latency quantiles present: `{qualification['summary']['native_has_latency_quantiles']}`.",
        f"- ctypes cases reported: `{qualification['summary']['ctypes_case_count']}`; latency quantiles present: `{qualification['summary']['ctypes_has_latency_quantiles']}`.",
        "- Native hot-path expectation: packet scanning should stay allocation-free once scanners and buffers are created.",
        "- Snapshot/table expectation: runtime cost should be bounded by configured capacities and slot counts rather than hidden growth.",
        "- Python ctypes results intentionally include wrapper overhead; treat them as host-binding qualification rather than the core DLL ceiling.",
        "",
    ]
    if native_payload is not None:
        out.extend(_native_section(native_payload))
    if ctypes_payload is not None:
        out.extend(_ctypes_section(ctypes_payload))
    out.extend([
        "## Allocation expectations",
        "",
    ])
    for item in qualification["allocation_expectations"]:
        out.append(f"- `{item['scope']}`: {item['expectation']}")
    out.extend([
        "",
        "## Practical conclusions to look for",
        "",
        "- If callback-every-packet is much slower than no-callback scanning, move more filtering/downsampling into C before the callback.",
        "- If pose-only and full-prefix Entity State decode are close, memory/cache effects may dominate and field masks matter less for your traffic.",
        "- If ctypes is far slower than native, that is expected; Unreal/Godot should call the DLL directly, while Python should batch large packet groups.",
        "- If combined ingest+publish is not meaningfully faster than separate calls, keep the separate calls for clearer engine integration unless your FFI boundary is expensive.",
        "- If entity-ID allowlists are costly at large set sizes, the next optimization is a sorted/vectorized set or fixed-domain bitmap for known site/application pairs.",
        "",
    ])
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, help="native benchmark JSON output")
    parser.add_argument("--ctypes", type=Path, help="ctypes benchmark JSON output")
    parser.add_argument("--out", type=Path, help="write Markdown report here")
    parser.add_argument("--json-out", type=Path, help="write qualification JSON report here")
    args = parser.parse_args(argv)
    if args.native is None and args.ctypes is None:
        parser.error("provide --native, --ctypes, or both")

    native_payload = _load(args.native)
    ctypes_payload = _load(args.ctypes)
    text = render(native_payload, ctypes_payload)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    else:
        print(text)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(build_qualification(native_payload, ctypes_payload), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
