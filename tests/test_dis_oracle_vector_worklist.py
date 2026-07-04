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


def _readiness(path: Path) -> Path:
    return _write_json(
        path,
        {
            "schema": "fastdis.dis_oracle_vector_readiness.v1",
            "rows": [
                {
                    "version": "dis6",
                    "pdu_type": 1,
                    "pdu_name": "Entity State",
                    "family_name": "Entity Information",
                    "vectors": [
                        {
                            "vector_type": "minimal",
                            "file": "vectors/dis6/entity_state/minimal.json",
                            "readiness": "skeleton_or_missing",
                            "blockers": ["spec_basis_pending", "canonical_bytes_missing", "sha256_missing"],
                        },
                        {
                            "vector_type": "typical",
                            "file": "vectors/dis6/entity_state/typical.json",
                            "readiness": "skeleton_or_missing",
                            "blockers": ["canonical_bytes_missing", "sha256_missing", "hex_missing"],
                        },
                        {
                            "vector_type": "malformed",
                            "file": "vectors/dis6/entity_state/malformed.json",
                            "readiness": "skeleton_or_missing",
                            "blockers": ["malformed_expectation_pending"],
                        },
                        {
                            "vector_type": "boundary",
                            "file": "vectors/dis6/entity_state/boundary.json",
                            "readiness": "golden_ready",
                            "blockers": [],
                        },
                    ],
                }
            ],
        },
    )


def _tranche_plan(path: Path) -> Path:
    return _write_json(
        path,
        {
            "schema": "fastdis.dis_oracle_layout_pin_tranche_plan.v1",
            "tranches": [
                {
                    "name": "dis6_entity_information",
                    "review_order": 1,
                    "version": "dis6",
                    "family_name": "Entity Information",
                }
            ],
        },
    )


def test_vector_worklist_ranks_authoring_actions(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_worklist")

    report = module.build_report(
        _readiness(tmp_path / "readiness.json"),
        tranche_plan_path=_tranche_plan(tmp_path / "tranche_plan.json"),
        ignore_layout_gate=True,
    )

    assert report["schema"] == "fastdis.dis_oracle_vector_worklist.v1"
    assert report["status"] == "partial"
    assert report["summary"]["slot_count"] == 4
    assert report["summary"]["pending_slot_count"] == 3
    assert report["summary"]["ready_slot_count"] == 1
    assert report["summary"]["top_action"] == "pin_spec_basis"
    assert report["summary"]["first_tranche"] == "dis6_entity_information"
    assert [task["next_action"] for task in report["tasks"]] == [
        "pin_spec_basis",
        "fill_canonical_bytes",
        "write_malformed_expectation",
        "ready",
    ]
    assert "not golden byte evidence" in report["claim_boundary"]


def test_vector_worklist_prioritizes_layout_pin_gate(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_worklist")
    readiness = _readiness(tmp_path / "readiness.json")
    payload = json.loads(readiness.read_text(encoding="utf-8"))
    payload["rows"][0]["vectors"][0]["blockers"].append("layout_not_pinned")
    readiness.write_text(json.dumps(payload), encoding="utf-8")

    report = module.build_report(readiness)

    assert report["summary"]["top_action"] == "pin_normative_layout"
    assert report["tasks"][0]["next_action"] == "pin_normative_layout"
    assert report["tasks"][0]["priority"] == 5


def test_vector_worklist_can_filter_to_malformed_authoring(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_worklist")
    readiness = _readiness(tmp_path / "readiness.json")
    payload = json.loads(readiness.read_text(encoding="utf-8"))
    for vector in payload["rows"][0]["vectors"]:
        vector["blockers"].append("layout_not_pinned")
    readiness.write_text(json.dumps(payload), encoding="utf-8")

    report = module.build_report(
        readiness,
        tranche_plan_path=_tranche_plan(tmp_path / "tranche_plan.json"),
        ignore_layout_gate=True,
        only_vector_types={"malformed"},
    )

    assert report["summary"]["slot_count"] == 1
    assert report["summary"]["top_action"] == "write_malformed_expectation"
    assert report["tasks"][0]["vector_type"] == "malformed"
    assert report["tasks"][0]["tranche_name"] == "dis6_entity_information"


def test_vector_worklist_cli_writes_report(tmp_path: Path) -> None:
    module = _load("build_dis_oracle_vector_worklist")

    rc = module.main(
        [
            "--vector-readiness",
            str(_readiness(tmp_path / "readiness.json")),
            "--tranche-plan",
            str(_tranche_plan(tmp_path / "tranche_plan.json")),
            "--ignore-layout-gate",
            "--json-out",
            str(tmp_path / "out" / "worklist.json"),
            "--md-out",
            str(tmp_path / "out" / "worklist.md"),
        ]
    )

    assert rc == 0
    report = json.loads((tmp_path / "out" / "worklist.json").read_text(encoding="utf-8"))
    assert report["schema"] == "fastdis.dis_oracle_vector_worklist.v1"
    assert report["report_meta"]["producer"] == "tools/build_dis_oracle_vector_worklist.py"
    assert "DIS Oracle Vector Worklist" in (tmp_path / "out" / "worklist.md").read_text(encoding="utf-8")
