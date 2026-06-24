from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _ensure_report() -> dict[str, object]:
    path = ROOT / "generated" / "epic2_parity_report.json"
    if not path.exists():
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_epic2_parity_report.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return json.loads(path.read_text(encoding="utf-8"))


def test_epic2_parity_report_tracks_current_catalog_and_deep_counts() -> None:
    report = _ensure_report()
    summary = report["summary"]

    assert report["schema"] == "fastdis.epic2.parity_report.v1"
    assert summary["records"] == 141
    assert summary["all_catalog_surfaces_rows"] == 141
    assert summary["all_deep_surfaces_rows"] == 12
    assert summary["surface_catalog_counts"]["unity"] == 141
    assert summary["surface_deep_counts"]["unity"] == 12
    assert summary["surface_deep_counts"]["python"] == 12
    assert summary["representative_typed_rows"] == 4


def test_epic2_parity_report_represents_entity_state_lanes_honestly() -> None:
    report = _ensure_report()
    rows = {
        (row["protocol_version"], row["pdu_type"]): row
        for row in report["representative_rows"]
    }

    assert rows[(7, 1)]["deep_surfaces"]["python"] is True
    assert rows[(7, 1)]["deep_surfaces"]["unity"] is True
    assert rows[(7, 67)]["deep_surfaces"]["unreal"] is True
    assert rows[(7, 67)]["catalog_surfaces"]["unity"] is True


def test_generate_epic2_parity_report_check_passes_for_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_epic2_parity_report.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
