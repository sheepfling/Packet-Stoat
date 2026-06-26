from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_unity_parity


def test_unity_grill_parity_current_alpha6_state_is_honest() -> None:
    report = check_unity_parity.build_report(ROOT / "docs" / "research" / "unity_grill_parity.yaml", "alpha6")

    assert report["status"] == "PASS"
    assert report["required"] >= 8
    assert report["verified"] >= 8
    assert any(row["name"] == "udp_receive" and row["bucket"] == "verified" for row in report["features"])
    assert any(row["name"] == "multicast_receive" and row["bucket"] == "verified" for row in report["features"])
    assert any(row["name"] == "stale_timeout" and row["bucket"] == "verified" for row in report["features"])
    assert any(row["name"] == "entity_mapping" and row["bucket"] == "verified" for row in report["features"])
    assert report["missing"] == 0


def test_unity_grill_parity_gate_passes_when_all_required_rows_are_verified(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.yaml"
    impl = tmp_path / "impl.cs"
    test_file = tmp_path / "test.cs"
    verify = tmp_path / "verify.py"
    sample = tmp_path / "sample.md"
    doc = tmp_path / "doc.md"
    for path in (impl, test_file, verify, sample, doc):
        path.write_text("ok\n", encoding="utf-8")
    matrix.write_text(
        "\n".join(
            [
                "features:",
                "  udp_receive:",
                "    fastdis: playmode_verified",
                "    required_for: [alpha6]",
                f"    implementation: [{impl}]",
                f"    tests: [{test_file}]",
                f"    verification: [{verify}]",
                f"    samples: [{sample}]",
                f"    docs: [{doc}]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = check_unity_parity.build_report(matrix, "alpha6")

    assert report["status"] == "PASS"
    assert report["verified"] == 1
    assert report["missing"] == 0


def test_unity_grill_parity_json_main_reports_alpha7_pass(capsys) -> None:
    rc = check_unity_parity.main(
        [
            "--matrix",
            str(ROOT / "docs" / "research" / "unity_grill_parity.yaml"),
            "--milestone",
            "alpha7",
            "--format",
            "json",
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["status"] == "PASS"
    assert out["verified"] >= 8
    assert any(row["name"] == "udp_send" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "dead_reckoning" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "fire_event_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "start_resume_event_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "heartbeat_threshold_send" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "ground_clamp_and_culling" and row["bucket"] == "verified" for row in out["features"])
    assert out["missing"] == 0


def test_unity_grill_parity_json_main_reports_alpha8_pass(capsys) -> None:
    rc = check_unity_parity.main(
        [
            "--matrix",
            str(ROOT / "docs" / "research" / "unity_grill_parity.yaml"),
            "--milestone",
            "alpha8",
            "--format",
            "json",
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["status"] == "PASS"
    assert out["verified"] >= 6
    assert any(row["name"] == "designator_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "electromagnetic_emission_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "signal_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "multicast_and_broadcast_send" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "orientation_visual_verification" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "wildcard_entity_mapping" and row["bucket"] == "verified" for row in out["features"])
    assert out["missing"] == 0


def test_unity_grill_parity_json_main_reports_beta1_remaining_blockers(capsys) -> None:
    rc = check_unity_parity.main(
        [
            "--matrix",
            str(ROOT / "docs" / "research" / "unity_grill_parity.yaml"),
            "--milestone",
            "beta1",
            "--format",
            "json",
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert out["status"] == "FAIL"
    assert out["verified"] >= 9
    assert any(row["name"] == "collision_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "collision_elastic_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "transmitter_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "receiver_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "iff_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "attribute_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "entity_damage_status_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "directed_energy_fire_surface" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "cross_engine_equivalence" and row["bucket"] == "verified" for row in out["features"])
    assert any(row["name"] == "head_to_head_benchmark" and row["bucket"] == "implemented" for row in out["features"])
    assert any(row["name"] == "head_to_head_benchmark" for row in out["failures"])
    assert all(row["name"] != "cross_engine_equivalence" for row in out["failures"])
