from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import generate_zorn_short_matrix  # noqa: E402


def test_zorn_short_matrix_compacts_proven_gap_unknown_and_skip_rows(tmp_path: Path) -> None:
    report_root = tmp_path / "alpha5"
    for directory in (
        report_root / "lattice_zorn_rest_sdk",
        report_root / "lattice_zorn_grpc",
        report_root / "lattice_zorn_entity_parity",
        report_root / "lattice_zorn_auth_lifecycle",
        report_root / "lattice_zorn_auth_lifecycle_alpha1_3",
    ):
        directory.mkdir(parents=True)

    (report_root / "lattice_zorn_rest_sdk" / "zorn_rest_sdk_probe_report.json").write_text(
        json.dumps({"overall_status": "ready", "checks": [{"name": "rest_check", "status": "passed", "detail": "ok"}]}),
        encoding="utf-8",
    )
    (report_root / "lattice_zorn_grpc" / "zorn_grpc_probe_report.json").write_text(
        json.dumps({"overall_status": "ready", "checks": [{"name": "grpc_check", "status": "passed", "detail": "ok"}]}),
        encoding="utf-8",
    )
    (report_root / "lattice_zorn_entity_parity" / "zorn_entity_parity_probe_report.json").write_text(
        json.dumps({"overall_status": "ready", "checks": [{"name": "parity_check", "status": "passed", "detail": "ok"}]}),
        encoding="utf-8",
    )
    (report_root / "lattice_zorn_auth_lifecycle" / "zorn_auth_lifecycle_probe_report.json").write_text(
        json.dumps(
            {
                "overall_status": "ready-with-gaps",
                "checks": [{"name": "auth_check", "status": "passed", "detail": "ok"}],
                "gaps": ["token expiry not enforced"],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "lattice_zorn_auth_lifecycle_alpha1_3" / "zorn_auth_lifecycle_probe_report.json").write_text(
        json.dumps(
            {
                "overall_status": "ready-with-gaps",
                "checks": [
                    {"name": "rest_static_x_api_key_accepted", "status": "passed", "detail": "ok"},
                    {"name": "rest_auth_mode_none_accepts_without_headers", "status": "passed", "detail": "ok"},
                    {"name": "grpc_static_x_api_key_accepted", "status": "passed", "detail": "ok"},
                    {"name": "grpc_auth_mode_none_accepts_without_headers", "status": "passed", "detail": "ok"},
                    {"name": "rest_oauth_client_credentials", "status": "passed", "detail": "ok"},
                    {"name": "rest_oauth_issued_token", "status": "passed", "detail": "ok"},
                    {"name": "grpc_oauth_issued_token", "status": "passed", "detail": "ok"},
                ],
                "gaps": [
                    "REST OAuth tokens use a fixed expires_in and are not actually expired or rotated by Zorn.",
                    "OAuth refresh semantics are not exposed on either REST or gRPC.",
                    "Issued OAuth tokens currently alias the same static bearer token state rather than a distinct lifecycle.",
                    "Scope values are echoed on REST token issuance but are not enforced on REST or gRPC requests.",
                    "gRPC currently enforces bearer metadata but does not expose a sandbox-header equivalent.",
                ],
            }
        ),
        encoding="utf-8",
    )

    matrix = generate_zorn_short_matrix.build_short_matrix(report_root)

    assert matrix["backend"] == "external-zorn"
    assert matrix["summary"]["total"] == len(matrix["rows"])
    assert matrix["summary"]["proven"] >= 6
    assert matrix["summary"]["gap"] >= 4
    assert matrix["summary"]["unknown"] >= 3
    assert matrix["summary"]["live_lattice_skip"] >= 4

    assert any(row["surface"] == "rest_sdk" and row["proven"] for row in matrix["rows"])
    assert any(row["surface"].startswith("auth_lifecycle") and row["gap"] for row in matrix["rows"])
    assert any(row["surface"].startswith("real_lattice_unknown") and row["unknown"] for row in matrix["rows"])
    assert any(row["surface"] == "grpc.static.x_api_key" and row["live_lattice_skip"] for row in matrix["rows"])

    md = generate_zorn_short_matrix._render_markdown(matrix)
    assert "| Surface | Proven | Gap | Unknown | Live-Lattice-skip | Evidence | Note |" in md
