from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import generate_workspace_ci_matrix


def test_build_document_tracks_manifest_python_policy() -> None:
    document = generate_workspace_ci_matrix.build_document()

    assert document["schema"] == "packet_stoat.workspace_ci_matrix.v1"
    assert document["preferred_python_version"] == "3.14"
    assert [row["python-version"] for row in document["python_green"]["include"] if row["host_class"] == "windows"] == [
        "3.12",
        "3.13",
        "3.14",
    ]
    assert any(row["route"] == "unreal-native" and row["surface_version"] == "5.7" for row in document["workspace_ci"]["include"])
    assert any(row["route"] == "unreal-native" and row["surface_version"] == "5.8" for row in document["workspace_ci"]["include"])
    assert {row["host_class"] for row in document["native_green"]["include"]} == {"windows", "macos", "linux"}
    assert all(row["surface"] == "python" and row["target"] == "host" for row in document["workspace_ci_host_python"]["include"])
    assert all(row["surface"] in {"godot", "unity", "unreal"} for row in document["workspace_ci_declared_engine"]["include"])
    assert all(row["target"] != "host" for row in document["workspace_ci_declared_cross_build"]["include"])


def test_github_outputs_reads_checked_in_matrix(tmp_path: Path) -> None:
    document = generate_workspace_ci_matrix.build_document()
    matrix_path = tmp_path / "workspace-ci-matrix.json"
    matrix_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    output_path = tmp_path / "github-output.txt"

    rc = generate_workspace_ci_matrix.main(
        [
            "github-outputs",
            "--path",
            str(matrix_path),
            "--output",
            str(output_path),
        ]
    )

    assert rc == 0
    output = output_path.read_text(encoding="utf-8")
    assert "preferred_python=3.14" in output
    assert "symbols_proof_node=22" in output
    assert "python_green=" in output
    assert "native_green=" in output
    assert "workspace_ci=" in output
    assert "workspace_ci_host_python=" in output
    assert "workspace_ci_declared_engine=" in output
    assert "workspace_ci_declared_cross_build=" in output
