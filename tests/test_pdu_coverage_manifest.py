from __future__ import annotations

import json
from pathlib import Path
import subprocess
import struct
import sys

import fastdis


ROOT = Path(__file__).resolve().parents[1]


def _ensure_generated() -> None:
    required = [
        ROOT / "generated" / "pdu_coverage_manifest.json",
        ROOT / "generated" / "pdu_standard_backbone.json",
    ]
    if not all(path.exists() for path in required):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_pdu_coverage.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def _ensure_manifest() -> dict[str, object]:
    _ensure_generated()
    path = ROOT / "generated" / "pdu_coverage_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _rows_by_key(manifest: dict[str, object]) -> dict[tuple[int, int], dict[str, object]]:
    rows = manifest["rows"]
    assert isinstance(rows, list)
    return {
        (int(row["standard_version"]), int(row["pdu_type"])): row
        for row in rows
        if isinstance(row, dict)
    }


def test_standard_backbone_has_full_dis6_dis7_pdu_enum_counts() -> None:
    _ensure_generated()
    backbone = json.loads((ROOT / "generated" / "pdu_standard_backbone.json").read_text(encoding="utf-8"))
    summary = backbone["summary"]
    assert summary["dis6_rows"] == 68
    assert summary["dis7_rows"] == 73
    assert summary["total_rows"] == 141
    assert {(item["pdu_type"], item["dis6_name"], item["dis7_name"]) for item in summary["aliases"]} == {
        (28, "IFF/ATC/NAVAIDS", "IFF"),
        (35, "Transfer Control", "Transfer Ownership"),
    }


def test_pdu_coverage_manifest_distinguishes_standard_from_xml_catalog() -> None:
    manifest = _ensure_manifest()
    summary = manifest["summary"]
    assert summary["standard_dis6_rows"] == 68
    assert summary["standard_dis7_rows"] == 73
    assert summary["standard_total_rows"] == 141
    assert summary["xml_catalog_dis6_rows"] == 61
    assert summary["xml_catalog_dis7_rows"] == 55
    assert summary["xml_catalog_total_rows"] == 116
    assert summary["catalog_gap_rows"] == 25


def test_every_standard_pdu_has_safe_ingest_and_endpoint_behavior() -> None:
    manifest = _ensure_manifest()
    rows = manifest["rows"]
    assert isinstance(rows, list)
    assert len(rows) == 141
    for row in rows:
        assert row["safe_ingest"]
        assert row["header_validated"]
        assert row["length_checked"]
        assert row["generic_endpoint"]
        endpoint_behavior = row["endpoint_behavior"]
        assert isinstance(endpoint_behavior, dict)
        for endpoint in ("python", "c", "cpp", "unreal", "godot", "unity", "lattice_lab"):
            assert endpoint_behavior[endpoint]


def test_every_standard_pdu_header_is_safely_ingested() -> None:
    rows = _ensure_manifest()["rows"]
    assert isinstance(rows, list)
    for row in rows:
        version = int(row["standard_version"])
        pdu_type = int(row["pdu_type"])
        family = int(row["protocol_family"])
        status_or_padding = 0 if version >= 7 else 0
        packet = struct.pack(">BBBBIHH", version, 1, pdu_type, family, 0x10203040, 12, status_or_padding)
        header = fastdis.parse_header(packet, strict=True)
        assert header is not None
        assert header.version == version
        assert header.pdu_type == pdu_type
        assert header.protocol_family == family
        assert header.length == 12


def test_known_schema_gaps_and_aliases_are_explicit() -> None:
    rows = _rows_by_key(_ensure_manifest())

    assert rows[(7, 28)]["translation_status"] == "RENAMED"
    assert rows[(7, 35)]["translation_status"] == "RENAMED"

    assert rows[(7, 70)]["schema_status"] == "SCHEMA_GAP"
    assert rows[(7, 70)]["catalog_status"] == "ENUM_ONLY"
    assert rows[(7, 71)]["schema_status"] == "SCHEMA_GAP"
    assert rows[(7, 71)]["catalog_status"] == "ENUM_ONLY"

    attribute = rows[(7, 72)]
    assert attribute["schema_status"] == "PRESENT_BUT_MISSING_PDU_TYPE_INITIAL_VALUE"
    assert attribute["schema_present"]
    assert not attribute["generated_catalog_present"]


def test_generate_pdu_coverage_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_pdu_coverage.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
