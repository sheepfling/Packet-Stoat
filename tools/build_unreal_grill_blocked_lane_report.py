#!/usr/bin/env python3
"""Summarize a blocked Unreal GRILL lane into a junior-friendly artifact."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_SMOKE = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "ue58_timeout180" / "grill_unreal_source_smoke.json"
DEFAULT_JSON_OUT = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_ue58_blocked.json"
DEFAULT_MD_OUT = ROOT / "artifacts" / "verification_reports" / "unreal_grill_baseline" / "grill_unreal_ue58_blocked.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _error_lines(output: str, needle: str) -> list[str]:
    lines: list[str] = []
    for line in output.splitlines():
        if needle not in line:
            continue
        if "error " not in line and "fatal error" not in line and "undeclared" not in line and "not a member" not in line:
            continue
        lines.append(line.strip())
    return lines


def build_report(source_smoke_path: Path) -> dict[str, Any]:
    payload = load_json(source_smoke_path)
    probe = payload.get("platform_probe") if isinstance(payload.get("platform_probe"), dict) else {}
    output = str(probe.get("output") or "")
    version = str(payload.get("resolved_engine_version") or payload.get("requested_engine_version") or "unknown")
    cesium_errors = _error_lines(output, "Cesium")
    lowentry_errors = _error_lines(output, "LowEntry")
    blockers: list[str] = []
    if cesium_errors:
        blockers.append("Cesium sample plugin is not forward-compatible with UE 5.8 on this route")
    if lowentry_errors:
        blockers.append("LowEntry sample plugin is not forward-compatible with UE 5.8 on this route")
    if not blockers:
        blockers.append("UE 5.8 GRILL route failed without a classified upstream sample-plugin blocker")
    return {
        "schema": "fastdis.unreal_grill_blocked_lane.v1",
        "generated_at_utc": utc_now(),
        "lane": f"ue{version}",
        "engine_version": version,
        "status": "blocked",
        "source_smoke_path": display_path(source_smoke_path),
        "source_smoke_status": payload.get("status"),
        "probe_failure_kind": probe.get("failure_kind"),
        "summary": (
            "The public GRILL Unreal sample route is intentionally not lit for UE 5.8 on this host because "
            "bundled upstream sample dependencies still fail to compile."
        ),
        "blockers": blockers,
        "upstream_dependencies": {
            "CesiumForUnreal": {
                "blocked": bool(cesium_errors),
                "examples": cesium_errors[:8],
            },
            "LowEntryExtStdLib": {
                "blocked": bool(lowentry_errors),
                "examples": lowentry_errors[:8],
            },
        },
        "next_steps": [
            "Keep UE 5.7 as the preferred GRILL Unreal lane on Windows until the upstream sample plugins are updated.",
            "Track Cesium and LowEntry compatibility fixes separately from FastDIS plugin verification.",
            "Rerun the UE 5.8 GRILL source smoke after upstream sample dependencies are refreshed.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Unreal GRILL Blocked Lane",
        "",
        f"- lane: `{report['lane']}`",
        f"- status: `{report['status']}`",
        f"- source_smoke_path: `{report['source_smoke_path']}`",
        "",
        report["summary"],
        "",
        "## Blockers",
        "",
    ]
    for blocker in report["blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Upstream Dependencies", ""])
    deps = report["upstream_dependencies"]
    for name in ("CesiumForUnreal", "LowEntryExtStdLib"):
        dep = deps[name]
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- blocked: `{dep['blocked']}`")
        for example in dep["examples"]:
            lines.append(f"- `{example}`")
        if not dep["examples"]:
            lines.append("- no classified error lines captured")
        lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-smoke", type=Path, default=DEFAULT_SOURCE_SMOKE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.source_smoke)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        args.json_out,
        report,
        producer="tools/build_unreal_grill_blocked_lane_report.py",
    )
    args.md_out.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {display_path(args.json_out)}")
    print(f"md: {display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
