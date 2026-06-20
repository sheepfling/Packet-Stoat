from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_alpha4_1_sdk_gap_report


def test_alpha4_1_sdk_gap_report_is_access_ready_no_credentials(tmp_path: Path) -> None:
    report = run_alpha4_1_sdk_gap_report.build_report()
    json_path, md_path = run_alpha4_1_sdk_gap_report.write_report(report, tmp_path)

    assert report["overall_status"] == "access_ready_no_credentials"
    assert report["real_lattice_verified"] is False
    assert report["transport_contract"]["real_rest"] == "requires_credentials"
    assert json.loads(json_path.read_text(encoding="utf-8"))["overall_status"] == "access_ready_no_credentials"
    assert "Alpha 4.1 Lattice SDK Gap Report" in md_path.read_text(encoding="utf-8")
