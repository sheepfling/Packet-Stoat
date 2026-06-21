from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_alpha5_integration_matrix


def test_alpha5_integration_matrix_is_explicit_about_major_lanes() -> None:
    report = run_alpha5_integration_matrix.build_report()
    rows = {row["area"]: row for row in report["rows"]}
    expected = {
        "DIS 6/7 catalog",
        "DIS 6/7 ingress",
        "DIS 6/7 egress",
        "Filtering",
        "Buffering",
        "Robustness",
        "Dead reckoning",
        "Logging",
        "Engine example projects",
    }
    assert set(rows) == expected
    assert rows["DIS 6/7 catalog"]["status"] == "ready"
    assert rows["Logging"]["status"] == "ready"
    assert rows["Dead reckoning"]["status"] == "partial"
    assert "predictive extrapolation" in " ".join(rows["Dead reckoning"]["gaps"])


def test_alpha5_integration_matrix_writes_json_and_markdown(tmp_path: Path) -> None:
    paths = run_alpha5_integration_matrix.write_report(tmp_path)
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert payload["schema"] == "fastdis.alpha5_integration_matrix.v1"
    assert payload["summary"]["rows"] == 9
    assert "| Area | Status | Surfaces | Confirmation | Primary commands | Gaps |" in markdown
    assert "dead reckoning is intentionally marked partial" in markdown
