from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import generate_zorn_gap_manifest  # noqa: E402


def test_zorn_gap_manifest_collects_probe_statuses(tmp_path: Path) -> None:
    report_root = tmp_path / "alpha5"
    rest_dir = report_root / "lattice_zorn_rest_sdk"
    grpc_dir = report_root / "lattice_zorn_grpc"
    parity_dir = report_root / "lattice_zorn_entity_parity"
    auth_dir = report_root / "lattice_zorn_auth_lifecycle"
    for directory in (rest_dir, grpc_dir, parity_dir, auth_dir):
        directory.mkdir(parents=True)

    (rest_dir / "zorn_rest_sdk_probe_report.json").write_text(
        json.dumps({"overall_status": "ready", "checks": [{"name": "rest_check", "status": "passed"}]}),
        encoding="utf-8",
    )
    (grpc_dir / "zorn_grpc_probe_report.json").write_text(
        json.dumps({"overall_status": "ready", "checks": [{"name": "grpc_check", "status": "passed"}]}),
        encoding="utf-8",
    )
    (parity_dir / "zorn_entity_parity_probe_report.json").write_text(
        json.dumps({"overall_status": "ready", "checks": [{"name": "parity_check", "status": "passed"}]}),
        encoding="utf-8",
    )
    (auth_dir / "zorn_auth_lifecycle_probe_report.json").write_text(
        json.dumps(
            {
                "overall_status": "ready-with-gaps",
                "checks": [{"name": "auth_check", "status": "passed"}],
                "gaps": ["token expiry not enforced"],
            }
        ),
        encoding="utf-8",
    )

    manifest = generate_zorn_gap_manifest.build_manifest(report_root)

    assert manifest["backend"] == "external-zorn"
    assert "rest_sdk" in manifest["proven_surfaces"]
    assert "grpc" in manifest["proven_surfaces"]
    assert "entity_parity" in manifest["proven_surfaces"]
    auth_surface = next(surface for surface in manifest["surface_statuses"] if surface["name"] == "auth_lifecycle")
    assert auth_surface["status"] == "gap"
    assert auth_surface["gaps"] == ["token expiry not enforced"]
    assert any(gap["surface"] == "backend_cheat_surface" for gap in manifest["gaps"])
