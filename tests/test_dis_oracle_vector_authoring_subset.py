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


def test_vector_authoring_subset_filters_rows(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_authoring_subset")
    sheet = tmp_path / "sheet.yaml"
    sheet.write_text(
        yaml.safe_dump(
            {
                "schema": "fastdis.dis_oracle_vector_authoring_sheet.v1",
                "instructions": ["x"],
                "rows": [
                    {"pdu_name": "Entity State", "vector_type": "minimal"},
                    {"pdu_name": "Collision", "vector_type": "minimal"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    rc = module.main(["--sheet", str(sheet), "--pdu-name", "Entity State", "--yaml-out", str(tmp_path / "out" / "subset.yaml")])
    assert rc == 0
    payload = yaml.safe_load((tmp_path / "out" / "subset.yaml").read_text(encoding="utf-8"))
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["pdu_name"] == "Entity State"
