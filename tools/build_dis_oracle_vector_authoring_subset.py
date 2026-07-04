#!/usr/bin/env python3
"""Build a filtered vector authoring sheet subset, typically for one PDU family."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_authoring_sheet"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--pdu-name", required=True)
    parser.add_argument("--yaml-out", type=Path)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def build_subset(sheet_path: Path, pdu_name: str) -> dict[str, Any]:
    sheet = load_yaml(sheet_path)
    rows = sheet.get("rows") if isinstance(sheet.get("rows"), list) else []
    subset = [row for row in rows if isinstance(row, dict) and row.get("pdu_name") == pdu_name]
    return {
        "schema": "fastdis.dis_oracle_vector_authoring_sheet.v1",
        "source_sheet": display_path(sheet_path),
        "instructions": [
            f"This subset is filtered to pdu_name={pdu_name}.",
            *(sheet.get("instructions") if isinstance(sheet.get("instructions"), list) else []),
        ],
        "rows": subset,
        "claim_boundary": sheet.get("claim_boundary") or "This sheet is an editing aid.",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    subset = build_subset(args.sheet, args.pdu_name)
    yaml_out = args.yaml_out
    if yaml_out is None:
        stem = args.sheet.stem
        slug = args.pdu_name.lower().replace("/", "_").replace(" ", "_")
        yaml_out = DEFAULT_OUT_DIR / f"{stem}_{slug}.yaml"
    yaml_out.parent.mkdir(parents=True, exist_ok=True)
    yaml_out.write_text(yaml.safe_dump(subset, sort_keys=False), encoding="utf-8")
    print(f"yaml: {display_path(yaml_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
