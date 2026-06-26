from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_grill_unreal_source_smoke


def write_plugin(root: Path, *, whitelist: list[str]) -> None:
    root.mkdir(parents=True)
    (root / "GRILLDISForUnreal.uplugin").write_text(
        json.dumps(
            {
                "FriendlyName": "GRILL DIS for Unreal",
                "EngineVersion": "4.27.0",
                "Modules": [
                    {
                        "Name": "DISRuntime",
                        "Type": "Runtime",
                        "WhitelistPlatforms": whitelist,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runtime = root / "Source" / "DISRuntime"
    runtime.mkdir(parents=True)
    (runtime / "DISRuntime.Build.cs").write_text(
        'string WinPath = Path.Combine(BinaryPath, "Win64");\nPublicAdditionalLibraries.Add(Path.Combine(WinPath, "OpenDIS6.lib"));\n',
        encoding="utf-8",
    )
    win64 = root / "Source" / "ThirdParty" / "Binaries" / "Win64"
    win64.mkdir(parents=True)
    (win64 / "OpenDIS6.lib").write_text("", encoding="utf-8")


def write_example(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "GRILLDISExample.uproject").write_text(json.dumps({"EngineAssociation": "4.27"}) + "\n", encoding="utf-8")
    embedded = root / "Plugins" / "DISPluginForUnreal"
    embedded.mkdir(parents=True)
    (embedded / ".git").mkdir()


def test_plugin_whitelist_platforms_collects_unique_values() -> None:
    descriptor = {
        "Modules": [
            {"WhitelistPlatforms": ["Win64"]},
            {"PlatformAllowList": ["Mac", "Win64"]},
        ]
    }
    assert run_grill_unreal_source_smoke.plugin_whitelist_platforms(descriptor) == ["Win64", "Mac"]


def test_build_report_marks_mac_host_blocked_when_plugin_is_win64_only(tmp_path: Path, monkeypatch) -> None:
    plugin = tmp_path / "plugin"
    example = tmp_path / "example"
    write_plugin(plugin, whitelist=["Win64"])
    write_example(example)

    monkeypatch.setattr(run_grill_unreal_source_smoke, "host_unreal_platform", lambda: "Mac")
    monkeypatch.setattr(run_grill_unreal_source_smoke, "git_commit", lambda path: "deadbeef")
    monkeypatch.setattr(
        run_grill_unreal_source_smoke.unreal_env,
        "discover_installs",
        lambda: [type("Install", (), {"version": "4.27", "to_dict": lambda self: {"version": "4.27", "install_root": "/UE_4.27", "editor_path": "/UE_4.27/Engine/Binaries/Mac/UE4Editor"}})()],
    )

    args = run_grill_unreal_source_smoke.parse_args(
        ["--plugin-root", str(plugin), "--example-root", str(example), "--engine-version", "4.27"]
    )
    report = run_grill_unreal_source_smoke.build_report(args)

    assert report["status"] == "blocked-host-platform"
    assert "Win64" in report["detail"]
    assert "plugin manifest does not allow host platform Mac" in report["blockers"]
    assert report["win64_only_build_cs_linkage"] is True


def test_render_markdown_mentions_blocked_status() -> None:
    report = {
        "status": "blocked-host-platform",
        "host_platform": "Mac",
        "requested_engine_version": "4.27",
        "resolved_engine_version": "4.27",
        "plugin_root": "/tmp/plugin",
        "example_root": "/tmp/example",
        "detail": "blocked",
        "plugin_commit": "a",
        "example_commit": "b",
        "example_plugin_commit": "c",
        "plugin_whitelist_platforms": ["Win64"],
        "third_party_binary_platforms": ["Win64"],
        "win64_only_build_cs_linkage": True,
        "blockers": ["plugin manifest does not allow host platform Mac"],
    }

    markdown = run_grill_unreal_source_smoke.render_markdown(report)

    assert "GRILL Unreal Source Smoke" in markdown
    assert "status: `blocked-host-platform`" in markdown
    assert "plugin manifest does not allow host platform Mac" in markdown
