#!/usr/bin/env python3
"""Create a human-readable benchmark report from fastdis JSON outputs.

Typical use:

    python tools/run_benchmarks.py --format json --out-dir benchmark_results
    python tools/summarize_benchmarks.py \
      --native benchmark_results/native.json \
      --ctypes benchmark_results/ctypes.json \
      --out benchmark_results/summary.md

The native benchmark measures the DLL/shared-object hot path. The ctypes
benchmark intentionally includes Python packet-view setup and Python callback
costs, so treat it as interoperability overhead rather than core throughput.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text())


def _native_mpps(row: dict[str, Any]) -> float:
    return float(row.get("best_mpps", row.get("avg_mpps", 0.0)))


def _ctypes_mpps(row: dict[str, Any]) -> float:
    return float(row.get("mega_packets_per_sec", 0.0))


def _by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("case", "")): row for row in rows}


def _fmt_ratio(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}x"


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "—"


def _rel(row: dict[str, Any], baseline_mpps: float, mpps_fn) -> str:
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
    table = [["case", "best Mpps", "vs header-only", "accepted", "emitted", "malformed", "notes"]]
    for row in rows:
        table.append([
            str(row.get("case", "")),
            f"{_native_mpps(row):.2f}",
            _rel(row, baseline, _native_mpps),
            _fmt_int(row.get("accepted")),
            _fmt_int(row.get("emitted")),
            _fmt_int(row.get("malformed")),
            str(row.get("notes", "")),
        ])
    out.extend(_markdown_table(table))
    out.append("")

    def ratio(a: str, b: str) -> float | None:
        if a not in cases or b not in cases:
            return None
        denom = _native_mpps(cases[b])
        return _native_mpps(cases[a]) / denom if denom > 0 else None

    out.extend([
        "### Native readout",
        "",
        f"- Header callback-every-packet throughput vs header-only: `{_fmt_ratio(ratio('header_all_callback_every', 'header_all_no_callback'))}`.",
        f"- Header downsample-before-callback throughput vs callback-every-packet: `{_fmt_ratio(ratio('header_downsample_1pct_cb', 'header_all_callback_every'))}`.",
        f"- Entity pose-only decode vs full fixed-prefix decode: `{_fmt_ratio(ratio('entity_pose_no_callback', 'entity_all_no_callback'))}`.",
        f"- Reused scanner pose decode vs one-shot pose decode: `{_fmt_ratio(ratio('scanner_reuse_pose_no_callback', 'entity_pose_no_callback'))}`.",
        f"- Native entity-ID allowlist throughput vs routing-only decode: `{_fmt_ratio(ratio('scanner_entity_id_allow_32', 'entity_routing_no_callback'))}`.",
        f"- Callback-free pose batch throughput vs pose callback-every-packet: `{_fmt_ratio(ratio('entity_pose_to_batch', 'entity_pose_callback_every'))}`.",
        f"- Compact transform batch throughput vs pose batch throughput: `{_fmt_ratio(ratio('entity_transform_to_batch', 'entity_pose_to_batch'))}`.",
        f"- Entity-table ingest + changed publish vs ingest-only: `{_fmt_ratio(ratio('entity_table_ingest_publish_changed', 'entity_table_ingest_latest'))}`.",
        f"- Combined ingest+publish ABI call vs separate ingest+publish: `{_fmt_ratio(ratio('entity_table_ingest_publish_combined', 'entity_table_ingest_publish_changed'))}`.",
        f"- Publish-all snapshot buffer vs publish-changed dirty snapshot buffer: `{_fmt_ratio(ratio('entity_snapshot_publish_all', 'entity_snapshot_publish_changed_dirty'))}`.",
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
    table = [["case", "Mpps", "vs ctypes header-only", "accepted", "emitted", "callbacks", "notes"]]
    for row in rows:
        table.append([
            str(row.get("case", "")),
            f"{_ctypes_mpps(row):.3f}",
            _rel(row, baseline, _ctypes_mpps),
            _fmt_int(row.get("accepted")),
            _fmt_int(row.get("emitted")),
            _fmt_int(row.get("callbacks")),
            str(row.get("notes", "")),
        ])
    out.extend(_markdown_table(table))
    out.append("")

    def ratio(a: str, b: str) -> float | None:
        if a not in cases or b not in cases:
            return None
        denom = _ctypes_mpps(cases[b])
        return _ctypes_mpps(cases[a]) / denom if denom > 0 else None

    out.extend([
        "### ctypes readout",
        "",
        f"- Python callback-every-packet throughput vs ctypes header-only: `{_fmt_ratio(ratio('ctypes_header_callback_every_packet', 'ctypes_header_no_callback'))}`.",
        f"- C-side downsample before Python callback vs callback-every-packet: `{_fmt_ratio(ratio('ctypes_header_callback_sample_100', 'ctypes_header_callback_every_packet'))}`.",
        f"- ctypes pose-only Entity State decode vs full fixed-prefix decode: `{_fmt_ratio(ratio('ctypes_entity_pose_no_callback', 'ctypes_entity_all_no_callback'))}`.",
        f"- chained filters + downsample callback vs callback-every-packet: `{_fmt_ratio(ratio('ctypes_scanner_chained_filters_callback', 'ctypes_header_callback_every_packet'))}`.",
        f"- ctypes transform batch vs ctypes pose callback-free scan: `{_fmt_ratio(ratio('ctypes_entity_transform_to_batch', 'ctypes_entity_pose_no_callback'))}`.",
        f"- ctypes table ingest + snapshot-buffer publish vs table ingest-only: `{_fmt_ratio(ratio('ctypes_entity_table_ingest_publish_changed', 'ctypes_entity_table_ingest_latest'))}`.",
        f"- ctypes combined ingest+publish vs separate ingest+publish: `{_fmt_ratio(ratio('ctypes_ingest_publish_changed_combined', 'ctypes_entity_table_ingest_publish_changed'))}`.",
        "",
    ])
    return out


def render(native_payload: dict[str, Any] | None, ctypes_payload: dict[str, Any] | None) -> str:
    out = [
        "# fastdis benchmark report",
        "",
        "This report compares the major choices in the fast path: header-only scanning, callbacks, early rejection, downsampling, Entity State field subscriptions, callback-free batch output, compact transform output, reusable scanners, and native allow/block filters, latest-state tables, and double-buffer snapshot publication.",
        "",
        "> Results are machine- and build-dependent. Use the ratios to decide what to benchmark in your target engine/runtime, not as universal throughput guarantees.",
        "",
    ]
    if native_payload is not None:
        out.extend(_native_section(native_payload))
    if ctypes_payload is not None:
        out.extend(_ctypes_section(ctypes_payload))
    out.extend([
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
    args = parser.parse_args(argv)
    if args.native is None and args.ctypes is None:
        parser.error("provide --native, --ctypes, or both")

    text = render(_load(args.native), _load(args.ctypes))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
