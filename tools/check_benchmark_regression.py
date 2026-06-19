#!/usr/bin/env python3
"""Fail if selected fastdis benchmark cases regress past a threshold.

Usage:
    python tools/check_benchmark_regression.py baseline.json current.json \
      --max-regression-percent 10

The script accepts either a single benchmark payload with a top-level
`results` list or a combined payload from `tools/run_benchmarks.py` with
`native` and `ctypes` sections.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _row_mpps(row: dict[str, Any]) -> float:
    if "best_mpps" in row:
        return float(row.get("best_mpps", 0.0))
    if "mega_packets_per_sec" in row:
        return float(row.get("mega_packets_per_sec", 0.0))
    return float(row.get("avg_mpps", 0.0))


def _collect_rows(payload: dict[str, Any]) -> dict[str, float]:
    rows: dict[str, float] = {}
    for row in payload.get("results", []):
        case = str(row.get("case", "")).strip()
        if case:
            rows[case] = _row_mpps(row)
    return rows


def _flatten_payload(payload: dict[str, Any]) -> dict[str, float]:
    if "results" in payload:
        return _collect_rows(payload)

    flattened: dict[str, float] = {}
    for lane in ("native", "ctypes"):
        section = payload.get(lane)
        if isinstance(section, dict) and "results" in section:
            for case, value in _collect_rows(section).items():
                flattened[f"{lane}:{case}"] = value
    return flattened


def _resolve_selection(
    baseline: dict[str, float],
    current: dict[str, float],
    requested: list[str],
) -> set[str]:
    overlap = set(baseline) & set(current)
    if not requested:
        return overlap

    selected: set[str] = set()
    for item in requested:
        if item in overlap:
            selected.add(item)
            continue
        native_key = f"native:{item}"
        ctypes_key = f"ctypes:{item}"
        if native_key in overlap:
            selected.add(native_key)
        if ctypes_key in overlap:
            selected.add(ctypes_key)
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--max-regression-percent", type=float, default=10.0)
    parser.add_argument("--only-case", action="append", default=[])
    args = parser.parse_args(argv)

    baseline = _flatten_payload(_load(args.baseline))
    current = _flatten_payload(_load(args.current))

    selected = _resolve_selection(baseline, current, args.only_case)
    if not selected:
        print("No overlapping benchmark cases found.")
        return 2

    failures: list[str] = []
    for case in sorted(selected):
        base = baseline.get(case, 0.0)
        now = current.get(case, 0.0)
        if base <= 0.0 or now <= 0.0:
            continue
        regression_percent = ((base - now) / base) * 100.0
        if regression_percent > args.max_regression_percent:
            failures.append(
                f"{case}: baseline={base:.3f} current={now:.3f} regression={regression_percent:.2f}%"
            )

    if failures:
        print("Benchmark regression check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"Benchmark regression check passed for {len(selected)} cases "
        f"(max allowed regression {args.max_regression_percent:.2f}%)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
