from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import lattice_compatibility_harness_report  # noqa: E402


def test_lattice_compatibility_harness_report_is_no_credential_ready(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(lattice_compatibility_harness_report, "OUT_DIR", tmp_path)

    rc = lattice_compatibility_harness_report.main()

    payload = json.loads((tmp_path / "compatibility_harness_report.json").read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["overall_status"] == "compatibility_harness_ready_no_credentials"
    assert payload["real_lattice_verified"] is False
    assert payload["auth_session"]["sandbox_header_rejection"] == "passed:403"
    assert payload["entities"]["stream"] == "passed"
