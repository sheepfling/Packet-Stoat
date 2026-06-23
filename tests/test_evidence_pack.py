from __future__ import annotations

import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from tools import check_evidence_pack, generate_evidence_pack


def test_evidence_pack_generates_and_checks(tmp_path: Path) -> None:
    out_dir = tmp_path / "evidence"

    manifest = generate_evidence_pack.generate(out_dir, clean=True, render_symbols="never")

    assert manifest["schema"] == "fastdis.evidence_pack.v1"
    assert manifest["status"] == "pass"
    assert (out_dir / "index.md").exists()
    assert (out_dir / "sha256sums.txt").exists()
    assert (out_dir / "charts" / "pdu_handling_status.svg").exists()
    assert (out_dir / "symbols" / "contact_sheet.svg").exists()
    assert (out_dir / "traces" / "transform_only_negative_trace.md").exists()

    ok, errors = check_evidence_pack.check(out_dir / "manifest.json")
    assert ok, errors


def test_evidence_pack_manifest_tracks_output_hashes(tmp_path: Path) -> None:
    out_dir = tmp_path / "evidence"
    generate_evidence_pack.generate(out_dir, clean=True, render_symbols="never")

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    artifact_rows = {row["path"]: row for row in manifest["artifacts"]}
    chart_key = next(path for path in artifact_rows if path.endswith("charts/pdu_handling_status.svg"))
    assert artifact_rows[chart_key]["sha256"]


def test_evidence_pack_svgs_are_parseable(tmp_path: Path) -> None:
    out_dir = tmp_path / "evidence"
    generate_evidence_pack.generate(out_dir, clean=True, render_symbols="never")

    for path in sorted((out_dir / "charts").glob("*.svg")):
        root = ET.parse(path).getroot()
        assert root.attrib["width"] == "1600"
        assert root.attrib["height"] == "900"
