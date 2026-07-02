from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_grill_unreal_source_smoke
import workflow_versions


def write_plugin(root: Path, *, whitelist: list[str]) -> None:
    root.mkdir(parents=True)
    (root / "GRILLDISForUnreal.uplugin").write_text(
        json.dumps(
            {
                "FriendlyName": "GRILL DIS for Unreal",
                "EngineVersion": "5.7.0",
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
    (root / "GRILLDISExample.uproject").write_text(
        json.dumps(
            {
                "EngineAssociation": "5.7",
                "Plugins": [
                    {"Name": "CesiumForUnreal", "Enabled": True},
                    {"Name": "LowEntryExtStdLib", "Enabled": True},
                    {"Name": "GRILLDISForUnreal", "Enabled": True},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    embedded = root / "Plugins" / "DISPluginForUnreal"
    embedded.mkdir(parents=True)
    (embedded / ".git").mkdir()
    (root / "Plugins" / "CesiumForUnreal").mkdir(parents=True)
    (root / "Plugins" / "LowEntryExtStdLib").mkdir(parents=True)
    source_dir = root / "Source" / "GRILLDISExample"
    source_dir.mkdir(parents=True)
    (source_dir / "GRILLDISExample.Build.cs").write_text(
        'PublicDependencyModuleNames.AddRange(new string[] { "Core", "GeoReferencing"});\n'
        'PrivateDependencyModuleNames.AddRange(new string[] { "CesiumRuntime" });\n',
        encoding="utf-8",
    )
    (source_dir / "Custom_BPFL.h").write_text(
        '#include <CesiumRuntime/Public/CesiumIonRasterOverlay.h>\n'
        "class UCustom_BPFL {};\n",
        encoding="utf-8",
    )
    (source_dir / "Custom_BPFL.cpp").write_text(
        '#include "Custom_BPFL.h"\n'
        "void noop() {}\n",
        encoding="utf-8",
    )


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
        lambda: [type("Install", (), {"version": "5.7.1", "to_dict": lambda self: {"version": "5.7.1", "install_root": "/UE_5.7", "editor_path": "/UE_5.7/Engine/Binaries/Mac/UnrealEditor"}})()],
    )

    args = run_grill_unreal_source_smoke.parse_args(
        ["--plugin-root", str(plugin), "--example-root", str(example), "--engine-version", workflow_versions.DEFAULT_UNREAL_ENGINE_VERSION]
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
        "requested_engine_version": workflow_versions.DEFAULT_UNREAL_ENGINE_VERSION,
        "resolved_engine_version": workflow_versions.DEFAULT_UNREAL_ENGINE_VERSION,
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


def test_build_report_forwards_probe_timeout(tmp_path: Path, monkeypatch) -> None:
    plugin = tmp_path / "plugin"
    example = tmp_path / "example"
    write_plugin(plugin, whitelist=["Win64"])
    write_example(example)

    install = type(
        "Install",
        (),
        {
            "version": "5.7",
            "to_dict": lambda self: {
                "version": "5.7",
                "install_root": "/UE_5.7",
                "editor_path": "/UE_5.7/Engine/Binaries/Win64/UnrealEditor.exe",
            },
        },
    )()

    recorded: dict[str, object] = {}

    monkeypatch.setattr(run_grill_unreal_source_smoke, "git_commit", lambda path: "deadbeef")
    monkeypatch.setattr(run_grill_unreal_source_smoke.unreal_env, "discover_installs", lambda: [install])

    def fake_probe(resolved_install, project_path=None, *, timeout_seconds=20.0):
        recorded["install"] = resolved_install
        recorded["project_path"] = project_path
        recorded["timeout_seconds"] = timeout_seconds
        return {"status": "ok", "failure_kind": None, "detail": "ok", "command": [], "output": ""}

    monkeypatch.setattr(run_grill_unreal_source_smoke.unreal_env, "probe_host_platform_support", fake_probe)

    args = run_grill_unreal_source_smoke.parse_args(
        [
            "--plugin-root",
            str(plugin),
            "--example-root",
            str(example),
            "--engine-version",
            workflow_versions.DEFAULT_UNREAL_ENGINE_VERSION,
            "--probe-timeout-seconds",
            "45",
        ]
    )
    report = run_grill_unreal_source_smoke.build_report(args)

    assert report["status"] == "pass"
    assert recorded["timeout_seconds"] == 45.0


def test_stage_example_project_replaces_embedded_plugin_with_live_checkout(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    example = tmp_path / "example"
    write_plugin(plugin, whitelist=["Win64"])
    write_example(example)
    embedded_plugin = example / "Plugins" / "plugin"
    embedded_plugin.mkdir(parents=True)
    (embedded_plugin / "marker.txt").write_text("stale\n", encoding="utf-8")

    stage = run_grill_unreal_source_smoke.stage_example_project(example, plugin, "5.8")
    staged_example = Path(stage["staged_example_root"])
    staged_plugin = Path(stage["staged_plugin_root"])

    assert staged_example.is_dir()
    assert staged_plugin.exists()
    assert (staged_plugin / "GRILLDISForUnreal.uplugin").is_file()
    assert not (staged_plugin / "marker.txt").exists()
    assert (staged_plugin / "Source" / "ThirdParty" / "Binaries" / "Win64" / "OpenDIS6.lib").is_file()
    staged_project = json.loads((staged_example / "GRILLDISExample.uproject").read_text(encoding="utf-8"))
    plugin_states = {row["Name"]: row["Enabled"] for row in staged_project["Plugins"]}
    assert plugin_states["CesiumForUnreal"] is False
    assert plugin_states["LowEntryExtStdLib"] is False
    assert plugin_states["GRILLDISForUnreal"] is True
    assert stage["disabled_optional_plugins"] == ["CesiumForUnreal", "LowEntryExtStdLib"]
    assert stage["removed_optional_plugin_dirs"] == ["CesiumForUnreal", "LowEntryExtStdLib"]
    assert not (staged_example / "Plugins" / "CesiumForUnreal").exists()
    assert not (staged_example / "Plugins" / "LowEntryExtStdLib").exists()
    assert any(path.endswith("GRILLDISExample.Build.cs") for path in stage["compatibility_patches"])
    assert any(path.endswith("Custom_BPFL.h") for path in stage["compatibility_patches"])
    assert any(path.endswith("Custom_BPFL.cpp") for path in stage["compatibility_patches"])
    assert "CesiumRuntime" not in (staged_example / "Source" / "GRILLDISExample" / "GRILLDISExample.Build.cs").read_text(encoding="utf-8")


def test_build_report_stages_windows_example_before_probe(tmp_path: Path, monkeypatch) -> None:
    plugin = tmp_path / "plugin"
    example = tmp_path / "example"
    write_plugin(plugin, whitelist=["Win64"])
    write_example(example)

    install = type(
        "Install",
        (),
        {
            "version": "5.7",
            "to_dict": lambda self: {
                "version": "5.7",
                "install_root": "/UE_5.7",
                "editor_path": "/UE_5.7/Engine/Binaries/Win64/UnrealEditor.exe",
            },
        },
    )()

    recorded: dict[str, object] = {}

    monkeypatch.setattr(run_grill_unreal_source_smoke, "git_commit", lambda path: "deadbeef")
    monkeypatch.setattr(run_grill_unreal_source_smoke.unreal_env, "discover_installs", lambda: [install])
    monkeypatch.setattr(run_grill_unreal_source_smoke, "host_unreal_platform", lambda: "Win64")

    def fake_probe(resolved_install, project_path=None, *, timeout_seconds=20.0):
        recorded["project_path"] = project_path
        return {"status": "ok", "failure_kind": None, "detail": "ok", "command": [], "output": ""}

    monkeypatch.setattr(run_grill_unreal_source_smoke.unreal_env, "probe_host_platform_support", fake_probe)

    args = run_grill_unreal_source_smoke.parse_args(
        [
            "--plugin-root",
            str(plugin),
            "--example-root",
            str(example),
            "--engine-version",
            workflow_versions.DEFAULT_UNREAL_ENGINE_VERSION,
        ]
    )
    report = run_grill_unreal_source_smoke.build_report(args)

    assert report["status"] == "pass"
    assert "staged_project" in report
    assert str(recorded["project_path"]).startswith(str(run_grill_unreal_source_smoke.unreal_env.work_root()))
