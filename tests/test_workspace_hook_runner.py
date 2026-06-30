from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import workspace_hook_runner


def test_python_package_hook_blocks_when_exact_abi_requirement_is_not_met(monkeypatch, capsys) -> None:
    monkeypatch.setattr(workspace_hook_runner, "_requirement_context", lambda: {})

    rc = workspace_hook_runner.main(["python", "package"])
    out = capsys.readouterr().out

    assert rc == 2
    assert "surface: python" in out
    assert "hook: package" in out
    assert "requirement_status: fail" in out
    assert "interpreter-abi-mismatch" in out or "interpreter-version-mismatch" in out
    assert "command: blocked-by-requirements" in out


def test_unreal_doctor_hook_blocks_when_exact_engine_lane_is_not_met(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        workspace_hook_runner,
        "_requirement_context",
        lambda: {"engines": {"unreal": {"status": "ready", "versions": ["5.7"]}}},
    )

    rc = workspace_hook_runner.main(["unreal", "doctor"])
    out = capsys.readouterr().out

    assert rc == 2
    assert "surface: unreal" in out
    assert "hook: doctor" in out
    assert "requirement_status: fail" in out
    assert "engine-version-mismatch" in out
    assert "command: blocked-by-requirements" in out
