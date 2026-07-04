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


def test_apply_vector_authoring_sheet_updates_vector_files(tmp_path: Path, monkeypatch) -> None:
    module = _load("apply_dis_oracle_vector_authoring_sheet")
    monkeypatch.setattr(module, "ROOT", tmp_path)

    vector_path = tmp_path / "vectors/dis6/entity_state/minimal.json"
    vector_path.parent.mkdir(parents=True, exist_ok=True)
    vector_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.dis_oracle_vector.v1",
                "spec_basis": [{"standard": "old", "reference": "old", "claim": "old"}],
                "notes": ["old"],
                "expected_wire": {"status": "layout_only"},
                "malformed_expectation": None,
            }
        ),
        encoding="utf-8",
    )
    sheet_path = tmp_path / "sheet.yaml"
    sheet_path.write_text(
        yaml.safe_dump(
            {
                "schema": "fastdis.dis_oracle_vector_authoring_sheet.v1",
                "rows": [
                    {
                        "file": "vectors/dis6/entity_state/minimal.json",
                        "edit": {
                            "spec_basis": [{"standard": "ieee-1278.1a-1998", "reference": "Table X", "claim": "Entity State minimal"}],
                            "notes": ["new"],
                            "expected_wire": {"status": "canonical_bytes_known", "endianness": "big"},
                            "malformed_expectation": None,
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    report = module.apply_sheet(sheet_path)

    payload = json.loads(vector_path.read_text(encoding="utf-8"))
    assert report["updated_count"] == 1
    assert payload["spec_basis"][0]["reference"] == "Table X"
    assert payload["notes"] == ["new"]
    assert payload["expected_wire"]["status"] == "canonical_bytes_known"
