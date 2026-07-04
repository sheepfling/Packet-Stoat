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


def test_vector_spec_basis_packet_cli_writes_reports(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_spec_basis_packet")
    sheet = tmp_path / "sheet.yaml"
    sheet.write_text(
        yaml.safe_dump(
            {
                "schema": "fastdis.dis_oracle_vector_authoring_sheet.v1",
                "rows": [
                    {
                        "file": "vectors/dis6/entity_state/minimal.json",
                        "pdu_name": "Entity State",
                        "vector_type": "minimal",
                        "edit": {
                            "spec_basis": [{"standard": "ieee-1278.1a-1998", "reference": "pending", "claim": "layout"}]
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    rc = module.main(["--sheet", str(sheet), "--json-out", str(tmp_path / "out" / "packet.json"), "--md-out", str(tmp_path / "out" / "packet.md")])
    assert rc == 0
    payload = json.loads((tmp_path / "out" / "packet.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.dis_oracle_vector_spec_basis_packet.v1"
    assert payload["summary"]["pending_row_count"] == 1

