from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_env


def test_classify_probe_failure_detects_sandbox_write_denied() -> None:
    output = (
        "Access to the path '/Users/rick/Library/Logs/Unreal Engine/LocalBuildLogs/Log.txt' is denied.\n"
    )
    assert unreal_env.classify_probe_failure(output) == "sandbox-home-write-denied"


def test_classify_probe_failure_detects_mac_platform_unavailable() -> None:
    output = "Platform Mac is not a valid platform to build."
    assert unreal_env.classify_probe_failure(output) == "host-mac-platform-unavailable"


def test_probe_failure_note_describes_sandbox_case() -> None:
    note = unreal_env.probe_failure_note("sandbox-home-write-denied")
    assert note is not None
    assert "sandbox" in note
    assert "~/Library" in note
