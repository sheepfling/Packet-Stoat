from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_plugin_repo(plugin_root: Path) -> None:
    (plugin_root / ".git").mkdir(parents=True)
    (plugin_root / "Scripts" / "linux_proof_profiles").mkdir(parents=True)
    package = plugin_root / ".build" / "grill_buildplugin_linux" / "ue5.7.4-linux_ubuntu-24.04" / "package"
    (package / "Binaries" / "Linux").mkdir(parents=True)
    (package / "Source" / "ThirdParty" / "Binaries" / "Linux").mkdir(parents=True)
    (package / "GRILLDISForUnreal.uplugin").write_text(
        json.dumps(
            {
                "FriendlyName": "GRILL DIS for Unreal",
                "EngineVersion": "5.7.0",
                "Installed": True,
                "Modules": [
                    {"Name": "DISRuntime", "PlatformAllowList": ["Linux", "Mac", "Win64"]},
                    {"Name": "DISEditor", "PlatformAllowList": ["Linux", "Mac", "Win64"]},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (package / "Binaries" / "Linux" / "libUnrealEditor-DISRuntime.so").write_bytes(b"runtime")
    (package / "Binaries" / "Linux" / "libUnrealEditor-DISEditor.so").write_bytes(b"editor")
    (package / "Source" / "ThirdParty" / "Binaries" / "Linux" / "libOpenDIS6.a").write_bytes(b"opendis")
    (plugin_root / "Scripts" / "linux_proof_profiles" / "ubuntu_24_04_ue57.env").write_text(
        "\n".join(
            [
                "UE_PROOF_PROFILE=ubuntu-24.04",
                "UE_VERSION_LABEL=ue5.7.4-linux",
                "UE_LINUX_IMAGE=grill-linux-proof:ubuntu24.04",
                "DOCKER_PLATFORM=linux/amd64",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_report_passes_for_packaged_linux_proof(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("capture_grill_unreal_linux_build_proof", ROOT / "tools" / "capture_grill_unreal_linux_build_proof.py")
    plugin_root = tmp_path / "GRILL_DISPluginForUnreal"
    _write_plugin_repo(plugin_root)
    profile = plugin_root / "Scripts" / "linux_proof_profiles" / "ubuntu_24_04_ue57.env"
    package = plugin_root / ".build" / "grill_buildplugin_linux" / "ue5.7.4-linux_ubuntu-24.04" / "package"

    monkeypatch.setattr(module, "git_output", lambda _path, *args: {"rev-parse": "abc123"}.get(args[0], "origin"))

    args = module.parse_args(
        [
            "--plugin-root",
            str(plugin_root),
            "--profile",
            str(profile),
            "--package-dir",
            str(package),
            "--json-out",
            str(tmp_path / "proof.json"),
            "--md-out",
            str(tmp_path / "proof.md"),
        ]
    )
    report = module.build_report(args)

    assert report["schema"] == "fastdis.grill_unreal_linux_build_proof.v1"
    assert report["status"] == "pass"
    assert report["package"]["engine_version"] == "5.7.0"
    assert report["package"]["platform_allow_list"] == ["Linux", "Mac", "Win64"]
    assert len(report["package"]["required_artifacts"]) == 3
    assert report["blockers"] == []


def test_cli_writes_linux_proof_outputs(tmp_path: Path) -> None:
    plugin_root = tmp_path / "GRILL_DISPluginForUnreal"
    _write_plugin_repo(plugin_root)
    profile = plugin_root / "Scripts" / "linux_proof_profiles" / "ubuntu_24_04_ue57.env"
    package = plugin_root / ".build" / "grill_buildplugin_linux" / "ue5.7.4-linux_ubuntu-24.04" / "package"
    json_out = tmp_path / "proof.json"
    md_out = tmp_path / "proof.md"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "capture_grill_unreal_linux_build_proof.py"),
            "--plugin-root",
            str(plugin_root),
            "--profile",
            str(profile),
            "--package-dir",
            str(package),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert "Build-proof only" in payload["claim_boundary"]
    markdown = md_out.read_text(encoding="utf-8")
    assert "GRILL Unreal Linux Build Proof" in markdown
    assert "Required Artifacts" in markdown
