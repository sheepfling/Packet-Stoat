from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import lattice_contract_audit


def test_lattice_contract_audit_reports_known_public_field_gaps() -> None:
    report = lattice_contract_audit.build_report()

    assert report["overall_status"] == "aligned"
    first_payload = report["payload_audits"][0]
    by_field = {row["field"]: row for row in first_payload["checks"]}
    assert by_field["entityId"]["status"] == "pass"
    assert by_field["isLive"]["status"] == "pass"
    assert by_field["location.position"]["status"] == "pass"
    assert by_field["packetStoat.source"]["status"] == "pass"


def test_lattice_contract_audit_writes_reports(tmp_path: Path) -> None:
    report = lattice_contract_audit.build_report()
    json_path, md_path = lattice_contract_audit.write_report(report, tmp_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["overall_status"] == "aligned"
    assert "Lattice Contract Audit" in md_path.read_text(encoding="utf-8")
