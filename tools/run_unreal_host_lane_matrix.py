#!/usr/bin/env python3
"""Summarize current Unreal host/platform harness evidence lanes."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import load_local_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports"
DEFAULT_UNREAL_MATRIX = ROOT / "artifacts" / "reports" / "unreal_version_matrix.json"
DEFAULT_LINUX_PROOF = ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_proof.json"
DEFAULT_LINUX_VERIFY = ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_verify.json"
DEFAULT_LINUX_DEMO = ROOT / "verification_reports" / "unreal_fastdis_baseline" / "fastdis_unreal_linux_demo.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for JSON/Markdown reports")
    parser.add_argument("--unreal-matrix", default=str(DEFAULT_UNREAL_MATRIX))
    parser.add_argument("--linux-proof", default=str(DEFAULT_LINUX_PROOF))
    parser.add_argument("--linux-verify", default=str(DEFAULT_LINUX_VERIFY))
    parser.add_argument("--linux-demo", default=str(DEFAULT_LINUX_DEMO))
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def lane_row(lane: str, host_class: str, evidence_path: Path, payload: dict[str, object] | None) -> dict[str, object]:
    exists = payload is not None
    if lane == "mac-host-matrix":
        if not exists:
            status = "missing"
            evidence_kind = "missing"
        else:
            results = payload.get("results")
            ok = isinstance(results, list) and any(
                isinstance(row, dict)
                and row.get("plugin_build", {}).get("status") == "passed"
                and row.get("orientation", {}).get("status") in {"passed", "skipped"}
                and row.get("demo", {}).get("status") in {"passed", "skipped"}
                for row in results
            )
            status = "pass" if ok else "needs-attention"
            evidence_kind = "runtime-matrix"
    else:
        if not exists:
            status = "missing"
            evidence_kind = "missing"
        else:
            status = str(payload.get("status") or "unknown")
            evidence_kind = {
                "package-proof": "package-proof",
                "pass": "runtime-proof",
                "fail": "runtime-proof",
                "blocked-host-platform": "blocked",
                "dry-run": "planned",
            }.get(status, "unknown")
    return {
        "lane": lane,
        "host_class": host_class,
        "path": display_path(evidence_path),
        "present": exists,
        "status": status,
        "evidence_kind": evidence_kind,
    }


def build_report(args: argparse.Namespace) -> dict[str, object]:
    unreal_matrix_path = Path(args.unreal_matrix).expanduser().resolve()
    linux_proof_path = Path(args.linux_proof).expanduser().resolve()
    linux_verify_path = Path(args.linux_verify).expanduser().resolve()
    linux_demo_path = Path(args.linux_demo).expanduser().resolve()

    lanes = [
        lane_row("mac-host-matrix", "macos", unreal_matrix_path, load_json(unreal_matrix_path)),
        lane_row("linux-package-proof", "linux-docker", linux_proof_path, load_json(linux_proof_path)),
        lane_row("linux-verify", "linux-host", linux_verify_path, load_json(linux_verify_path)),
        lane_row("linux-demo", "linux-host", linux_demo_path, load_json(linux_demo_path)),
    ]
    summary = {
        "present_count": sum(1 for lane in lanes if lane["present"]),
        "pass_count": sum(1 for lane in lanes if lane["status"] in {"pass", "package-proof"}),
        "blocked_count": sum(1 for lane in lanes if str(lane["status"]).startswith("blocked")),
        "missing_count": sum(1 for lane in lanes if lane["status"] == "missing"),
    }
    return {
        "schema": "fastdis.unreal_host_lane_matrix.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "summary": summary,
        "lanes": lanes,
        "claim_boundary": (
            "This matrix summarizes current Unreal harness evidence by host class. "
            "It distinguishes macOS live matrix evidence, Linux Docker package proof, "
            "and Linux host live-harness reports without conflating package proof with runtime proof."
        ),
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unreal Host Lane Matrix",
        "",
        f"- present_count: `{report['summary']['present_count']}`",
        f"- pass_count: `{report['summary']['pass_count']}`",
        f"- blocked_count: `{report['summary']['blocked_count']}`",
        f"- missing_count: `{report['summary']['missing_count']}`",
        "",
        report["claim_boundary"],
        "",
        "| Lane | Host Class | Status | Evidence Kind | Path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for lane in report["lanes"]:
        lines.append(
            f"| {lane['lane']} | {lane['host_class']} | {lane['status']} | {lane['evidence_kind']} | `{lane['path']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(args)
    json_path = out_dir / "unreal_host_lane_matrix.json"
    md_path = out_dir / "unreal_host_lane_matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {display_path(json_path)}")
    print(f"Markdown: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
