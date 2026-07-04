#!/usr/bin/env python3
"""Apply an edited DIS oracle vector authoring sheet back to vector JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def rooted(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def apply_sheet(sheet_path: Path) -> dict[str, Any]:
    sheet = load_yaml(sheet_path)
    rows = sheet.get("rows") if isinstance(sheet.get("rows"), list) else []
    updated: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        file_text = row.get("file")
        edit = row.get("edit") if isinstance(row.get("edit"), dict) else {}
        if not isinstance(file_text, str) or not file_text:
            continue
        path = rooted(file_text)
        payload = load_json(path)
        payload["spec_basis"] = edit.get("spec_basis") if isinstance(edit.get("spec_basis"), list) else []
        payload["notes"] = edit.get("notes") if isinstance(edit.get("notes"), list) else []
        payload["expected_wire"] = edit.get("expected_wire") if isinstance(edit.get("expected_wire"), dict) else {}
        payload["malformed_expectation"] = edit.get("malformed_expectation")
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        updated.append(display_path(path))
    return {
        "schema": "fastdis.dis_oracle_vector_authoring_sheet_apply.v1",
        "status": "passed",
        "source_sheet": display_path(sheet_path),
        "updated_count": len(updated),
        "updated_files": updated,
        "claim_boundary": "This apply step copies reviewed edits into vector JSON files. It does not make them golden automatically.",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = apply_sheet(args.sheet)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
