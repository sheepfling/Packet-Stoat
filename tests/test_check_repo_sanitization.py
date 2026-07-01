from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_repo_sanitization


def test_find_violations_rejects_tracked_generated_outputs() -> None:
    violations = check_repo_sanitization.find_violations(
        [
            "artifacts/reports/unity_install_smoke_windows.json",
            "artifacts/verification_reports/alpha2_hosts/host-a/host_report_manifest.json",
            "verification_reports/alpha3_current/network_ingest_matrix.json",
            "docs/UNITY_CROSS_HOST_SIGNOFF.md",
        ]
    )

    assert violations == [
        "artifacts/reports/unity_install_smoke_windows.json",
        "artifacts/verification_reports/alpha2_hosts/host-a/host_report_manifest.json",
        "verification_reports/alpha3_current/network_ingest_matrix.json",
    ]


def test_find_violations_allows_source_paths() -> None:
    violations = check_repo_sanitization.find_violations(
        [
            "docs/CROSS_HOST_SIGNOFF.md",
            "tools/stage_alpha2_host_report.py",
            "tests/test_package_alpha3.py",
        ]
    )

    assert violations == []
