from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_host_compat_report
import unreal_env


def test_summarize_markdown_includes_probe_rows_and_host_sections() -> None:
    report = {
        "generated_at": "2026-06-19T12:00:00Z",
        "host": {
            "platform_system": "Darwin",
            "machine": "arm64",
            "sw_vers_summary": "26.5.1",
            "clang_summary": "Apple clang version 21.0.0",
            "xcode_select": {"returncode": 0, "output": "/Applications/Xcode.app/Contents/Developer\n"},
            "sw_vers": {"returncode": 0, "output": "ProductVersion:\t15.5\n"},
            "clang_version": {"returncode": 0, "output": "Apple clang version 17.0.0\n"},
            "sdk_path": {"returncode": 0, "output": "/Applications/Xcode.app/.../MacOSX.sdk\n"},
        },
        "official_reference": {
            "macos_requirements_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/macos-development-requirements-for-unreal-engine",
            "ue56_macos_baseline": {
                "minimum_macos": "Sonoma 14.0",
                "recommended_macos": "Latest macOS 14 Sonoma",
                "minimum_xcode": "Xcode 15.2",
                "recommended_xcode": "Xcode 15.4 or newer",
            },
        },
        "lanes": [
            {
                "version": "5.6",
                "discovered": True,
                "install": {
                    "install_root": "/Users/Shared/Epic Games/UE_5.6",
                    "editor_path": "/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/Mac/UnrealEditor",
                    "dotnet_path": "/Users/Shared/Epic Games/UE_5.6/dotnet",
                    "ubt_path": "/Users/Shared/Epic Games/UE_5.6/UnrealBuildTool.dll",
                    "quirks": ["editor app bundle present"],
                },
                "probe": {
                    "status": "fail",
                    "failure_kind": "host-mac-platform-unavailable",
                    "detail": "host Mac SDK/platform rejected by this engine install before plugin code compiled; verify the engine/Xcode/macOS compatibility for this Unreal minor",
                    "command": ["dotnet", "ubt"],
                    "output": "Platform Mac is not a valid platform to build.\n",
                },
            }
        ],
    }

    markdown = run_unreal_host_compat_report.summarize_markdown(report)

    assert "| 5.6 | yes | fail | host-mac-platform-unavailable |" in markdown
    assert "### xcode_select" in markdown
    assert "## Compatibility Interpretation" in markdown
    assert "UE 5.6 macOS baseline from Epic" in markdown
    assert "This host reported macOS `26.5.1`." in markdown
    assert "### 5.6" in markdown
    assert "- probe failure kind: `host-mac-platform-unavailable`" in markdown


def test_main_writes_reports_from_stubbed_host_and_probe(monkeypatch, tmp_path: Path) -> None:
    class FakeInstall:
        def __init__(self, version: str) -> None:
            self.version = version

        def to_dict(self) -> dict[str, object]:
            return {
                "install_root": f"/Engines/UE_{self.version}",
                "editor_path": f"/Engines/UE_{self.version}/UnrealEditor",
                "dotnet_path": f"/Engines/UE_{self.version}/dotnet",
                "ubt_path": f"/Engines/UE_{self.version}/UnrealBuildTool.dll",
                "quirks": [],
            }

    monkeypatch.setattr(
        run_unreal_host_compat_report,
        "parse_args",
        lambda: run_unreal_host_compat_report.argparse.Namespace(
            versions=["5.6", "5.8"],
            out_dir=str(tmp_path),
            probe_project=str(tmp_path / "Project.uproject"),
        ),
    )
    monkeypatch.setattr(run_unreal_host_compat_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_unreal_host_compat_report,
        "detect_host_facts",
        lambda: {
            "platform_system": "Darwin",
            "machine": "arm64",
            "sw_vers": {"returncode": 0, "output": "ProductVersion:\t26.5.1\n"},
            "clang_version": {"returncode": 0, "output": "Apple clang version 21.0.0\n"},
        },
    )
    monkeypatch.setattr(run_unreal_host_compat_report.unreal_env, "discover_installs", lambda: [FakeInstall("5.6"), FakeInstall("5.8")])

    def fake_probe(install: unreal_env.UnrealInstall, project_path: Path) -> dict[str, object]:
        if install.version == "5.6":
            return {
                "status": "fail",
                "failure_kind": "host-mac-platform-unavailable",
                "detail": "blocked",
                "command": ["dotnet", "ubt"],
                "output": "Platform Mac is not a valid platform to build.\n",
            }
        return {
            "status": "ok",
            "failure_kind": None,
            "detail": "ok",
            "command": ["dotnet", "ubt"],
            "output": "ok\n",
        }

    monkeypatch.setattr(run_unreal_host_compat_report.unreal_env, "probe_host_platform_support", fake_probe)

    rc = run_unreal_host_compat_report.main()

    assert rc == 2
    payload = json.loads((tmp_path / "unreal_host_compat_report.json").read_text(encoding="utf-8"))
    assert payload["official_reference"]["ue56_macos_baseline"]["minimum_macos"] == "Sonoma 14.0"
    assert payload["host"]["sw_vers_summary"] == "26.5.1"
    assert [lane["version"] for lane in payload["lanes"]] == ["5.6", "5.8"]
    lane_56 = next(lane for lane in payload["lanes"] if lane["version"] == "5.6")
    lane_58 = next(lane for lane in payload["lanes"] if lane["version"] == "5.8")
    assert lane_56["probe"]["failure_kind"] == "host-mac-platform-unavailable"
    assert lane_58["probe"]["status"] == "ok"
    assert "Unreal Host Compatibility Report" in (tmp_path / "unreal_host_compat_report.md").read_text(encoding="utf-8")
