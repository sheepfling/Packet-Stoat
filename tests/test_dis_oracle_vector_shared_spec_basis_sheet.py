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


def test_shared_spec_basis_sheet_filters_single_pdu(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_shared_spec_basis_sheet")
    sheet = tmp_path / "sheet.yaml"
    sheet.write_text(
        yaml.safe_dump(
            {
                "rows": [
                    {"file": "a.json", "pdu_name": "Entity State", "edit": {"spec_basis": [{"reference": "pending"}]}},
                    {"file": "b.json", "pdu_name": "Collision", "edit": {"spec_basis": [{"reference": "pending"}]}},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    payload = module.build_sheet(sheet, "Entity State")
    assert payload["pdu_name"] == "Entity State"
    assert payload["target_files"] == ["a.json"]

