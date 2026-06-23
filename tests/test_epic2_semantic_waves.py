from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _ensure_manifest() -> dict[str, object]:
    path = ROOT / "generated" / "epic2_semantic_waves.json"
    if not path.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_epic2_semantic_waves.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return json.loads(path.read_text(encoding="utf-8"))


def test_epic2_semantic_waves_cover_all_141_rows() -> None:
    manifest = _ensure_manifest()
    summary = manifest["summary"]
    records = manifest["records"]

    assert summary["records"] == 141
    assert summary["waves"] == 5
    assert len(records) == 141
    assert {record["wave_id"] for record in records} == {"wave1", "wave2", "wave3", "wave4", "wave5"}


def test_epic2_semantic_waves_keep_expected_anchor_rows_in_expected_waves() -> None:
    manifest = _ensure_manifest()
    records = {
        (record["protocol_version"], record["pdu_type"]): record
        for record in manifest["records"]
    }

    assert records[(7, 1)]["wave_id"] == "wave1"
    assert records[(7, 67)]["wave_id"] == "wave1"
    assert records[(7, 2)]["wave_id"] == "wave2"
    assert records[(7, 23)]["wave_id"] == "wave3"
    assert records[(7, 13)]["wave_id"] == "wave4"
    assert records[(7, 5)]["wave_id"] == "wave5"
    assert records[(7, 72)]["wave_id"] == "wave1"
    assert records[(7, 70)]["wave_id"] == "wave5"


def test_epic2_semantic_waves_show_wave2_decoded_progress() -> None:
    manifest = _ensure_manifest()
    waves = {wave["wave_id"]: wave for wave in manifest["waves"]}

    assert waves["wave2"]["fully_domain_decoded_rows"] == 10
    assert waves["wave2"]["semantic_prefix_rows"] == 0


def test_epic2_semantic_waves_show_wave3_radio_progress() -> None:
    manifest = _ensure_manifest()
    waves = {wave["wave_id"]: wave for wave in manifest["waves"]}

    assert waves["wave3"]["fully_domain_decoded_rows"] == 20
    assert waves["wave3"]["semantic_prefix_rows"] == 0


def test_epic2_semantic_waves_show_wave1_lifecycle_progress() -> None:
    manifest = _ensure_manifest()
    waves = {wave["wave_id"]: wave for wave in manifest["waves"]}

    assert waves["wave1"]["fully_domain_decoded_rows"] == 12
    assert waves["wave1"]["semantic_prefix_rows"] == 4


def test_epic2_semantic_waves_show_wave4_control_progress() -> None:
    manifest = _ensure_manifest()
    waves = {wave["wave_id"]: wave for wave in manifest["waves"]}

    assert waves["wave4"]["fully_domain_decoded_rows"] == 44
    assert waves["wave4"]["semantic_prefix_rows"] == 0


def test_epic2_semantic_waves_show_wave5_remaining_family_progress() -> None:
    manifest = _ensure_manifest()
    waves = {wave["wave_id"]: wave for wave in manifest["waves"]}

    assert waves["wave5"]["fully_domain_decoded_rows"] == 30
    assert waves["wave5"]["semantic_prefix_rows"] == 0


def test_generate_epic2_semantic_waves_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_epic2_semantic_waves.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
