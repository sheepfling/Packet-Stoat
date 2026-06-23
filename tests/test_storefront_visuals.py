from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
STOREFRONT = ROOT / "media" / "storefront" / "fab"
EXPECTED = [
    "01_hero_1920x1080.svg",
    "02_pipeline_1920x1080.svg",
    "03_coverage_ladder_1920x1080.svg",
    "04_symbols_handoff_1920x1080.svg",
    "05_cabi_portability_1920x1080.svg",
    "06_core_plugin_boundary_1920x1080.svg",
    "07_unreal_grill_parity_1920x1080.svg",
]
FORBIDDEN_CLAIMS = (
    "all PDU bodies",
    "all DIS PDUs supported",
    "complete MIL-STD-2525",
    "production symbology library",
)


def test_storefront_svg_kit_has_expected_assets() -> None:
    assert sorted(path.name for path in STOREFRONT.glob("*.svg")) == EXPECTED


def test_storefront_svg_assets_are_fab_sized() -> None:
    for name in EXPECTED:
        root = ET.parse(STOREFRONT / name).getroot()
        assert root.attrib["width"] == "1920"
        assert root.attrib["height"] == "1080"
        assert root.attrib["viewBox"] == "0 0 1920 1080"


def test_storefront_visuals_do_not_overclaim_coverage() -> None:
    for path in sorted(STOREFRONT.glob("*.svg")):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for claim in FORBIDDEN_CLAIMS:
            assert claim.lower() not in lowered, f"{path} contains forbidden claim: {claim}"


def test_storefront_visuals_doc_names_non_claims() -> None:
    text = (ROOT / "docs" / "STOREFRONT_VISUALS.md").read_text(encoding="utf-8")
    assert "Do not claim:" in text
    assert "Do claim:" in text


def test_unreal_fab_draft_is_packaged_and_conservative() -> None:
    draft = ROOT / "examples" / "unreal" / "FastDis" / "Docs" / "FAB_DRAFT.md"
    text = draft.read_text(encoding="utf-8")
    build_script = (ROOT / "tools" / "build_unreal_plugin.py").read_text(encoding="utf-8")
    plugin_readme = (ROOT / "examples" / "unreal" / "FastDis" / "README.md").read_text(encoding="utf-8")

    assert "Boring core. Useful adapters. Honest coverage." in text
    assert "Do Not Claim Yet" in text
    assert "Full semantic body decoding for every DIS PDU" in text
    assert "Required Final Screenshots" in text
    assert "Docs/FAB_DRAFT.md" in build_script
    assert "Docs/FAB_DRAFT.md" in plugin_readme
