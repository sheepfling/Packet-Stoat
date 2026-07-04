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


def test_vector_authoring_sheet_audit_reports_pending_rows(tmp_path: Path) -> None:
    module = _load("audit_dis_oracle_vector_authoring_sheet")
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
                            "spec_basis": [{"standard": "ieee-1278.1a-1998", "reference": "pending", "claim": "layout"}],
                            "expected_wire": {"status": "layout_only"},
                            "malformed_expectation": None,
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report = module.build_report(sheet)
    assert report["summary"]["spec_basis_pending_rows"] == 1
    assert report["status"] == "partial"
