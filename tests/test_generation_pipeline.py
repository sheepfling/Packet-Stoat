from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _run_generator(script: str, *args: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _ensure_generated_ir_files() -> None:
    if (ROOT / "generated" / "fastdis_ir_dis6.json").exists() and (
        ROOT / "generated" / "fastdis_ir_dis7.json"
    ).exists():
        return
    _run_generator("generate_fastdis_ir.py")


def _ensure_shallow_fuzz_corpus() -> None:
    if (ROOT / "generated" / "fuzz_shallow_corpus" / "manifest.json").exists():
        return
    _run_generator("generate_shallow_fuzz_corpus.py")


def _ensure_message_coverage_manifest() -> None:
    if (ROOT / "generated" / "message_coverage_manifest.json").exists():
        return
    _run_generator("generate_pdu_catalog.py")


def test_generated_fastdis_ir_files_exist_and_are_consistent() -> None:
    _ensure_generated_ir_files()
    ir6 = json.loads((ROOT / "generated" / "fastdis_ir_dis6.json").read_text(encoding="utf-8"))
    ir7 = json.loads((ROOT / "generated" / "fastdis_ir_dis7.json").read_text(encoding="utf-8"))

    assert ir6["schema_version"] == 6
    assert ir7["schema_version"] == 7
    assert ir6["source"] == "references/open-dis/DIS6.xml"
    assert ir7["source"] == "references/open-dis/DIS7.xml"
    assert ir6["pdu_count"] > 0
    assert ir7["pdu_count"] > 0
    assert ir6["class_count"] >= ir6["pdu_count"]
    assert ir7["class_count"] >= ir7["pdu_count"]

    entity_state6 = next(item for item in ir6["pdus"] if item["class_name"] == "EntityStatePdu")
    entity_state7 = next(item for item in ir7["pdus"] if item["class_name"] == "EntityStatePdu")
    assert entity_state6["pdu_type"] == 1
    assert entity_state7["pdu_type"] == 1
    assert entity_state6["protocol_family"] == 1
    assert entity_state7["protocol_family"] == 1
    assert entity_state6["has_body_decoder"]
    assert entity_state7["has_body_decoder"]


def test_generate_fastdis_ir_check_passes_for_current_tree() -> None:
    _ensure_generated_ir_files()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_fastdis_ir.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_check_generated_fresh_passes_for_current_tree() -> None:
    _ensure_generated_ir_files()
    _ensure_message_coverage_manifest()
    _ensure_shallow_fuzz_corpus()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_generated_fresh.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "[ok] pdu catalog" in result.stdout
    assert "[ok] normalized IR" in result.stdout
    assert "[ok] shallow fuzz corpus" in result.stdout
