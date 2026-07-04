#!/usr/bin/env python3
"""Build an actionable malformed-vector authoring queue."""

from __future__ import annotations

import argparse
from pathlib import Path

import build_dis_oracle_vector_worklist as worklist_tool
from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_malformed_vector_worklist"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vector-readiness", type=Path, default=worklist_tool.DEFAULT_VECTOR_READINESS)
    parser.add_argument("--tranche-plan", type=Path, default=worklist_tool.DEFAULT_TRANCHE_PLAN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_DIR / "dis_oracle_malformed_vector_worklist.json")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_DIR / "dis_oracle_malformed_vector_worklist.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = worklist_tool.build_report(
        args.vector_readiness,
        tranche_plan_path=args.tranche_plan,
        ignore_layout_gate=True,
        only_vector_types={"malformed"},
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(
        args.json_out,
        report,
        schema="fastdis.dis_oracle_vector_worklist.v1",
        producer="tools/build_dis_oracle_malformed_vector_worklist.py",
    )
    args.md_out.write_text(worklist_tool.render_markdown(report) + "\n", encoding="utf-8")
    print(f"json: {worklist_tool.display_path(args.json_out)}")
    print(f"md: {worklist_tool.display_path(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
