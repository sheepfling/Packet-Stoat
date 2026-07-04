from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_vector_authoring_packet_cli_writes_summary_reports(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_authoring_packet")
    golden = _write_json(
        tmp_path / "golden.json",
        {
            "schema": "fastdis.dis_oracle_vector_worklist.v1",
            "tasks": [
                {
                    "tranche_name": "dis6_entity_information",
                    "version": "dis6",
                    "family_name": "Entity Information",
                    "pdu_name": "Entity State",
                    "vector_type": "minimal",
                    "file": "vectors/dis6/entity_state/minimal.json",
                    "next_action": "pin_spec_basis",
                    "blockers": ["spec_basis_pending", "canonical_bytes_missing"],
                }
            ],
        },
    )
    malformed = _write_json(
        tmp_path / "malformed.json",
        {
            "schema": "fastdis.dis_oracle_vector_worklist.v1",
            "tasks": [
                {
                    "tranche_name": "dis6_entity_information",
                    "version": "dis6",
                    "family_name": "Entity Information",
                    "pdu_name": "Entity State",
                    "vector_type": "malformed",
                    "file": "vectors/dis6/entity_state/malformed.json",
                    "next_action": "pin_spec_basis",
                    "blockers": ["spec_basis_pending", "malformed_expectation_pending"],
                }
            ],
        },
    )

    rc = module.main(
        [
            "--tranche",
            "dis6_entity_information",
            "--golden-worklist",
            str(golden),
            "--malformed-worklist",
            str(malformed),
            "--json-out",
            str(tmp_path / "out" / "packet.json"),
            "--md-out",
            str(tmp_path / "out" / "packet.md"),
        ]
    )

    assert rc == 0
    payload = json.loads((tmp_path / "out" / "packet.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.dis_oracle_vector_authoring_packet.v1"
    assert payload["summary"]["tranche_name"] == "dis6_entity_information"
    assert payload["summary"]["golden_slot_count"] == 1
    assert payload["summary"]["malformed_slot_count"] == 1
    assert payload["summary"]["spec_basis_pending_slots"] == 2
    assert payload["report_meta"]["producer"] == "tools/build_dis_oracle_vector_authoring_packet.py"
