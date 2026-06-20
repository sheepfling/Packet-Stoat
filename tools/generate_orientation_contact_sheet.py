#!/usr/bin/env python3
"""Generate a simple HTML contact sheet for orientation visual review artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="append", required=True, help="Projection report JSON file")
    parser.add_argument("--out", required=True, help="HTML output path")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_from_namespace(args: argparse.Namespace) -> int:
    reports = [load_json(Path(path)) for path in args.report]
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sections: list[str] = []
    for report in reports:
        rows = []
        for item in report["results"]:
            expected = ROOT / item["expected_image"]
            actual = ROOT / item["actual_image"]
            rows.append(
                "<tr>"
                f"<td>{item['case']}</td>"
                f"<td>{item['camera']}</td>"
                f"<td>{item['failure_signature'] or ''}</td>"
                f"<td>{'PASS' if item['pass'] else 'FAIL'}</td>"
                f"<td><img src=\"{os.path.relpath(expected, out_path.parent)}\" width=\"240\"></td>"
                f"<td><img src=\"{os.path.relpath(actual, out_path.parent)}\" width=\"240\"></td>"
                "</tr>"
            )
        sections.append(
            f"<h2>{report['engine']} / {report['label']}</h2>"
            "<table border=\"1\" cellspacing=\"0\" cellpadding=\"6\">"
            "<tr><th>Case</th><th>Camera</th><th>Signature</th><th>Status</th><th>Expected</th><th>Actual</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    html = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>FastDIS Orientation Contact Sheet</title>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;background:#15181d;color:#f0f0f0;} "
        "table{margin-bottom:24px;background:#20242b;} td,th{vertical-align:top;} img{background:#0f1115;}</style>"
        "</head><body><h1>FastDIS Orientation Contact Sheet</h1>"
        + "".join(sections)
        + "</body></html>"
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {display_path(out_path)}")
    return 0


def main() -> int:
    return run_from_namespace(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
