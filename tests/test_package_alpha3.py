from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import package_alpha3


def test_should_include_filters_generated_dirs() -> None:
    assert not package_alpha3.should_include("artifacts/reports/unity_workflow_report.json")
    assert not package_alpha3.should_include("build-alpha3/foo.txt")
    assert not package_alpha3.should_include("dist/alpha3/foo.txt")
    assert not package_alpha3.should_include(".pytest_cache/state")
    assert package_alpha3.should_include("docs/MESSAGE_COVERAGE.md")


def test_should_include_rejects_alpha3_host_bundle_files() -> None:
    assert not package_alpha3.should_include(
        "verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/host_report_manifest.json"
    )
    assert not package_alpha3.should_include(
        "artifacts/verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/host_report_manifest.json"
    )
    assert not package_alpha3.should_include(
        "verification_reports/alpha3_hosts/pbs-air.local-darwin-arm64/network_ingest_matrix.md"
    )


def test_repo_files_only_consults_tracked_paths(monkeypatch) -> None:
    monkeypatch.setattr(package_alpha3, "_git_paths", lambda *args: ["docs/MESSAGE_COVERAGE.md"] if not args else ["artifacts/reports/rogue.json"])
    monkeypatch.setattr(package_alpha3, "ROOT", Path(__file__).resolve().parents[1])

    files = package_alpha3.repo_files()

    assert files == ["docs/MESSAGE_COVERAGE.md"]


def test_write_checksums_skips_checksum_file(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.txt").write_text("a", encoding="utf-8")
    checksum_path = bundle / package_alpha3.CHECKSUM_FILE

    package_alpha3.write_checksums(bundle, ["a.txt", package_alpha3.CHECKSUM_FILE], checksum_path)

    text = checksum_path.read_text(encoding="utf-8")
    assert "a.txt" in text
    assert package_alpha3.CHECKSUM_FILE not in text
