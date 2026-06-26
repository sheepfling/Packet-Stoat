from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import import_unreal_grill_mapping_manifest as importer


def test_import_manifest_preserves_grill_row_override_with_priority() -> None:
    payload = {
        "product": "GRILL DIS for Unreal",
        "rows": [
            {
                "friendly_name": "Aircraft A",
                "dis_entity": "/Game/BP/BP_AircraftA.BP_AircraftA_C",
                "associated_dis_enumerations": [
                    {"kind": 1, "domain": 2, "country": 225, "category": 1, "subcategory": 1, "specific": 0, "extra": 0}
                ],
            },
            {
                "friendly_name": "Aircraft B",
                "dis_entity": "/Game/BP/BP_AircraftB.BP_AircraftB_C",
                "associated_dis_enumerations": [
                    {"kind": 1, "domain": 2, "country": 225, "category": 1, "subcategory": 1, "specific": 0, "extra": 0}
                ],
            },
        ],
    }

    fastdis_manifest, report = importer.import_manifest(payload, source_route="AF-GRILL/DISPluginForUnreal@ue5", input_manifest="manifest.json")
    assert report["duplicate_exact_enumerations"] == 1
    assert fastdis_manifest["rows"][0]["Priority"] == 1
    assert fastdis_manifest["rows"][1]["Priority"] == 2
    assert fastdis_manifest["rows"][0]["ActorClassSoftPath"] == "/Game/BP/BP_AircraftA.BP_AircraftA_C"
    assert fastdis_manifest["rows"][1]["SourceActorClassPath"] == "/Game/BP/BP_AircraftB.BP_AircraftB_C"
    assert "later-row override behavior" in report["notes"][0]


def test_import_manifest_validates_actor_classes_against_search_root(tmp_path: Path) -> None:
    (tmp_path / "Content" / "Aircrafts" / "F18").mkdir(parents=True)
    resolved_asset = tmp_path / "Content" / "Aircrafts" / "F18" / "BP_West_Fighter_F18C_Showcase.uasset"
    resolved_asset.write_text("asset", encoding="utf-8")

    payload = {
        "product": "GRILL DIS for Unreal",
        "rows": [
            {
                "friendly_name": "Resolved Aircraft",
                "dis_entity": "/Game/Aircrafts/F18/BP_West_Fighter_F18C_Showcase.BP_West_Fighter_F18C_Showcase_C",
                "associated_dis_enumerations": [
                    {"kind": 1, "domain": 2, "country": 225, "category": 1, "subcategory": 1, "specific": 0, "extra": 0}
                ],
            },
            {
                "friendly_name": "Missing Aircraft",
                "dis_entity": "/Game/Aircrafts/F18/BP_DoesNotExist.BP_DoesNotExist_C",
                "associated_dis_enumerations": [
                    {"kind": 1, "domain": 2, "country": 225, "category": 2, "subcategory": 1, "specific": 0, "extra": 0}
                ],
            },
        ],
    }

    fastdis_manifest, report = importer.import_manifest(
        payload,
        source_route="AF-GRILL/DISPluginForUnreal@ue5",
        input_manifest="manifest.json",
        search_roots=[tmp_path],
    )
    assert report["resolved_actor_classes"] == 1
    assert report["unresolved_actor_classes"] == 1
    assert fastdis_manifest["rows"][0]["ActorResolution"]["status"] == "resolved"
    assert fastdis_manifest["rows"][0]["ActorResolution"]["resolved_path"] == str(resolved_asset.resolve())
    assert fastdis_manifest["rows"][1]["ActorResolution"]["status"] == "unresolved"


def test_import_manifest_chooses_most_specific_primary_and_keeps_aliases() -> None:
    payload = {
        "product": "GRILL DIS for Unreal",
        "rows": [
            {
                "friendly_name": "Ground Vehicle",
                "dis_entity": "/Game/BP/BP_GroundVehicle.BP_GroundVehicle_C",
                "associated_dis_enumerations": [
                    {"kind": 1, "domain": 1, "country": 225, "category": 1, "subcategory": -1, "specific": -1, "extra": -1},
                    {"kind": 1, "domain": 1, "country": 225, "category": 1, "subcategory": 3, "specific": 2, "extra": 0},
                ],
            }
        ],
    }

    fastdis_manifest, report = importer.import_manifest(payload, source_route="AF-GRILL/DISPluginForUnreal@ue5", input_manifest="manifest.json")
    row = fastdis_manifest["rows"][0]
    assert row["EntityType"]["Subcategory"] == 3
    assert row["AliasEntityTypes"][0]["Subcategory"] == -1
    assert report["wildcard_enumerations"] == 1


def test_main_writes_expected_outputs(tmp_path: Path) -> None:
    manifest_path = tmp_path / "grill_manifest.json"
    fastdis_out = tmp_path / "fastdis_manifest.json"
    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"
    manifest_path.write_text(
        json.dumps(
            {
                "product": "GRILL DIS for Unreal",
                "rows": [
                    {
                        "friendly_name": "Aircraft",
                        "dis_entity": "/Game/BP/BP_Aircraft.BP_Aircraft_C",
                        "associated_dis_enumerations": [
                            {"kind": 1, "domain": 2, "country": 225, "category": 1, "subcategory": 1, "specific": 0, "extra": 0}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    original_argv = sys.argv
    sys.argv = [
        "import_unreal_grill_mapping_manifest.py",
        "--input",
        str(manifest_path),
        "--fastdis-out",
        str(fastdis_out),
        "--json-out",
        str(json_out),
        "--md-out",
        str(md_out),
        "--search-root",
        str(tmp_path),
    ]
    try:
        assert importer.main() == 0
    finally:
        sys.argv = original_argv

    assert json.loads(fastdis_out.read_text(encoding="utf-8"))["rows"][0]["DisplayName"] == "Aircraft"
    report = json.loads(json_out.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert report["resolved_actor_classes"] == 0
    assert "# Unreal GRILL Mapping Import" in md_out.read_text(encoding="utf-8")
