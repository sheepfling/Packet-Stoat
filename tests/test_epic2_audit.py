from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_epic2_audit


def test_epic2_audit_build_report_tracks_current_epic2_state() -> None:
    report = run_epic2_audit.build_report()

    assert report["schema"] == "fastdis.epic2_audit.v1"
    assert report["overall_status"] in {"complete", "in_progress"}
    criteria = {item["name"]: item for item in report["criteria"]}

    assert criteria["141-row generated truth"]["status"] == "complete"
    assert criteria["Generic wire and field coverage"]["status"] == "complete"
    assert criteria["Typed semantic waves"]["status"] == "complete"
    assert criteria["Cross-engine and Lattice/Zorn parity"]["status"] == "complete"
    assert criteria["Evidence and release gates"]["status"] in {"partial", "complete"}

    assert criteria["141-row generated truth"]["metrics"]["catalog_gap_rows"] == 0
    assert criteria["Generic wire and field coverage"]["metrics"]["field_visitor_rows"] == 141
    assert criteria["Typed semantic waves"]["metrics"]["fully_domain_decoded_rows"] == 141
    assert criteria["Cross-engine and Lattice/Zorn parity"]["metrics"]["language_rows"]["unity"]["catalog_rows"] == 141
    assert criteria["Cross-engine and Lattice/Zorn parity"]["metrics"]["language_rows"]["unity"]["deep_rows"] == 141
    assert "unity_csharp_bridge_probe_status" in criteria["Cross-engine and Lattice/Zorn parity"]["metrics"]
    assert "release_ready_receipt_status" in criteria["Evidence and release gates"]["metrics"]


def test_epic2_audit_writes_json_and_markdown(tmp_path: Path) -> None:
    json_path, md_path = run_epic2_audit.write_report(tmp_path)

    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.epic2_audit.v1"
    assert "# Epic 2 Audit Report" in md_path.read_text(encoding="utf-8")
