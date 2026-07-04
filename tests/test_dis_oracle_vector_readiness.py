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


def _vector(path: Path, *, vector_type: str, vector_status: str, wire_status: str, pending: bool = True) -> Path:
    expected_wire = {"status": wire_status, "endianness": "big"}
    if wire_status == "canonical_bytes_known":
        expected_wire.update(
            {
                "total_length": 12,
                "sha256": "a" * 64,
                "hex": "00" * 12,
                "field_offsets": {"header.protocolVersion": 0},
                "field_widths": {"header.protocolVersion": 1},
            }
        )
    payload = {
        "schema": "fastdis.dis_oracle_vector.v1",
        "id": f"dis6-fire-{vector_type}",
        "version": "dis6",
        "pdu_type": 2,
        "pdu_name": "Fire",
        "vector_type": vector_type,
        "vector_status": vector_status,
        "spec_basis": [
            {
                "standard": "ieee-1278.1a-1998",
                "reference": "pending exact pin" if pending else "Table 5. Fire PDU",
                "claim": "Fire vector",
            }
        ],
        "semantic_message": {},
        "expected_wire": expected_wire,
        "malformed_expectation": (
            {"status": "pending"} if pending and vector_type == "malformed" else {"status": "reject_truncated_length"} if vector_type == "malformed" else None
        ),
    }
    return _write_json(path, payload)


def _catalog(tmp_path: Path, *, qualities: dict[str, str], layout_pinned: bool = True) -> Path:
    files = {}
    for vector_type, quality in qualities.items():
        files[vector_type] = str(tmp_path / "vectors" / f"{vector_type}.json")
        if quality == "skeleton":
            _vector(Path(files[vector_type]), vector_type=vector_type, vector_status="skeleton", wire_status="layout_only" if vector_type != "malformed" else "malformed_rejected")
        elif quality == "draft":
            _vector(Path(files[vector_type]), vector_type=vector_type, vector_status="draft", wire_status="canonical_bytes_known" if vector_type != "malformed" else "malformed_rejected")
        else:
            _vector(Path(files[vector_type]), vector_type=vector_type, vector_status="golden", wire_status="canonical_bytes_known" if vector_type != "malformed" else "malformed_rejected", pending=False)
    return _write_json(
        tmp_path / "catalog.json",
        {
            "schema": "fastdis.dis_oracle_catalog.v1",
            "rows": [
                {
                    "version": "dis6",
                    "pdu_type": 2,
                    "pdu_name": "Fire",
                    "family_name": "Warfare",
                    "coverage": {"normative_layout_pinned": layout_pinned},
                    "vectors": {"quality": qualities, "files": files},
                }
            ],
        },
    )


def test_vector_readiness_reports_skeleton_blockers(tmp_path: Path) -> None:
    module = _load("audit_dis_oracle_vector_readiness")
    catalog = _catalog(tmp_path, qualities={name: "skeleton" for name in module.VECTOR_TYPES})

    report = module.build_report(catalog)

    row = report["rows"][0]
    assert report["status"] == "partial"
    assert report["summary"]["present_vector_files"] == 5
    assert report["summary"]["layout_pinned_rows"] == 1
    assert report["summary"]["rows_blocked_by_unpinned_layout"] == 0
    assert report["summary"]["golden_vector_slots"] == 0
    assert row["family_name"] == "Warfare"
    assert row["review_state"] == "skeleton_or_missing"
    assert "vector_status_not_golden" in row["blockers"]
    assert "spec_basis_pending" in row["blockers"]
    assert "canonical_bytes_missing" in row["blockers"]


def test_vector_readiness_distinguishes_draft_byte_evidence(tmp_path: Path) -> None:
    module = _load("audit_dis_oracle_vector_readiness")
    qualities = {name: "skeleton" for name in module.VECTOR_TYPES}
    qualities["minimal"] = "draft"
    catalog = _catalog(tmp_path, qualities=qualities)

    report = module.build_report(catalog)

    row = report["rows"][0]
    assert row["review_state"] == "draft_byte_evidence"
    assert row["draft_byte_evidence_count"] == 1
    assert report["summary"]["draft_byte_evidence_slots"] == 1


def test_vector_readiness_accepts_all_golden_vectors(tmp_path: Path) -> None:
    module = _load("audit_dis_oracle_vector_readiness")
    catalog = _catalog(tmp_path, qualities={name: "golden" for name in module.VECTOR_TYPES})

    report = module.build_report(catalog)

    row = report["rows"][0]
    assert report["status"] == "passed"
    assert row["review_state"] == "golden_ready"
    assert row["golden_required_vectors"] is True
    assert row["blockers"] == []
    assert report["summary"]["rows_with_all_golden_vectors"] == 1


def test_vector_readiness_blocks_golden_vectors_without_pinned_layout(tmp_path: Path) -> None:
    module = _load("audit_dis_oracle_vector_readiness")
    catalog = _catalog(tmp_path, qualities={name: "golden" for name in module.VECTOR_TYPES}, layout_pinned=False)

    report = module.build_report(catalog)

    row = report["rows"][0]
    assert report["status"] == "partial"
    assert row["normative_layout_pinned"] is False
    assert row["golden_required_vectors"] is False
    assert row["golden_count"] == 0
    assert row["blockers"] == ["layout_not_pinned"]
    assert report["summary"]["layout_pinned_rows"] == 0
    assert report["summary"]["rows_blocked_by_unpinned_layout"] == 1
    assert report["summary"]["slots_blocked_by_unpinned_layout"] == 5


def test_vector_readiness_cli_writes_report(tmp_path: Path) -> None:
    module = _load("audit_dis_oracle_vector_readiness")
    catalog = _catalog(tmp_path, qualities={name: "skeleton" for name in module.VECTOR_TYPES})

    rc = module.main(
        [
            "--catalog",
            str(catalog),
            "--json-out",
            str(tmp_path / "out" / "vector_readiness.json"),
            "--md-out",
            str(tmp_path / "out" / "vector_readiness.md"),
        ]
    )

    assert rc == 0
    payload = json.loads((tmp_path / "out" / "vector_readiness.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.dis_oracle_vector_readiness.v1"
    assert payload["report_meta"]["producer"] == "tools/audit_dis_oracle_vector_readiness.py"
    assert "DIS Oracle Vector Readiness" in (tmp_path / "out" / "vector_readiness.md").read_text(encoding="utf-8")
