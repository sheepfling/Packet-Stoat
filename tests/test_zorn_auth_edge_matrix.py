from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import generate_zorn_auth_edge_matrix  # noqa: E402


def test_zorn_auth_edge_matrix_tracks_setup_heavy_paths(tmp_path: Path) -> None:
    report_root = tmp_path / "alpha5"
    auth_dir = report_root / "lattice_zorn_auth_lifecycle_alpha1_3"
    auth_dir.mkdir(parents=True)
    (auth_dir / "zorn_auth_lifecycle_probe_report.json").write_text(
        json.dumps(
            {
                "overall_status": "ready-with-gaps",
                "checks": [
                    {"name": "rest_x_api_key_accepted", "status": "passed", "detail": "ok"},
                    {"name": "rest_auth_mode_none_accepts_without_headers", "status": "passed", "detail": "ok"},
                    {"name": "grpc_x_api_key_accepted", "status": "passed", "detail": "ok"},
                    {"name": "grpc_auth_mode_none_accepts_without_headers", "status": "passed", "detail": "ok"},
                ],
                "gaps": ["scope not enforced"],
            }
        ),
        encoding="utf-8",
    )

    matrix = generate_zorn_auth_edge_matrix.build_matrix(report_root)

    assert matrix["backend"] == "external-zorn"
    assert matrix["zorn_tag"]
    assert matrix["summary"]["total"] == len(matrix["rows"])
    assert any(row["surface"] == "rest.static.x_api_key" for row in matrix["rows"])
    assert any(row["surface"] == "grpc.auth_mode.none" for row in matrix["rows"])
    assert matrix["gaps"][0]["details"] == ["scope not enforced"]
