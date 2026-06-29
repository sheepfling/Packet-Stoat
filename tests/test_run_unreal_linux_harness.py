from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_linux_harness


def test_dry_run_writes_report_even_on_non_linux_host(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run_unreal_linux_harness.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unreal_linux_harness.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(run_unreal_linux_harness.platform, "machine", lambda: "arm64")

    json_out = tmp_path / "linux_verify.json"
    md_out = tmp_path / "linux_verify.md"

    rc = run_unreal_linux_harness.main(
        [
            "--mode",
            "verify",
            "--engine-version",
            "5.7",
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
            "--dry-run",
        ]
    )

    assert rc == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert payload["executed"] is False
    assert payload["lane"] == "linux-verify"
    assert payload["command"] == [
        sys.executable,
        "tools/run_unreal_linux_harness.py".replace("run_unreal_linux_harness.py", "run_unreal_orientation_verification.py"),
        "--engine-version",
        "5.7",
        "--dry-run",
    ]
    assert "does not claim execution on the current host" in md_out.read_text(encoding="utf-8")


def test_non_linux_host_writes_blocked_report(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run_unreal_linux_harness.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unreal_linux_harness.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(run_unreal_linux_harness.platform, "machine", lambda: "arm64")

    json_out = tmp_path / "linux_demo.json"
    md_out = tmp_path / "linux_demo.md"

    rc = run_unreal_linux_harness.main(
        [
            "--mode",
            "demo",
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )

    assert rc == 2
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked-host-platform"
    assert payload["executed"] is False
    assert payload["mode"] == "demo"
    assert payload["blockers"]
    assert "non-Linux host" in payload["claim_boundary"]
