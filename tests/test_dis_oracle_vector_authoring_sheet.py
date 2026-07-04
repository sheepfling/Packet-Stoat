from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import yaml


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


def test_vector_authoring_sheet_cli_writes_yaml(tmp_path: Path, monkeypatch) -> None:
    module = _load("build_dis_oracle_vector_authoring_sheet")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "DEFAULT_OUT_DIR", tmp_path / "out")

    vector_file = _write_json(
        tmp_path / "vectors/dis6/entity_state/minimal.json",
        {
            "schema": "fastdis.dis_oracle_vector.v1",
            "spec_basis": [{"standard": "ieee-1278.1a-1998", "reference": "pending", "claim": "layout"}],
            "notes": ["pending"],
            "expected_wire": {"status": "layout_only", "endianness": "big"},
            "malformed_expectation": None,
        },
    )
    packet = _write_json(
        tmp_path / "packet.json",
        {
            "schema": "fastdis.dis_oracle_vector_authoring_packet.v1",
            "golden_slots": [
                {
                    "file": str(vector_file.relative_to(tmp_path)),
                    "version": "dis6",
                    "family_name": "Entity Information",
                    "pdu_name": "Entity State",
                    "vector_type": "minimal",
                    "next_action": "pin_spec_basis",
                    "blockers": ["spec_basis_pending"],
                }
            ],
            "malformed_slots": [],
        },
    )

    rc = module.main(["--packet", str(packet), "--yaml-out", str(tmp_path / "out" / "sheet.yaml")])

    assert rc == 0
    payload = yaml.safe_load((tmp_path / "out" / "sheet.yaml").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.dis_oracle_vector_authoring_sheet.v1"
    assert payload["rows"][0]["pdu_name"] == "Entity State"
    assert payload["rows"][0]["edit"]["spec_basis"][0]["reference"] == "pending"
