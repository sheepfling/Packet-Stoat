from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

import pytest

from fastdis import native
from fastdis.tools._shared import EntityStateSpec, make_entity_state_packet


ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "extensions" / "fastdis-symbols-proof"
RULES = PROOF / "rules" / "demo_dis_to_symbol_rules.json"
AFFILIATIONS = PROOF / "rules" / "affiliation_policy.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def entity_type_tuple(value: str) -> tuple[int, int, int, int, int, int, int]:
    parts = tuple(int(part) for part in value.split("."))
    if len(parts) != 7:
        raise ValueError(f"expected seven DIS entity type parts: {value}")
    return parts  # type: ignore[return-value]


def affiliation_from_force_id(force_id: int, policy: Mapping[str, Any]) -> str:
    force_map = policy["force_id_map"]
    if not isinstance(force_map, Mapping):
        raise ValueError("force_id_map must be an object")
    return str(force_map.get(str(force_id), policy["default"]))


def find_symbol_key(entity_type: tuple[int, int, int, int, int, int, int], rules: Mapping[str, Any], affiliation: str) -> str:
    kind, domain, *_ = entity_type
    for rule in rules["rules"]:
        when = rule["when"]
        if int(when.get("kind", -1)) == kind and int(when.get("domain", -1)) == domain:
            return str(rule["symbol_key"])
    fallback = rules["fallback_symbol_key_by_affiliation"]
    return str(fallback.get(affiliation, fallback["unknown"]))


def sidc_for(symbol_key: str, affiliation: str, rules: Mapping[str, Any]) -> str:
    table = rules["sidc_by_symbol_key_and_affiliation"]
    by_affiliation = table[symbol_key]
    if affiliation in by_affiliation:
        return str(by_affiliation[affiliation])
    if "unknown" in by_affiliation:
        return str(by_affiliation["unknown"])
    return str(next(iter(by_affiliation.values())))


def descriptor_from_entity(entity: Mapping[str, Any]) -> dict[str, Any]:
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    affiliation_policy = json.loads(AFFILIATIONS.read_text(encoding="utf-8"))
    force_id = int(entity["force_id"])
    entity_type = entity_type_tuple(str(entity["entity_type"]))
    affiliation = affiliation_from_force_id(force_id, affiliation_policy)
    symbol_key = find_symbol_key(entity_type, rules, affiliation)
    orientation = entity.get("orientation_rad", {})
    direction = None
    if isinstance(orientation, Mapping) and orientation.get("psi") is not None:
        direction = round(math.degrees(float(orientation["psi"])) % 360.0, 6)
    return {
        "case_id": entity["case_id"],
        "standard": rules["standard"],
        "sidc": sidc_for(symbol_key, affiliation, rules),
        "source": {
            "force_id": force_id,
            "entity_kind": entity_type[0],
            "domain": entity_type[1],
            "country": entity_type[2],
            "category": entity_type[3],
            "subcategory": entity_type[4],
            "specific": entity_type[5],
            "extra": entity_type[6],
        },
        "modifiers": {
            "uniqueDesignation": entity.get("marking"),
            "direction": direction,
        },
    }


def entity_prefix_to_proof_input(case_id: str, prefix: native.EntityStatePrefix) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "force_id": prefix.force_id,
        "entity_type": ".".join(str(part) for part in prefix.entity_type),
        "marking": prefix.marking_text,
        "orientation_rad": {
            "psi": prefix.orientation[0],
            "theta": prefix.orientation[1],
            "phi": prefix.orientation[2],
        },
        "location_ecef_m": {
            "x": prefix.location[0],
            "y": prefix.location[1],
            "z": prefix.location[2],
        },
    }


def test_demo_entities_map_to_renderer_descriptors() -> None:
    entities = read_jsonl(PROOF / "cases" / "demo_fastdis_entities.jsonl")
    descriptors = [descriptor_from_entity(entity) for entity in entities]

    assert [descriptor["case_id"] for descriptor in descriptors] == [
        "friendly-land-demo-001",
        "hostile-land-demo-001",
        "neutral-air-demo-001",
        "unknown-subsurface-demo-001",
        "unmapped-entity-demo-001",
    ]
    assert all(len(str(descriptor["sidc"])) == 30 for descriptor in descriptors)
    assert descriptors[0]["modifiers"] == {"uniqueDesignation": "A12", "direction": 90.0}
    assert descriptors[-1]["sidc"] == "130100000011010000000000000000"


def test_fastdis_entity_state_prefix_has_symbol_identity_fields() -> None:
    lib = native.load_native()
    packet = make_entity_state_packet(
        EntityStateSpec(
            force_id=1,
            marking="A12",
            entity_type=(1, 1, 225, 1, 1, 0, 0),
            alternate_entity_type=(1, 1, 225, 1, 1, 0, 0),
            orientation_dis_deg=(90.0, 0.0, 0.0),
            location_ecef_m=(1.0, 2.0, 3.0),
        )
    )

    prefix = lib.parse_entity_state_prefix(packet)
    assert prefix.has_field(native.FASTDIS_ES_FIELD_FORCE_ID)
    assert prefix.has_field(native.FASTDIS_ES_FIELD_ENTITY_TYPE)
    assert prefix.has_field(native.FASTDIS_ES_FIELD_MARKING)
    assert prefix.has_field(native.FASTDIS_ES_FIELD_LOCATION)
    assert prefix.has_field(native.FASTDIS_ES_FIELD_ORIENTATION)
    entity = entity_prefix_to_proof_input("friendly-land-demo-001", prefix)
    descriptor = descriptor_from_entity(entity)

    assert descriptor["sidc"] == "130310000011010000000000000000"
    assert descriptor["modifiers"]["uniqueDesignation"] == "A12"
    assert descriptor["modifiers"]["direction"] == pytest.approx(90.0, abs=1e-3)
    assert descriptor["source"]["entity_kind"] == 1
    assert descriptor["source"]["domain"] == 1


def test_transform_only_payload_is_negative_case() -> None:
    transform_only = {
        "case_id": "transform-only",
        "force_id": 1,
        "location_ecef_m": {"x": 1.0, "y": 2.0, "z": 3.0},
        "orientation_rad": {"psi": 0.0, "theta": 0.0, "phi": 0.0},
    }

    with pytest.raises(KeyError):
        descriptor_from_entity(transform_only)


def test_milsymbol_accepts_demo_descriptors_when_installed(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    if not (PROOF / "node_modules" / "milsymbol").exists():
        pytest.skip("run `npm install --prefix extensions/fastdis-symbols-proof` to enable live milsymbol proof")

    input_path = tmp_path / "descriptors.jsonl"
    descriptors = [descriptor_from_entity(entity) for entity in read_jsonl(PROOF / "cases" / "demo_fastdis_entities.jsonl")]
    input_path.write_text("\n".join(json.dumps(descriptor) for descriptor in descriptors) + "\n", encoding="utf-8")
    out_dir = tmp_path / "svg"

    result = subprocess.run(
        [
            "node",
            str(PROOF / "render_milsymbol.mjs"),
            str(input_path),
            str(out_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "rendered=5" in result.stdout
    for descriptor in descriptors:
        svg_path = out_dir / f"{descriptor['case_id']}.svg"
        assert svg_path.exists()
        assert "<svg" in svg_path.read_text(encoding="utf-8")


def test_entity_state_pdu_can_render_symbol_svg_through_proof_harness(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    if not (PROOF / "node_modules" / "milsymbol").exists():
        pytest.skip("run `npm install --prefix extensions/fastdis-symbols-proof` to enable live milsymbol proof")

    lib = native.load_native()
    packet = make_entity_state_packet(
        EntityStateSpec(
            force_id=1,
            marking="A12",
            entity_type=(1, 1, 225, 1, 1, 0, 0),
            alternate_entity_type=(1, 1, 225, 1, 1, 0, 0),
            orientation_dis_deg=(90.0, 0.0, 0.0),
            location_ecef_m=(1.0, 2.0, 3.0),
        )
    )
    prefix = lib.parse_entity_state_prefix(packet)
    entity = entity_prefix_to_proof_input("entity-state-pdu-e2e", prefix)
    descriptor = descriptor_from_entity(entity)
    input_path = tmp_path / "descriptors.jsonl"
    input_path.write_text(json.dumps(descriptor) + "\n", encoding="utf-8")
    out_dir = tmp_path / "svg"

    result = subprocess.run(
        [
            "node",
            str(PROOF / "render_milsymbol.mjs"),
            str(input_path),
            str(out_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    svg_path = out_dir / "entity-state-pdu-e2e.svg"
    assert "rendered=1" in result.stdout
    assert descriptor["sidc"] == "130310000011010000000000000000"
    assert descriptor["modifiers"]["uniqueDesignation"] == "A12"
    assert descriptor["modifiers"]["direction"] == pytest.approx(90.0, abs=1e-3)
    assert svg_path.exists()
    assert "<svg" in svg_path.read_text(encoding="utf-8")
