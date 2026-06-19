from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_matrix


def test_classify_failure_detects_sandbox_home_write_denied() -> None:
    output = (
        "Failed to delete file /Users/rick/Library/Logs/Unreal Engine/LocalBuildLogs/Log.json\n"
        "Access to the path '/Users/rick/Library/Application Support/Epic/UnrealBuildTool/Log.txt' is denied.\n"
    )
    assert run_unreal_matrix.classify_failure(output) == "sandbox-home-write-denied"


def test_classify_failure_detects_host_mac_platform_unavailable() -> None:
    output = "Platform Mac is not a valid platform to build."
    assert run_unreal_matrix.classify_failure(output) == "host-mac-platform-unavailable"


def test_failure_note_for_sandbox_home_write_denied() -> None:
    note = run_unreal_matrix.failure_note("sandbox-home-write-denied")
    assert note is not None
    assert "sandbox" in note
    assert "~/Library" in note


def test_summarize_markdown_includes_demo_column() -> None:
    report = {
        "generated_at": "2026-06-19T08:11:27Z",
        "host_platform": "darwin",
        "results": [
            {
                "version": "5.8",
                "discovered": True,
                "install": {
                    "install_root": "/Users/Shared/Epic Games/UE_5.8",
                    "editor_path": "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor",
                    "uat_path": "/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh",
                    "quirks": ["editor app bundle present"],
                },
                "notes": [],
                "plugin_build": {"status": "passed"},
                "orientation": {"status": "passed"},
                "demo": {"status": "passed"},
            }
        ],
    }
    markdown = run_unreal_matrix.summarize_markdown(report)
    assert "| Version | Discovered | Plugin Build | Orientation | Demo | Notes |" in markdown
    assert "| 5.8 | yes | passed | passed | passed | none |" in markdown
