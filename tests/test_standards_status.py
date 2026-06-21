from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import generate_standards_status
import generate_pdu_coverage


def test_standards_registry_tracks_update_sources() -> None:
    registry = generate_standards_status.load_registry()
    ids = {row["id"] for row in registry["standards"]}

    assert "ieee-1278.1a-1998" in ids
    assert "ieee-1278.1-2012" in ids
    assert "ieee-p1278.1-next" in ids
    assert "siso-ref-010-v32" in ids
    assert "siso-ref-010-latest" in ids
    assert "siso-std-023-2024-cdis" in ids
    assert registry["update_policy"]["known_version_unknown_pdu"] == "generic_event_with_raw_preservation"


def test_standards_outputs_include_enum_and_pdu_provenance() -> None:
    rendered = generate_standards_status.outputs()
    enum_manifest = json.loads(rendered[ROOT / "generated" / "enum_coverage_manifest.json"])
    status_manifest = json.loads(rendered[ROOT / "generated" / "standards_status_manifest.json"])

    assert enum_manifest["summary"]["pinned_siso_ref_010"] == "siso-ref-010-v32"
    assert enum_manifest["summary"]["full_siso_ref_010_imported"] is False
    assert status_manifest["overall_status"] == "update_ready"
    assert status_manifest["protocol_layouts"]["dis6"]["pdu_rows"] == 68
    assert status_manifest["protocol_layouts"]["dis7"]["pdu_rows"] == 73
    assert any(item["id"] == "ieee-p1278.1-next" for item in status_manifest["watch_items"])


def test_pdu_coverage_manifest_has_source_metadata() -> None:
    rendered = generate_pdu_coverage.outputs(generate_pdu_coverage.DEFAULT_DIS6, generate_pdu_coverage.DEFAULT_DIS7)
    manifest = json.loads(rendered[ROOT / "generated" / "pdu_coverage_manifest.json"])

    assert manifest["source_metadata"]["standards_registry"] == "standards/registry.yaml"
    assert "ieee-1278.1-2012" in manifest["source_metadata"]["protocol_layouts"]
    assert manifest["source_metadata"]["companion_standard_watch"] == "siso-std-023-2024-cdis"


def test_fastdis_standards_check_cli() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "fastdis", "standards", "check"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
