from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
import sys

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_cesium_engine_matrix


def test_build_payload_summarizes_mixed_engine_states(tmp_path: Path) -> None:
    unreal_57 = tmp_path / "unreal57.json"
    unreal_57.write_text(
        json.dumps(
            {
                "failure_class": "verified-build",
                "engine_version": "5.7",
                "build_report_json": "u57-build.json",
                "install_smoke_json": "u57-install.json",
                "build_report": {
                    "status": "ok",
                    "resolved_msvc_toolchain": {
                        "selected_version": "14.44.35228",
                        "selected_folder_version": "14.44.35207",
                        "selection_reason": "preferred",
                    },
                },
                "install_smoke_report": {"status": "pass"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    unreal_58 = tmp_path / "unreal58.json"
    unreal_58.write_text(
        json.dumps(
            {
                "failure_class": "verified-build",
                "engine_version": "5.8",
                "build_report_json": "u58-build.json",
                "install_smoke_json": "u58-install.json",
                "build_report": {
                    "status": "ok",
                    "resolved_msvc_toolchain": {
                        "selected_version": "14.50.35735",
                        "selected_folder_version": "14.50.35717",
                        "selection_reason": "preferred",
                    },
                },
                "install_smoke_report": {"status": "pass"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    unity = tmp_path / "unity.json"
    unity.write_text(
        json.dumps(
            {
                "failure_class": "compile-or-import",
                "build_report_json": "unity-build.json",
                "build_log": "unity.log",
                "build_report": {
                    "unity_version": "6000.5.1f1",
                    "status": "fail",
                    "failure_tail": ["error CS0246 missing type"],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    godot = tmp_path / "godot.json"
    godot.write_text(
        json.dumps(
            {
                "failure_class": "compile-or-link",
                "build_report_json": "godot-build.json",
                "build_log": "godot.log",
                "build_report": {
                    "godot_version": "4.7",
                    "status": "fail",
                    "failure_tail": ["fatal error C1083 missing header"],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    args = build_cesium_engine_matrix.parse_args(
        [
            "--unreal-57",
            str(unreal_57),
            "--unreal-58",
            str(unreal_58),
            "--unity",
            str(unity),
            "--godot",
            str(godot),
            "--json-out",
            str(tmp_path / "matrix.json"),
            "--md-out",
            str(tmp_path / "matrix.md"),
        ]
    )
    payload = build_cesium_engine_matrix.build_payload(args)

    assert payload["overall_status"] == "fail"
    assert payload["summary"]["passing_count"] == 2
    assert payload["goal"]["current_phase"] == "plugin_proofs"
    assert payload["goal"]["next_phase"] == "fix-plugin-proof-lanes"
    assert payload["gates"]["plugin_proofs"]["status"] == "fail"
    assert payload["gates"]["plugin_proofs"]["blocked_lanes"] == ["unity-6000.5", "godot-4.7"]
    assert payload["gates"]["minimal_example_proofs"]["status"] == "blocked"
    unreal_row = next(row for row in payload["lanes"] if row["lane"] == "unreal-5.8")
    assert unreal_row["selected_compiler_version"] == "14.50.35735"
    assert unreal_row["selected_folder_version"] == "14.50.35717"
    unity_row = next(row for row in payload["lanes"] if row["lane"] == "unity-6000.5")
    assert unity_row["failure_class"] == "compile-or-import"
    assert "CS0246" in unity_row["detail"]


def test_missing_report_is_marked_missing(tmp_path: Path) -> None:
    args = build_cesium_engine_matrix.parse_args(
        [
            "--unreal-57",
            str(tmp_path / "missing57.json"),
            "--unreal-58",
            str(tmp_path / "missing58.json"),
            "--unity",
            str(tmp_path / "missing-unity.json"),
            "--godot",
            str(tmp_path / "missing-godot.json"),
        ]
    )

    payload = build_cesium_engine_matrix.build_payload(args)

    assert payload["overall_status"] == "needs-attention"
    assert payload["summary"]["missing_count"] == 4
    assert payload["goal"]["next_phase"] == "refresh-missing-plugin-proofs"
    assert payload["gates"]["minimal_example_proofs"]["status"] == "blocked"


def test_plugin_green_matrix_unblocks_minimal_examples(tmp_path: Path) -> None:
    unreal = {
        "failure_class": "verified-build",
        "engine_version": "5.7",
        "build_report": {"status": "ok"},
        "install_smoke_report": {"status": "pass"},
    }
    unity = {
        "failure_class": "verified-build",
        "build_report": {"unity_version": "6000.5.1f1", "status": "pass"},
    }
    godot = {
        "failure_class": "verified-build",
        "build_report": {"godot_version": "4.7", "status": "pass"},
    }
    paths = {}
    for name, payload in {
        "unreal57": unreal,
        "unreal58": {**unreal, "engine_version": "5.8"},
        "unity": unity,
        "godot": godot,
    }.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        paths[name] = path

    args = build_cesium_engine_matrix.parse_args(
        [
            "--unreal-57",
            str(paths["unreal57"]),
            "--unreal-58",
            str(paths["unreal58"]),
            "--unity",
            str(paths["unity"]),
            "--godot",
            str(paths["godot"]),
        ]
    )

    payload = build_cesium_engine_matrix.build_payload(args)

    assert payload["overall_status"] == "pass"
    assert payload["goal"]["current_phase"] == "minimal_example_proofs"
    assert payload["goal"]["next_phase"] == "build-minimal-example-proofs"
    assert payload["gates"]["plugin_proofs"]["blocked_lanes"] == []
    assert payload["gates"]["minimal_example_proofs"]["status"] == "ready"
