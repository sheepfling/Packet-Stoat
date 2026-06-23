from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import lattice_zorn_rest_sdk_probe


def test_zorn_rest_sdk_probe_renders_skipped_official_sdk_as_gap() -> None:
    report = {
        "overall_status": "ready-with-gaps",
        "proof_source": "zorn-rest-sdk-compatible-route",
        "real_lattice_verified": False,
        "checks": [
            {"name": "official_python_sdk_import", "status": "skipped", "detail": "No module named 'anduril'"},
        ],
        "gaps": ["No module named 'anduril'"],
    }

    rendered = lattice_zorn_rest_sdk_probe._render_markdown(report)

    assert "official_python_sdk_import" in rendered
    assert "ready-with-gaps" in rendered
    assert "No module named 'anduril'" in rendered
