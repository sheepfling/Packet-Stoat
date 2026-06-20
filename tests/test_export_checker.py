from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_exports
import run_export_report


BUILT_LIBRARY = ROOT / "build" / "libfastdis.dylib"


def test_expected_export_manifest_matches_public_header() -> None:
    expected_from_header = check_exports.expected_symbols_from_header(check_exports.DEFAULT_HEADER)
    assert expected_from_header
    assert expected_from_header == sorted(set(expected_from_header))


def test_expected_export_manifest_covers_snapshot_buffer_alpha2_additions() -> None:
    manifest = set(check_exports.expected_symbols_from_header(check_exports.DEFAULT_HEADER))
    assert "fastdis_entity_snapshot_buffer_create_ex" in manifest
    assert "fastdis_entity_snapshot_buffer_get_stats" in manifest
    assert "fastdis_entity_snapshot_buffer_reset_stats" in manifest
    assert "fastdis_entity_snapshot_buffer_slot_count" in manifest
    assert "fastdis_entity_snapshot_buffer_stats_init" in manifest


def test_exported_manifest_matches_current_macos_build_when_available(tmp_path: Path) -> None:
    if not BUILT_LIBRARY.is_file():
        pytest.skip(f"built shared library not present: {BUILT_LIBRARY}")

    exported = sorted(check_exports.exported_symbols(BUILT_LIBRARY))
    summary, expected_manifest, exported_manifest = run_export_report.generate_report(BUILT_LIBRARY, tmp_path)
    expected = check_exports.expected_symbols_from_header(check_exports.DEFAULT_HEADER)
    assert expected_manifest.read_text(encoding="utf-8").splitlines() == expected
    assert exported_manifest.read_text(encoding="utf-8").splitlines() == exported
    assert summary["status"] == "passed"


def test_generated_export_summary_points_at_generated_manifests(tmp_path: Path) -> None:
    if not BUILT_LIBRARY.is_file():
        pytest.skip(f"built shared library not present: {BUILT_LIBRARY}")

    payload, expected_manifest, exported_manifest = run_export_report.generate_report(BUILT_LIBRARY, tmp_path)
    payload = json.loads(json.dumps(payload))
    assert payload["status"] == "passed"
    assert payload["expected_manifest"] == run_export_report.display_path(expected_manifest)
    assert payload["exported_manifest"] == run_export_report.display_path(exported_manifest)
