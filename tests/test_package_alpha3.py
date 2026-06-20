from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import package_alpha3


def test_should_include_filters_generated_dirs() -> None:
    assert not package_alpha3.should_include("build-alpha3/foo.txt")
    assert not package_alpha3.should_include("dist/alpha3/foo.txt")
    assert not package_alpha3.should_include(".pytest_cache/state")
    assert package_alpha3.should_include("docs/MESSAGE_COVERAGE.md")


def test_should_include_rejects_unexpected_alpha3_host_bundle_files() -> None:
    assert package_alpha3.should_include(
        "verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/host_report_manifest.json"
    )
    assert package_alpha3.should_include(
        "verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/network_ingest_matrix.md"
    )
    assert not package_alpha3.should_include(
        "verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/network_ingest_matrix 2.json"
    )
    assert not package_alpha3.should_include(
        "verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/random_notes.txt"
    )


def test_write_checksums_skips_checksum_file(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.txt").write_text("a", encoding="utf-8")
    checksum_path = bundle / package_alpha3.CHECKSUM_FILE

    package_alpha3.write_checksums(bundle, ["a.txt", package_alpha3.CHECKSUM_FILE], checksum_path)

    text = checksum_path.read_text(encoding="utf-8")
    assert "a.txt" in text
    assert package_alpha3.CHECKSUM_FILE not in text
