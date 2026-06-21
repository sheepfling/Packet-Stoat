from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import generate_dead_reckoning_coverage


def test_dead_reckoning_manifest_tracks_all_standard_algorithms() -> None:
    manifest = generate_dead_reckoning_coverage.build_manifest()
    rows = manifest["rows"]
    assert manifest["schema"] == "fastdis.dead_reckoning_coverage.v1"
    assert [row["value"] for row in rows] == list(range(10))
    assert {row["symbol"] for row in rows} == {
        "OTHER",
        "STATIC",
        "DRM_FPW",
        "DRM_RPW",
        "DRM_RVW",
        "DRM_FVW",
        "DRM_FPB",
        "DRM_RPB",
        "DRM_RVB",
        "DRM_FVB",
    }


def test_dead_reckoning_manifest_is_honest_about_current_gaps() -> None:
    manifest = generate_dead_reckoning_coverage.build_manifest()
    assert manifest["overall_status"] == "partial"
    assert manifest["summary"]["algorithm_rows"] == 10
    assert manifest["summary"]["surface_compliance_percent"] < 100.0
    for row in manifest["rows"]:
        assert row["surfaces"]["standard_enum_accounted"] is True
        assert row["surfaces"]["c_field_parse"] is True
        assert row["surfaces"]["cpp_field_parse"] is True
        assert row["surfaces"]["python_field_parse"] is True
        assert row["surfaces"]["linear_fallback"] is True
        assert "algorithmic_c" in row["missing_surfaces"]
        assert "unreal_runtime_scene" in row["missing_surfaces"]
        assert "lattice_metadata" in row["missing_surfaces"]


def test_checked_in_dead_reckoning_markdown_report_is_fresh() -> None:
    report_path = ROOT / "docs" / "DEAD_RECKONING_COVERAGE.md"
    expected = generate_dead_reckoning_coverage.render_markdown(generate_dead_reckoning_coverage.build_manifest())
    assert report_path.read_text(encoding="utf-8") == expected
