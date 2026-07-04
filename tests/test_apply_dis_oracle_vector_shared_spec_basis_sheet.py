from __future__ import annotations

import importlib.util
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


def test_apply_shared_spec_basis_sheet_updates_target_rows(tmp_path: Path) -> None:
    module = _load("apply_dis_oracle_vector_shared_spec_basis_sheet")
    shared = tmp_path / "shared.yaml"
    sheet = tmp_path / "sheet.yaml"
    shared.write_text(
        yaml.safe_dump(
            {
                "shared_spec_basis": [{"standard": "ieee-1278.1a-1998", "reference": "Table X", "claim": "Entity State"}],
                "target_files": ["a.json", "b.json"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    sheet.write_text(
        yaml.safe_dump(
            {
                "rows": [
                    {"file": "a.json", "edit": {"spec_basis": [{"reference": "pending"}]}},
                    {"file": "b.json", "edit": {"spec_basis": [{"reference": "pending"}]}},
                    {"file": "c.json", "edit": {"spec_basis": [{"reference": "pending"}]}},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result = module.apply_shared(shared, sheet)
    payload = yaml.safe_load(sheet.read_text(encoding="utf-8"))
    assert result["updated_rows"] == 2
    assert payload["rows"][0]["edit"]["spec_basis"][0]["reference"] == "Table X"
    assert payload["rows"][2]["edit"]["spec_basis"][0]["reference"] == "pending"
