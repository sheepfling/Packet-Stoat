from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_epic2_buildout_doc_tracks_baseline_and_milestones() -> None:
    doc = read(ROOT / "docs" / "EPIC2_FULL_DIS_BUILDOUT.md")

    assert "Current Baseline" in doc
    assert "141 / 141" in doc
    assert "116 / 141" in doc
    assert "40 / 141" in doc
    assert "10 / 141" in doc
    assert "101 / 141" in doc
    assert "Milestone 1: 141-Row Generated Truth Table" in doc
    assert "Milestone 2: Generic Wire And Field Coverage" in doc
    assert "Milestone 3: Typed Semantic PDU Waves" in doc
    assert "Milestone 4: Cross-Engine And Lattice/Zorn Parity" in doc
    assert "Milestone 5: Evidence And Release Gates" in doc


def test_epic2_buildout_doc_keeps_proof_commands_visible() -> None:
    doc = read(ROOT / "docs" / "EPIC2_FULL_DIS_BUILDOUT.md")

    assert "tests/test_pdu_coverage_manifest.py" in doc
    assert "tests/test_typed_pdu_parsers.py" in doc
    assert "tests/test_semantic_pdu_parsers.py" in doc
    assert "tests/test_pdu_logging.py" in doc
    assert "tests/test_lattice_dis_mapping_plan.py" in doc
    assert "EPIC2_SEMANTIC_WAVES.md" in doc
    assert "python tools/check_generated_fresh.py" in doc
    assert "python tools/generate_evidence_pack.py --clean --render-symbols never" in doc
    assert "python tools/check_evidence_pack.py build/verification_reports/evidence/latest/manifest.json" in doc
    assert "python tools/check_docs.py" in doc


def test_epic2_buildout_doc_is_linked_from_core_planning_docs() -> None:
    doc = read(ROOT / "docs" / "EPIC2_FULL_DIS_BUILDOUT.md")
    backlog = read(ROOT / "docs" / "PRODUCT_BACKLOG.md")
    roadmap = read(ROOT / "docs" / "ROADMAP.md")
    docs_index = read(ROOT / "docs" / "README.md")
    full_coverage = read(ROOT / "docs" / "DIS_FULL_COVERAGE_PLAN.md")
    waves = read(ROOT / "docs" / "EPIC2_SEMANTIC_WAVES.md")

    assert "PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout" in doc
    assert "EPIC2_FULL_DIS_BUILDOUT.md" in backlog
    assert "EPIC2_FULL_DIS_BUILDOUT.md" in roadmap
    assert "[Epic 2 full DIS buildout](EPIC2_FULL_DIS_BUILDOUT.md)" in docs_index
    assert "[Epic 2 semantic waves](EPIC2_SEMANTIC_WAVES.md)" in docs_index
    assert "EPIC2_FULL_DIS_BUILDOUT.md" in full_coverage
    assert "Wave 1: State And Lifecycle" in waves
