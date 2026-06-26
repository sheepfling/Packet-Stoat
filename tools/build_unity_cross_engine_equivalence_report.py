#!/usr/bin/env python3
"""Build a Unity-facing cross-engine equivalence report from existing audit evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import run_epic2_audit


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=ROOT / "build" / "reports" / "unity_cross_engine_equivalence.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "build" / "reports" / "unity_cross_engine_equivalence.md")
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(payload: dict[str, object]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# Unity Cross-Engine Equivalence",
        "",
        f"- status: `{payload['status']}`",
        "",
        payload["note"],
        "",
        "| surface | catalog rows | deep rows |",
        "| --- | --- | --- |",
    ]
    for surface, counts in metrics["language_rows"].items():
        lines.append(f"| {surface} | {counts['catalog_rows']} | {counts['deep_rows']} |")
    lines.extend(
        [
            "",
            f"- logging_descriptors: `{metrics['logging_descriptors']}`",
            f"- lattice_records: `{metrics['lattice_records']}`",
            f"- unity_csharp_bridge_probe_status: `{metrics['unity_csharp_bridge_probe_status']}`",
            "",
            "## Evidence",
            "",
        ]
    )
    for row in payload["evidence"]:
        lines.append(f"- `{row['path']}` exists=`{row['exists']}` kind=`{row['kind']}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = {
        "schema": "fastdis.unity_cross_engine_equivalence.v1",
        **run_epic2_audit.audit_cross_engine_parity(),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(payload) + "\n", encoding="utf-8")
    print(f"unity cross-engine equivalence json: {display_path(args.json_out)}")
    print(f"unity cross-engine equivalence md: {display_path(args.md_out)}")
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
