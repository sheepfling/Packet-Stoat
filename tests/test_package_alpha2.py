from __future__ import annotations

import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import package_alpha2


def test_refresh_generated_reports_accepts_non_ready_exit(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run(cmd: list[str], cwd=None, check=False, stdout=None, stderr=None, text=None):
        recorded.append(cmd)
        return subprocess.CompletedProcess(cmd, 2, stdout="report wrote output")

    monkeypatch.setattr(package_alpha2.subprocess, "run", fake_run)

    package_alpha2.refresh_generated_reports()

    assert recorded == [
        [
            sys.executable,
            str(package_alpha2.ROOT / "tools" / "run_alpha2_signoff_matrix.py"),
            "--out-dir",
            str(package_alpha2.AUDIT_REPORT_DIR),
        ],
        [
            sys.executable,
            str(package_alpha2.ROOT / "tools" / "run_alpha2_release_audit.py"),
            "--out-dir",
            str(package_alpha2.AUDIT_REPORT_DIR),
        ],
    ]


def test_refresh_generated_reports_raises_on_real_failure(monkeypatch) -> None:
    def fake_run(cmd: list[str], cwd=None, check=False, stdout=None, stderr=None, text=None):
        if str(package_alpha2.ROOT / "tools" / "run_alpha2_signoff_matrix.py") in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="ok")
        return subprocess.CompletedProcess(cmd, 1, stdout="boom")

    monkeypatch.setattr(package_alpha2.subprocess, "run", fake_run)

    try:
        package_alpha2.refresh_generated_reports()
    except RuntimeError as exc:
        assert "Alpha 2 release audit refresh failed" in str(exc)
        assert "boom" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
