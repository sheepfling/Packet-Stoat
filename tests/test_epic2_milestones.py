from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _ensure_report() -> dict[str, object]:
    path = ROOT / "generated" / "epic2_milestones.json"
    if not path.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_epic2_milestones.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return json.loads(path.read_text(encoding="utf-8"))


def test_epic2_milestone_report_tracks_all_five_milestones() -> None:
    report = _ensure_report()

    assert report["schema"] == "fastdis.epic2.milestones.v1"
    assert report["overall_status"] in {"in_progress", "complete", "missing_evidence"}
    assert len(report["milestones"]) == 5

    names = {row["name"] for row in report["milestones"]}
    assert "Milestone 1: 141-Row Generated Truth Table" in names
    assert "Milestone 2: Generic Wire And Field Coverage" in names
    assert "Milestone 3: Typed Semantic PDU Waves" in names
    assert "Milestone 4: Cross-Engine And Lattice/Zorn Parity" in names
    assert "Milestone 5: Evidence And Release Gates" in names


def test_epic2_milestone_report_reflects_current_partial_parity() -> None:
    report = _ensure_report()
    rows = {row["criterion_name"]: row for row in report["milestones"]}

    assert rows["141-row generated truth"]["status"] == "complete"
    assert rows["Generic wire and field coverage"]["status"] == "complete"
    assert rows["Typed semantic waves"]["status"] == "complete"
    assert rows["Cross-engine and Lattice/Zorn parity"]["status"] == "complete"
    assert rows["Evidence and release gates"]["status"] in {"partial", "complete"}
    assert any("unity_deep_rows=141" == item for item in rows["Cross-engine and Lattice/Zorn parity"]["progress_summary"])


def test_epic2_milestone_report_is_linked_from_core_docs() -> None:
    milestone_doc = (ROOT / "docs" / "EPIC2_MILESTONES.md").read_text(encoding="utf-8")
    readme = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    buildout = (ROOT / "docs" / "EPIC2_FULL_DIS_BUILDOUT.md").read_text(encoding="utf-8")
    audit = (ROOT / "docs" / "EPIC2_AUDIT.md").read_text(encoding="utf-8")

    assert "Epic 2 milestone" in milestone_doc
    assert "[Epic 2 milestones](EPIC2_MILESTONES.md)" in readme
    assert "EPIC2_MILESTONES.md" in roadmap
    assert "EPIC2_MILESTONES.md" in buildout
    assert "EPIC2_MILESTONES.md" in audit


def test_generate_epic2_milestones_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_epic2_milestones.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
