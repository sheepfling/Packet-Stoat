from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_exports


EXPECTED_MANIFEST = ROOT / "benchmark_results" / "expected_exports_alpha2_start.txt"
EXPORTED_MANIFEST = ROOT / "benchmark_results" / "exports_alpha2_start_macos.txt"
BUILT_LIBRARY = ROOT / "build" / "libfastdis.dylib"


def _read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_expected_export_manifest_matches_public_header() -> None:
    assert EXPECTED_MANIFEST.is_file()
    expected_from_header = check_exports.expected_symbols_from_header(check_exports.DEFAULT_HEADER)
    assert _read_lines(EXPECTED_MANIFEST) == expected_from_header


def test_expected_export_manifest_covers_snapshot_buffer_alpha2_additions() -> None:
    manifest = set(_read_lines(EXPECTED_MANIFEST))
    assert "fastdis_entity_snapshot_buffer_create_ex" in manifest
    assert "fastdis_entity_snapshot_buffer_get_stats" in manifest
    assert "fastdis_entity_snapshot_buffer_reset_stats" in manifest
    assert "fastdis_entity_snapshot_buffer_slot_count" in manifest
    assert "fastdis_entity_snapshot_buffer_stats_init" in manifest


def test_exported_manifest_matches_current_macos_build_when_available() -> None:
    if not BUILT_LIBRARY.is_file():
        pytest.skip(f"built shared library not present: {BUILT_LIBRARY}")

    exported = sorted(check_exports.exported_symbols(BUILT_LIBRARY))
    assert _read_lines(EXPORTED_MANIFEST) == exported
