from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_unity_csharp_bridge_probe_executes_unity_package_interop() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "probe_unity_csharp_bridge.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads((ROOT / "artifacts" / "reports" / "unity_csharp_bridge_probe.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.unity.csharp_bridge_probe.v1"
    assert payload["overall_status"] == "pass"
    assert '"status":"pass"' in payload["stdout"]
