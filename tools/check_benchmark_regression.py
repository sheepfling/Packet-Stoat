#!/usr/bin/env python3
"""Fail if selected fastdis benchmark cases regress past a threshold.

Usage:
    python tools/check_benchmark_regression.py baseline.json current.json \
      --max-regression-percent 10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _collect_cases(payload: dict) -> dict[str, float]:
    rows: dict[str, float] = {}
    for row in payload.get("results", []):
        case = str(row.get("case", ""))
        if not case:
            continue
        if "best_mpps" in row:
            rows[case] = float(row.get("best_mpps", 0.0))
        elif "mega_packets_per_sec" in row:
            rows[case] = float(row.get("mega_packets_per_sec", 0.0))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--max-regression-percent", type=float, default=10.0)
    parser.add_argument("--only-case", action="append", default=[])
    args = parser.parse_args(argv)

    baseline = _collect_cases(_load(args.baseline))
    current = _collect_cases(_load(args.current))

    selected = set(args.only_case) if args.only_case else set(baseline) & set(current)
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
