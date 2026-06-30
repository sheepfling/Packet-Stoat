#!/usr/bin/env python3
"""Render storefront-ready benchmark charts from audited report artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build" / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


DEFAULT_MATRIX = ROOT / "artifacts" / "reports" / "benchmark_matrix" / "benchmark_matrix.json"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "engine_benchmarks"
DEFAULT_HEAD_TO_HEAD = ROOT / "artifacts" / "reports" / "engine_head_to_head" / "unity_vs_grill.json"
DEFAULT_OUT_DIR = ROOT / "build" / "storefront" / "benchmark_charts"

SURFACE_ORDER = ("native", "c", "cpp", "python_ctypes", "godot", "unity", "unreal", "grill_unity")
SURFACE_LABELS = {
    "native": "Native",
    "c": "C",
    "cpp": "C++",
    "python_ctypes": "Python ctypes",
    "godot": "Godot",
    "unity": "Unity",
    "unreal": "Unreal",
    "grill_unity": "GRILL Unity",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--unity-head-to-head", type=Path, default=DEFAULT_HEAD_TO_HEAD)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def report_path_for(report_dir: Path, surface: str) -> Path:
    return report_dir / f"{surface}_engine_benchmark_report.json"


def best_measured_packets_per_sec(surface: str, report_dir: Path) -> dict[str, Any] | None:
    path = report_path_for(report_dir, surface)
    if not path.exists():
        return None
    payload = load_json(path)
    best: dict[str, Any] | None = None
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        metrics = row.get("metrics")
        if not isinstance(metrics, dict):
            continue
        packets_per_sec = metrics.get("packets_per_sec")
        if not isinstance(packets_per_sec, (int, float)):
            continue
        candidate = {
            "surface": surface,
            "label": SURFACE_LABELS.get(surface, surface),
            "scenario": row.get("scenario", "unknown"),
            "packets_per_sec": float(packets_per_sec),
        }
        if best is None or candidate["packets_per_sec"] > best["packets_per_sec"]:
            best = candidate
    return best


def collect_measured_throughput(report_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for surface in SURFACE_ORDER:
        row = best_measured_packets_per_sec(surface, report_dir)
        if row is not None:
            rows.append(row)
    return rows


def collect_surface_coverage(matrix_path: Path) -> list[dict[str, Any]]:
    payload = load_json(matrix_path)
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list):
        return []
    rows: list[dict[str, Any]] = []
    for row in surfaces:
        if not isinstance(row, dict):
            continue
        surface = str(row.get("surface", "unknown"))
        rows.append(
            {
                "surface": surface,
                "label": SURFACE_LABELS.get(surface, surface),
                "row_count": int(row.get("row_count", 0)),
                "runtime_metric_rows": int(row.get("runtime_metric_rows", 0)),
                "truth_rows": int(row.get("truth_rows", 0)),
            }
        )
    rows.sort(key=lambda item: SURFACE_ORDER.index(item["surface"]) if item["surface"] in SURFACE_ORDER else 999)
    return rows


def extract_unity_head_to_head(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = load_json(path)
    comparison = payload.get("comparison")
    if not isinstance(comparison, dict):
        return None
    rows = comparison.get("rows")
    if not isinstance(rows, list) or not rows:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        return None
    metrics = row.get("metrics")
    if not isinstance(metrics, dict):
        return None
    packets = metrics.get("packets_per_sec", {})
    apply_ms = metrics.get("main_thread_apply_ms", {})
    gc_bytes = metrics.get("steady_state_gc_bytes", {})
    return {
        "scenario": row.get("scenario", "unknown"),
        "left_label": comparison.get("left_label", "FastDIS Unity"),
        "right_label": comparison.get("right_label", "GRILL Unity"),
        "packets_per_sec": {
            "left": packets.get("left"),
            "right": packets.get("right"),
            "ratio": packets.get("ratio"),
        },
        "main_thread_apply_ms": {
            "left": apply_ms.get("left"),
            "right": apply_ms.get("right"),
            "ratio": apply_ms.get("ratio"),
        },
        "steady_state_gc_bytes": {
            "left": gc_bytes.get("left"),
            "right": gc_bytes.get("right"),
            "ratio": gc_bytes.get("ratio"),
        },
        "same_host": bool(comparison.get("same_host")),
        "status": str(comparison.get("status", payload.get("status", "unknown"))),
    }


def human_rate(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M pkt/s"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k pkt/s"
    return f"{value:.0f} pkt/s"


def render_throughput_chart(rows: list[dict[str, Any]], out_path: Path) -> None:
    labels = [row["label"] for row in rows]
    values = [row["packets_per_sec"] for row in rows]
    scenarios = [row["scenario"] for row in rows]

    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor("#0b1d25")
    ax.set_facecolor("#12303a")
    bars = ax.bar(labels, values, color="#8ad7d0")
    ax.set_yscale("log")
    ax.set_ylabel("Packets / sec (log scale)", color="#f1f6e9")
    ax.set_title("Measured FastDIS Throughput By Surface", fontsize=26, color="#f1f6e9", pad=18)
    ax.tick_params(axis="x", colors="#f1f6e9", rotation=20)
    ax.tick_params(axis="y", colors="#d9e7df")
    ax.grid(axis="y", alpha=0.22, color="#9cbcaf")
    for spine in ax.spines.values():
        spine.set_color("#456d77")

    for bar, scenario, value in zip(bars, scenarios, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.15,
            f"{human_rate(value)}\n{scenario}",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#f1f6e9",
        )

    fig.text(
        0.02,
        0.03,
        "Measured rows only. Surfaces without packets/sec metrics are intentionally omitted rather than implied to be slower.",
        fontsize=12,
        color="#c9ddd2",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_coverage_chart(rows: list[dict[str, Any]], out_path: Path) -> None:
    labels = [row["label"] for row in rows]
    row_counts = [row["row_count"] for row in rows]
    runtime_rows = [row["runtime_metric_rows"] for row in rows]
    truth_rows = [row["truth_rows"] for row in rows]
    x = range(len(rows))

    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor("#0b1d25")
    ax.set_facecolor("#12303a")
    width = 0.24
    ax.bar([idx - width for idx in x], row_counts, width=width, label="report rows", color="#8ad7d0")
    ax.bar(x, runtime_rows, width=width, label="runtime metric rows", color="#d2f36b")
    ax.bar([idx + width for idx in x], truth_rows, width=width, label="truth rows", color="#f3a16b")
    ax.set_title("Benchmark Coverage By Surface", fontsize=26, color="#f1f6e9", pad=18)
    ax.set_ylabel("Row count", color="#f1f6e9")
    ax.set_xticks(list(x), labels, rotation=20)
    ax.tick_params(axis="x", colors="#f1f6e9")
    ax.tick_params(axis="y", colors="#d9e7df")
    ax.grid(axis="y", alpha=0.22, color="#9cbcaf")
    ax.legend(facecolor="#12303a", edgecolor="#456d77", labelcolor="#f1f6e9")
    for spine in ax.spines.values():
        spine.set_color("#456d77")

    fig.text(
        0.02,
        0.03,
        "This chart shows proof maturity, not speed. A surface can be well-verified even when full runtime timings are still sparse.",
        fontsize=12,
        color="#c9ddd2",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_unity_head_to_head_chart(summary: dict[str, Any], out_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor("#241413")
    categories = (
        ("packets_per_sec", "Packets / sec", "#8ad7d0"),
        ("main_thread_apply_ms", "Main-thread apply ms", "#d2f36b"),
        ("steady_state_gc_bytes", "Steady-state GC bytes", "#f3a16b"),
    )
    labels = [summary["left_label"], summary["right_label"]]

    for ax, (metric_key, title, color) in zip(axes, categories):
        ax.set_facecolor("#331d1a")
        values = [summary[metric_key]["left"], summary[metric_key]["right"]]
        numeric = [float(value) if isinstance(value, (int, float)) else 0.0 for value in values]
        bars = ax.bar(labels, numeric, color=color)
        ax.set_title(title, color="#f9efe9", fontsize=16, pad=12)
        ax.tick_params(axis="x", colors="#f9efe9", rotation=15)
        ax.tick_params(axis="y", colors="#f0d2c7")
        ax.grid(axis="y", alpha=0.18, color="#d8aa9a")
        for spine in ax.spines.values():
            spine.set_color("#8d5b51")
        for bar, value in zip(bars, values):
            text = "n/a" if value is None else f"{value:,.3f}" if isinstance(value, float) else str(value)
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02 if bar.get_height() else 0.02, text, ha="center", va="bottom", fontsize=11, color="#f9efe9")

    ratio = summary["packets_per_sec"]["ratio"]
    ratio_text = f"{ratio:.1f}x packets/sec advantage" if isinstance(ratio, (int, float)) else "packets/sec ratio unavailable"
    fig.suptitle(f"Unity Same-Host: FastDIS vs GRILL ({summary['scenario']})", fontsize=26, color="#f9efe9", y=0.97)
    fig.text(0.02, 0.05, f"Same-host evidence: {summary['same_host']} | status: {summary['status']} | {ratio_text}", fontsize=12, color="#e4c6bd")
    fig.text(0.02, 0.025, "Only comparable metrics from the audited same-host head-to-head report are shown.", fontsize=12, color="#e4c6bd")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.08, 1, 0.93))
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def build_manifest(
    throughput_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    unity_head_to_head: dict[str, Any] | None,
    out_dir: Path,
) -> dict[str, Any]:
    return {
        "schema": "fastdis.storefront_benchmark_chart_manifest.v1",
        "charts": [
            {
                "name": "measured_throughput_by_surface",
                "path": str(out_dir / "measured_throughput_by_surface_1920x1080.png"),
                "surface_count": len(throughput_rows),
                "claim_boundary": "Measured rows only. Missing throughput metrics are omitted.",
            },
            {
                "name": "benchmark_coverage_by_surface",
                "path": str(out_dir / "benchmark_coverage_by_surface_1920x1080.png"),
                "surface_count": len(coverage_rows),
                "claim_boundary": "Coverage counts express proof maturity, not direct speed.",
            },
            {
                "name": "unity_vs_grill_same_host",
                "path": str(out_dir / "unity_vs_grill_same_host_1920x1080.png"),
                "present": unity_head_to_head is not None,
                "claim_boundary": "Direct competitor claims require same-host comparable metrics.",
            },
        ],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    throughput_rows = collect_measured_throughput(args.report_dir)
    coverage_rows = collect_surface_coverage(args.benchmark_matrix)
    unity_head_to_head = extract_unity_head_to_head(args.unity_head_to_head)

    out_dir = args.out_dir
    render_throughput_chart(throughput_rows, out_dir / "measured_throughput_by_surface_1920x1080.png")
    render_coverage_chart(coverage_rows, out_dir / "benchmark_coverage_by_surface_1920x1080.png")
    if unity_head_to_head is not None:
        render_unity_head_to_head_chart(unity_head_to_head, out_dir / "unity_vs_grill_same_host_1920x1080.png")

    manifest = build_manifest(throughput_rows, coverage_rows, unity_head_to_head, out_dir)
    manifest_path = out_dir / "benchmark_chart_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
