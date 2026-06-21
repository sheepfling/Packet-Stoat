from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from tools.generate_pdu_catalog import DEFAULT_DIS6, DEFAULT_DIS7, catalog_from_xml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "generated" / "version_translation_manifest.json"


def _ensure_manifest() -> dict[str, object]:
    if not MANIFEST.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_version_translation_manifest.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_translation_manifest_has_one_rule_per_cataloged_cross_version_pdu() -> None:
    manifest = _ensure_manifest()
    records6 = catalog_from_xml(DEFAULT_DIS6, 6)
    records7 = catalog_from_xml(DEFAULT_DIS7, 7)
    rows = manifest["rows"]
    assert isinstance(rows, list)
    assert len(rows) == len(records6) + len(records7)

    row_keys = {
        (
            row["source_version"],
            row["target_version"],
            row["pdu_type"],
            row["protocol_family"],
        )
        for row in rows
    }
    for record in records6:
        assert (6, 7, record.pdu_type, record.protocol_family) in row_keys
    for record in records7:
        assert (7, 6, record.pdu_type, record.protocol_family) in row_keys


def test_translation_manifest_exposes_required_status_and_policy_contract() -> None:
    manifest = _ensure_manifest()
    assert set(manifest["status_enum"]) == {
        "EXACT",
        "RENAMED",
        "DEFAULTED",
        "DROPPED_FIELD",
        "DROPPED_PDU",
        "PASSTHROUGH_RAW",
        "SYNTHETIC",
        "FAILED_STRICT",
    }
    for row in manifest["rows"]:
        assert row["translation_status"] in manifest["status_enum"]
        assert row["translation_statuses"]
        assert set(row["policy_behaviors"]) == {
            "strict",
            "tolerant",
            "preserve_raw",
            "bridge",
            "engine",
            "lattice_lab",
        }
        assert row["strict_behavior"]
        assert row["tolerant_behavior"]
        assert row["preserve_raw_behavior"]
        assert row["engine_behavior"]
        assert row["lattice_lab_behavior"]
        assert row["bridge_behavior"]


def test_dis7_only_pdus_are_not_silently_synthesized_to_dis6() -> None:
    manifest = _ensure_manifest()
    dis7_to_dis6_dropped = [
        row
        for row in manifest["rows"]
        if row["source_version"] == 7 and row["target_version"] == 6 and row["target_equivalent"] is None
    ]
    assert dis7_to_dis6_dropped
    for row in dis7_to_dis6_dropped:
        assert row["translation_status"] == "DROPPED_PDU"
        assert row["strict_behavior"] == "FAILED_STRICT"
        assert row["tolerant_behavior"] == "GENERIC_EVENT"
        assert row["preserve_raw_behavior"] == "GENERIC_EVENT_WITH_RAW_SIDECAR"
        assert row["lattice_lab_behavior"] == "SimulationPduObservation"


def test_common_rows_record_header_field_defaults_or_drops() -> None:
    manifest = _ensure_manifest()
    common_rows = [row for row in manifest["rows"] if row["target_equivalent"] is not None]
    assert common_rows
    for row in common_rows:
        statuses = set(row["translation_statuses"])
        if row["source_version"] == 6:
            assert "DEFAULTED" in statuses
            assert any(rule["field"] == "pduStatus" and rule["rule"] == "default_zero" for rule in row["field_rules"])
        else:
            assert "DROPPED_FIELD" in statuses
            assert any(rule["field"] == "pduStatus" and rule["rule"] == "drop_for_dis6_header" for rule in row["field_rules"])


def test_catalog_gap_alias_hints_are_tracked_explicitly() -> None:
    manifest = _ensure_manifest()
    hints = {hint["pdu_type"]: hint for hint in manifest["catalog_gap_alias_hints"]}
    assert 28 in hints
    assert 35 in hints
    assert hints[28]["expected_status"] == "RENAMED"
    assert hints[35]["expected_status"] == "RENAMED"


def test_generate_version_translation_manifest_check_passes_for_current_tree() -> None:
    _ensure_manifest()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_version_translation_manifest.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
