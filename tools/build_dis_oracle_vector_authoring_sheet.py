#!/usr/bin/env python3
"""Build an editable YAML sheet from a DIS oracle vector authoring packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_authoring_packet"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "dis_oracle_vector_authoring_sheet"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--yaml-out", type=Path)
    return parser.parse_args(argv)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_vector_payload(path_text: str | None) -> dict[str, Any]:
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        return {}
    return load_json(path)


def build_sheet(packet_path: Path) -> dict[str, Any]:
    packet = load_json(packet_path)
    rows: list[dict[str, Any]] = []
    for bucket_name in ("golden_slots", "malformed_slots"):
        for slot in packet.get(bucket_name, []) if isinstance(packet.get(bucket_name), list) else []:
            if not isinstance(slot, dict):
                continue
            payload = _load_vector_payload(slot.get("file"))
            rows.append(
                {
                    "file": slot.get("file"),
                    "version": slot.get("version"),
                    "family_name": slot.get("family_name"),
                    "pdu_name": slot.get("pdu_name"),
                    "vector_type": slot.get("vector_type"),
                    "next_action": slot.get("next_action"),
                    "blockers": slot.get("blockers") if isinstance(slot.get("blockers"), list) else [],
                    "edit": {
                        "spec_basis": payload.get("spec_basis") if isinstance(payload.get("spec_basis"), list) else [],
                        "notes": payload.get("notes") if isinstance(payload.get("notes"), list) else [],
                        "expected_wire": payload.get("expected_wire") if isinstance(payload.get("expected_wire"), dict) else {},
                        "malformed_expectation": payload.get("malformed_expectation"),
                    },
                }
            )
    return {
        "schema": "fastdis.dis_oracle_vector_authoring_sheet.v1",
        "source_packet": display_path(packet_path),
        "instructions": [
            "Edit this YAML sheet, then copy approved values back into the referenced vector JSON files.",
            "Replace pending spec_basis references with exact IEEE/SISO citations first.",
            "For malformed vectors, fill malformed_expectation with the exact reject-or-flag expectation.",
            "For golden vectors that still lack bytes, fill expected_wire only after the spec_basis is concrete.",
        ],
        "rows": rows,
        "claim_boundary": "This sheet is an editing aid. It does not itself make any vector golden or prove byte correctness.",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sheet = build_sheet(args.packet)
    yaml_out = args.yaml_out
    if yaml_out is None:
        stem = args.packet.stem.replace("dis_oracle_vector_authoring_packet_", "")
        yaml_out = DEFAULT_OUT_DIR / f"dis_oracle_vector_authoring_sheet_{stem}.yaml"
    yaml_out.parent.mkdir(parents=True, exist_ok=True)
    yaml_out.write_text(yaml.safe_dump(sheet, sort_keys=False), encoding="utf-8")
    print(f"yaml: {display_path(yaml_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
