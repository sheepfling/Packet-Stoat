from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compare_fields_handles_exact_and_float_matches() -> None:
    module = _load_module("run_differential_report", ROOT / "tools" / "run_differential_report.py")

    left = {"a": 1, "b": 2.00000, "c": "x"}
    right = {"a": 1, "b": 2.00001, "c": "y"}
    mismatches = module.compare_fields(left, right, ["a", "b", "c"], abs_tol=1e-4)

    assert mismatches == ["c"]


def test_build_catalog_report_detects_overlap_and_mismatches() -> None:
    module = _load_module("run_differential_report", ROOT / "tools" / "run_differential_report.py")

    DecoderA = type("EntityStatePdu", (), {})
    DecoderB = type("RepairResponsePdu", (), {})
    DecoderC = type("OnlyInOraclePdu", (), {})

    report = module.build_catalog_report({1: DecoderA, 10: DecoderB, 250: DecoderC})

    assert report["overlap_count"] >= 2
    assert any(item["pdu_type"] == 250 for item in report["open_dis_only"])
    assert report["name_mismatch_count"] == 0


def test_render_markdown_summarizes_fixture_status() -> None:
    module = _load_module("run_differential_report", ROOT / "tools" / "run_differential_report.py")
    report = {
        "catalog": {
            "fastdis_dis7_catalog_count": 57,
            "open_dis_decoder_count": 50,
            "overlap_count": 49,
            "name_mismatch_count": 1,
            "fastdis_only": [{}],
            "open_dis_only": [{}, {}],
        },
        "fixtures": {
            "fixture_count": 2,
            "header_match_count": 1,
            "entity_fixture_count": 1,
            "entity_match_count": 1,
            "fixtures": [
                {"file": "EntityStatePdu.raw", "header_match": True, "entity_state_match": True},
                {"file": "SignalPdu.raw", "header_match": False, "entity_state_match": None},
            ],
        },
    }

    text = module.render_markdown(report)

    assert "Catalog overlap" in text
    assert "`EntityStatePdu.raw`: header `PASS`, Entity State `PASS`" in text
    assert "`SignalPdu.raw`: header `FAIL`, Entity State `n/a`" in text
