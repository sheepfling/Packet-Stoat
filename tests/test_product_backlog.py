from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_product_backlog_declares_two_epics_and_ordering_rule() -> None:
    backlog = read(ROOT / "docs" / "PRODUCT_BACKLOG.md")

    assert "Epic 1: Unreal GRILL DIS Parity First" in backlog
    assert "Epic 2: Full DIS 6/7 PDU Feature Buildout" in backlog
    assert "Epic 1 is the first product gate" in backlog
    assert "141 versioned DIS 6/7 PDU rows" in backlog


def test_grill_parity_milestones_have_goal_blurbs_and_acceptance() -> None:
    backlog = read(ROOT / "docs" / "PRODUCT_BACKLOG.md")

    for milestone in [
        "Milestone 1: GRILL Core Receive Parity",
        "Milestone 2: GRILL PDU Surface Parity",
        "Milestone 3: Fab Product Parity",
        "Milestone 4: Beat GRILL Differentiators",
    ]:
        assert milestone in backlog

    assert backlog.count("Goal blurb:") >= 7
    assert "UFastDisUdpReceiverComponent" in backlog
    assert "UFastDisEntityMappingDataAsset" in backlog
    assert "Start/Resume and Stop/Freeze" in backlog
    assert "Electromagnetic Emission, Signal, and Designator" in backlog


def test_full_dis_milestones_keep_generated_coverage_gates_visible() -> None:
    backlog = read(ROOT / "docs" / "PRODUCT_BACKLOG.md")

    for milestone in [
        "Milestone 1: 141-Row Generated Truth Table",
        "Milestone 2: Generic Wire And Field Coverage",
        "Milestone 3: Typed Semantic PDU Waves",
        "Milestone 4: Cross-Engine And Lattice/Zorn Parity",
        "Milestone 5: Evidence And Release Gates",
    ]:
        assert milestone in backlog

    assert "CI fails if a known row has `none` behavior" in backlog
    assert "Raw-sidecar preservation" in backlog
    assert "strict full-duplex, lossy ingress, lossy egress" in backlog


def test_backlog_is_linked_from_roadmap_index_and_supporting_plans() -> None:
    docs_index = read(ROOT / "docs" / "README.md")
    roadmap = read(ROOT / "docs" / "ROADMAP.md")
    grill = read(ROOT / "docs" / "UNREAL_GRILL_PARITY.md")
    full_coverage = read(ROOT / "docs" / "DIS_FULL_COVERAGE_PLAN.md")
    fab_worklist = read(ROOT / "docs" / "UNREAL_FAB_ASSET_WORKLIST.md")
    differentiator_audit = read(ROOT / "docs" / "EPIC1_DIFFERENTIATOR_AUDIT.md")
    fab_draft = read(ROOT / "examples" / "unreal" / "FastDis" / "Docs" / "FAB_DRAFT.md")
    backlog = read(ROOT / "docs" / "PRODUCT_BACKLOG.md")

    assert "[Product backlog](PRODUCT_BACKLOG.md)" in docs_index
    assert "[Epic 1 differentiator audit](EPIC1_DIFFERENTIATOR_AUDIT.md)" in docs_index
    assert "[Unreal Fab asset worklist](UNREAL_FAB_ASSET_WORKLIST.md)" in docs_index
    assert "[Alpha12 final polish plan](releases/ALPHA12_FINAL_POLISH_PLAN.md)" in docs_index
    assert "[Alpha12 closeout audit](releases/ALPHA12_CLOSEOUT_AUDIT.md)" in docs_index
    assert "[Alpha12 publish decision](releases/ALPHA12_PUBLISH_DECISION.md)" in docs_index
    assert "PRODUCT_BACKLOG.md#epic-1-unreal-grill-dis-parity-first" in roadmap
    assert "PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout" in roadmap
    assert "EPIC1_DIFFERENTIATOR_AUDIT.md" in roadmap
    assert "UNREAL_FAB_ASSET_WORKLIST.md" in roadmap
    assert "PRODUCT_BACKLOG.md#epic-1-unreal-grill-dis-parity-first" in grill
    assert "EPIC1_DIFFERENTIATOR_AUDIT.md" in grill
    assert "UNREAL_FAB_ASSET_WORKLIST.md" in grill
    assert "PRODUCT_BACKLOG.md#epic-2-full-dis-67-pdu-feature-buildout" in full_coverage
    assert "Deterministic replay verification" in differentiator_audit
    assert "Evidence-pack receipts" in differentiator_audit
    assert "Non-Claims" in differentiator_audit
    assert "FastDis_Demo.umap" in fab_worklist
    assert "tools/create_unreal_fab_demo_assets.py" in fab_worklist
    assert "WBP_FastDisRuntimeStatus.uasset" in fab_worklist
    assert "DA_FastDisEntityMappings.uasset" in fab_worklist
    assert "pdu_event_marker.png" in fab_worklist
    assert "check_unreal_fab_readiness.py --strict" in fab_worklist
    assert "UNREAL_FAB_ASSET_WORKLIST.md" in fab_draft
    assert "ALPHA12_CLOSEOUT_AUDIT.md" in fab_draft or "ALPHA12_CLOSEOUT_AUDIT.md" in backlog
    assert "ALPHA12_PUBLISH_DECISION.md" in backlog
