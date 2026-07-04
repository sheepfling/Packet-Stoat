#!/usr/bin/env python3
"""Build a shared spec-basis sheet for one PDU across multiple vector rows."""

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


def build_sheet(sheet_path: Path, pdu_name: str) -> dict[str, Any]:
    sheet = load_yaml(sheet_path)
    rows = [row for row in sheet.get("rows", []) if isinstance(row, dict) and row.get("pdu_name") == pdu_name]
    seed = rows[0] if rows else {}
    seed_edit = seed.get("edit") if isinstance(seed.get("edit"), dict) else {}
    return {
        "schema": "fastdis.dis_oracle_vector_shared_spec_basis_sheet.v1",
        "source_sheet": display_path(sheet_path),
        "pdu_name": pdu_name,
        "instructions": [
            "Fill the shared spec_basis citation once for this PDU.",
            "Apply it back to every matching row in the source vector authoring sheet.",
        ],
        "shared_spec_basis": seed_edit.get("spec_basis") if isinstance(seed_edit.get("spec_basis"), list) else [],
        "target_files": [row.get("file") for row in rows],
        "claim_boundary": "This sheet only distributes shared citation edits; it does not validate them.",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_sheet(args.sheet, args.pdu_name)
    yaml_out = args.yaml_out
    if yaml_out is None:
        stem = args.sheet.stem
        slug = args.pdu_name.lower().replace("/", "_").replace(" ", "_")
        yaml_out = DEFAULT_OUT_DIR / f"{stem}_{slug}_shared_spec_basis.yaml"
    yaml_out.parent.mkdir(parents=True, exist_ok=True)
    yaml_out.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(f"yaml: {display_path(yaml_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
