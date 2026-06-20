from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fastdis.tools.lattice_shim import main as lattice_shim_main


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import lattice_workflow
import run_alpha4_release_audit


FIXTURE_DIR = ROOT / "integrations" / "lattice" / "examples"
DIS_FIXTURE = FIXTURE_DIR / "dis_entity_fixture.json"
TRACK_FIXTURE = FIXTURE_DIR / "lattice_track_fixture.json"
OBJECT_FIXTURE = FIXTURE_DIR / "object_fixture.json"
TASK_FIXTURE = FIXTURE_DIR / "task_fixture.json"


def test_alpha4_release_audit_reports_roundtrip_ready(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "dis-to-shim",
            str(DIS_FIXTURE),
            "--out-dir",
            str(tmp_path / "dis_to_shim"),
        ],
    )
    assert lattice_shim_main() == 0

    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "shim-to-dis",
            str(TRACK_FIXTURE),
            "--out-dir",
            str(tmp_path / "shim_to_dis"),
        ],
    )
    assert lattice_shim_main() == 0

    monkeypatch.setattr(
        "sys.argv",
        [
            "lattice_shim",
            "lab-state",
            "--object-fixture",
            str(OBJECT_FIXTURE),
            "--task-fixture",
            str(TASK_FIXTURE),
            "--out-dir",
            str(tmp_path / "lab_state"),
        ],
    )
    assert lattice_shim_main() == 0

    assert lattice_workflow.command_report(argparse.Namespace(out_root=str(tmp_path))) == 0

    generated = run_alpha4_release_audit.audit_generated_outputs(tmp_path)
    assert generated["generated_outputs_ready"] is True
    assert generated["roundtrip_proof"]["matched"] is True

    report_path = tmp_path / "alpha4_lattice_report.json"
    assert json.loads(report_path.read_text(encoding="utf-8"))["overall_status"] == "ready"
