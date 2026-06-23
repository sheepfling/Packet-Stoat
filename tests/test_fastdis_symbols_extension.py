from __future__ import annotations

from importlib import util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "extensions" / "fastdis-symbols"


def load_symbols_module() -> Any:
    spec = util.spec_from_file_location(
        "fastdis_symbols",
        EXTENSION / "python" / "src" / "fastdis_symbols" / "__init__.py",
    )
    assert spec is not None
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(ModuleType, module)


def test_symbols_extension_policy_files_are_valid_json() -> None:
    for path in [
        EXTENSION / "spec" / "symbol_descriptor.schema.json",
        EXTENSION / "spec" / "symbol_handoff.schema.json",
        EXTENSION / "spec" / "sidc.schema.json",
        EXTENSION / "spec" / "affiliation_policy.json",
        EXTENSION / "spec" / "dis_to_2525_rules.json",
    ]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        assert payload


def test_symbols_extension_golden_cases_are_jsonl() -> None:
    cases = [
        json.loads(line)
        for line in (EXTENSION / "spec" / "golden_cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert {case["case_id"] for case in cases} == {
        "friendly_air_platform_generic",
        "opposing_land_platform_generic",
    }
    for case in cases:
        assert case["expected_handoff"]["descriptor"]["schema"] == "fastdis.symbol_descriptor.v1"
        assert case["input"]["entity_type"].count(".") == 6


def test_symbols_python_descriptor_is_separate_from_fastdis_core() -> None:
    fastdis_symbols = load_symbols_module()

    descriptor = fastdis_symbols.descriptor_from_mapping(
        {
            "standard": "generic",
            "affiliation": "friendly",
            "symbol_set": "air",
            "sidc": None,
            "entity_type": "1.2.225.1.1.3.0",
            "label": "Air platform",
            "confidence": "fallback",
            "rule_id": "dis-platform-air-generic",
        }
    )

    assert descriptor.affiliation == "friendly"
    assert descriptor.sidc is None
    assert descriptor.__class__.__name__ == "SymbolDescriptor"

    handoff = fastdis_symbols.resolve_from_entity_state(
        {
            "force_id": 1,
            "entity_type": "1.2.225.1.1.3.0",
            "marking": "FASTDIS01",
            "orientation_rad": {"psi": 1.5707963267948966, "theta": 0.0, "phi": 0.0},
            "location_ecef_m": {"x": 1.0, "y": 2.0, "z": 3.0},
        }
    )

    assert handoff.descriptor.affiliation == "friendly"
    assert handoff.descriptor.symbol_set == "air"
    assert handoff.modifiers.unique_designation == "FASTDIS01"
    assert handoff.modifiers.direction_degrees == 90.0
    assert handoff.position_ecef_m is not None
    assert handoff.position_ecef_m.x_m == 1.0
    assert handoff.atlas_key == "generic:friendly:air:none"


def test_transform_only_shape_is_not_sufficient_for_symbols() -> None:
    fastdis_symbols = load_symbols_module()

    transform_only = {
        "force_id": 1,
        "location_ecef_m": {"x": 1.0, "y": 2.0, "z": 3.0},
        "orientation_rad": {"psi": 0.0, "theta": 0.0, "phi": 0.0},
        "linear_velocity_mps": {"x": 0.0, "y": 0.0, "z": 0.0},
    }

    try:
        fastdis_symbols.resolve_from_entity_state(transform_only)
    except ValueError as exc:
        assert "compact transform output is insufficient" in str(exc)
    else:
        raise AssertionError("transform-only payload should not resolve to a symbol handoff")


def test_core_does_not_reference_symbols_extension_policy() -> None:
    forbidden = ("fastdis_symbols", "MIL-STD-2525", "APP-6", "SIDC")
    core_paths = [
        *sorted((ROOT / "include" / "fastdis").glob("*.h")),
        *sorted((ROOT / "include" / "fastdis").glob("*.hpp")),
        *sorted((ROOT / "src" / "fastdis").rglob("*.py")),
    ]

    offenders: list[str] = []
    for path in core_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(token in text for token in forbidden):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
