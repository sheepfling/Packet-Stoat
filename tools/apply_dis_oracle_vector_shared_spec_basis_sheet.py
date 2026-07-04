#!/usr/bin/env python3
"""Apply a shared spec-basis sheet back to a vector authoring sheet."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-sheet", type=Path, required=True)
    parser.add_argument("--sheet", type=Path, required=True)
    return parser.parse_args(argv)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def apply_shared(shared_path: Path, sheet_path: Path) -> dict[str, Any]:
    shared = load_yaml(shared_path)
    sheet = load_yaml(sheet_path)
    target_files = set(shared.get("target_files") if isinstance(shared.get("target_files"), list) else [])
    shared_spec_basis = shared.get("shared_spec_basis") if isinstance(shared.get("shared_spec_basis"), list) else []
    updated = 0
    for row in sheet.get("rows", []) if isinstance(sheet.get("rows"), list) else []:
        if not isinstance(row, dict):
            continue
        if row.get("file") not in target_files:
            continue
        edit = row.get("edit")
        if not isinstance(edit, dict):
            row["edit"] = {"spec_basis": shared_spec_basis}
        else:
            edit["spec_basis"] = shared_spec_basis
        updated += 1
    sheet_path.write_text(yaml.safe_dump(sheet, sort_keys=False), encoding="utf-8")
    return {"updated_rows": updated}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = apply_shared(args.shared_sheet, args.sheet)
    print(yaml.safe_dump(result, sort_keys=False), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
