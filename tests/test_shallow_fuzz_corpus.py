from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import fastdis


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "generated" / "fuzz_shallow_corpus"


def test_shallow_fuzz_manifest_covers_entire_catalog() -> None:
    payload = json.loads((CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert payload["catalog_entry_count"] == len(fastdis.PDU_CATALOG)
    assert payload["catalog_seed_count"] == len(fastdis.PDU_CATALOG)
    assert payload["seed_count"] == len(fastdis.PDU_CATALOG) + 5

    expected = {
        (entry.protocol_version, entry.pdu_type, entry.protocol_family, entry.class_name)
        for entry in fastdis.PDU_CATALOG
    }
    observed = {
        (item["protocol_version"], item["pdu_type"], item["protocol_family"], item["class_name"])
        for item in payload["valid_catalog_seeds"]
    }
    assert observed == expected


def test_shallow_fuzz_seed_headers_match_catalog_metadata() -> None:
    payload = json.loads((CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    for item in payload["valid_catalog_seeds"]:
        path = CORPUS_DIR / item["path"]
        data = path.read_bytes()
        assert len(data) == 12
        header = fastdis.parse_header(data, strict=True)
        assert header is not None
        assert header.version == item["protocol_version"]
        assert header.pdu_type == item["pdu_type"]
        assert header.protocol_family == item["protocol_family"]
        assert header.length == 12


def test_generate_shallow_fuzz_corpus_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_shallow_fuzz_corpus.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_shallow_fuzz_targets_are_declared_in_cmake() -> None:
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    for target in (
        "fastdis_fuzz_header",
        "fastdis_fuzz_scan_many",
        "fastdis_fuzz_catalog_dispatch",
        "fastdis_fuzz_min_lengths",
        "fastdis_fuzz_unknown_pdu",
        "fastdis_fuzz_entity_transform",
        "fastdis_fuzz_snapshot_buffer",
        "fastdis_fuzz_frame_orientation",
        "fastdis_fuzz_entity_table_ingest",
    ):
        assert target in cmake
