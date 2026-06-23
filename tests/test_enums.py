from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import fastdis
from fastdis import enums


ROOT = Path(__file__).resolve().parents[1]


def test_pdu_type_lookup_uses_standard_backbone() -> None:
    value = enums.lookup("pdu_type", 1, version=7)

    assert value.known is True
    assert value.label == "Entity State"


def test_unknown_enum_values_are_preserved() -> None:
    value = enums.lookup("force_id", 99)

    assert value.known is False
    assert value.value == 99
    assert value.label == "Unknown(99)"


def test_entity_type_lookup_returns_progressive_fallback_keys() -> None:
    payload = enums.lookup_entity_type(1, 2, 225, 1, 1, 3, 0)

    assert payload["components"]["kind"]["label"] == "Platform"
    assert payload["components"]["domain"]["label"] == "Air"
    assert payload["components"]["country"]["label"] == "United States"
    assert payload["progressive_fallback_keys"] == [
        "1.2.225.1.1.3.0",
        "1.2.225.1.1.3.*",
        "1.2.225.1.1.*",
        "1.2.225.1.*",
        "1.2.225.*",
        "1.2.*",
    ]


def test_enum_coverage_manifest_tracks_wave_one_scope() -> None:
    manifest = enums.coverage_manifest()

    assert manifest["unknown_value_policy"] == "preserve_numeric_and_label_unknown"
    assert manifest["full_siso_ref_010_imported"] is False
    pdu_type = next(row for row in manifest["families"] if row["enum_name"] == "PduType")
    assert pdu_type["values_imported"] == 141
    assert any(row["enum_name"] == "EntityType" for row in manifest["families"])


def test_enum_api_is_exported_from_fastdis() -> None:
    assert fastdis.lookup_enum("force_id", 1).label == "Friendly"
    assert fastdis.describe_packet_header_enums(7, 1, 1)["pdu_type"]["label"] == "Entity State"


def test_fastdis_enums_check_cli() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "fastdis", "enums", "check"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["pinned_reference"] == "siso-ref-010-v32"
