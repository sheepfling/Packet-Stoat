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


def _write_fixture_tree(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    plugin_dir = root / "packages" / "unreal" / "FastDis"
    linux_build_dir = root / "build" / "cmake" / "linux-x86_64"
    build_cs = plugin_dir / "Source" / "FastDisUnreal" / "FastDisUnreal.Build.cs"
    mac_install_smoke = root / "build" / "reports" / "unreal_packaged_install_smoke.json"
    linux_package_dir = root / "tmp" / "FastDisPackage"

    build_cs.parent.mkdir(parents=True, exist_ok=True)
    linux_build_dir.mkdir(parents=True, exist_ok=True)
    mac_install_smoke.parent.mkdir(parents=True, exist_ok=True)
    linux_package_dir.mkdir(parents=True, exist_ok=True)

    (plugin_dir / "FastDis.uplugin").write_text(
        json.dumps({"VersionName": "0.17.0-alpha12", "Version": 12}) + "\n",
        encoding="utf-8",
    )
    (plugin_dir / "README.md").write_text(
        "Plugins/FastDis/ThirdParty/fastdis/lib/Linux/libfastdis.so\n",
        encoding="utf-8",
    )
    build_cs.write_text(
        "\n".join(
            [
                "if (Target.Platform == UnrealTargetPlatform.Linux)",
                "{",
                '    PublicAdditionalLibraries.Add(Path.Combine(LibPath, "libfastdis.so"));',
                '    RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/FastDis/Linux/libfastdis.so");',
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (linux_build_dir / "libfastdis.so.0.13.0").write_bytes(b"linuxlib")
    mac_install_smoke.write_text(
        json.dumps({"status": "pass", "engine_version": "5.8", "package_dir": "/private/tmp/fastdis_unreal/FastDisPackage"}) + "\n",
        encoding="utf-8",
    )
    (linux_package_dir / "FastDis.uplugin").write_text("{}\n", encoding="utf-8")
    lib_dir = linux_package_dir / "ThirdParty" / "fastdis" / "lib" / "Linux"
    lib_dir.mkdir(parents=True, exist_ok=True)
    (lib_dir / "libfastdis.so").write_bytes(b"packaged")
    return plugin_dir, linux_build_dir, build_cs, mac_install_smoke, linux_package_dir


def test_build_report_marks_package_proof_when_linux_package_exists(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("capture_fastdis_unreal_linux_proof", ROOT / "tools" / "capture_fastdis_unreal_linux_proof.py")
    plugin_dir, linux_build_dir, build_cs, mac_install_smoke, linux_package_dir = _write_fixture_tree(tmp_path)

    monkeypatch.setattr(module, "git_output", lambda _path, *args: "abc123")

    args = module.parse_args(
        [
            "--plugin-dir",
            str(plugin_dir),
            "--linux-build-dir",
            str(linux_build_dir),
            "--build-cs",
            str(build_cs),
            "--mac-install-smoke",
            str(mac_install_smoke),
            "--linux-package-dir",
            str(linux_package_dir),
            "--json-out",
            str(tmp_path / "proof.json"),
            "--md-out",
            str(tmp_path / "proof.md"),
        ]
    )
    report = module.build_report(args)

    assert report["schema"] == "fastdis.fastdis_unreal_linux_proof.v1"
    assert report["status"] == "package-proof"
    assert report["linux_native"]["library"]["exists"] is True
    assert report["linux_package"]["library"]["exists"] is True
    assert report["blockers"] == []


def test_cli_writes_fastdis_linux_proof_outputs(tmp_path: Path) -> None:
    plugin_dir, linux_build_dir, build_cs, mac_install_smoke, linux_package_dir = _write_fixture_tree(tmp_path)
    json_out = tmp_path / "proof.json"
    md_out = tmp_path / "proof.md"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "capture_fastdis_unreal_linux_proof.py"),
            "--plugin-dir",
            str(plugin_dir),
            "--linux-build-dir",
            str(linux_build_dir),
            "--build-cs",
            str(build_cs),
            "--mac-install-smoke",
            str(mac_install_smoke),
            "--linux-package-dir",
            str(linux_package_dir),
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
    assert payload["status"] == "package-proof"
    assert "payload readiness" in payload["claim_boundary"] or "built Linux native lib" in payload["claim_boundary"]
    markdown = md_out.read_text(encoding="utf-8")
    assert "FastDIS Unreal Linux Proof" in markdown
    assert "Linux Package" in markdown
