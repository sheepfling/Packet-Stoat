from __future__ import annotations

import json
from pathlib import Path
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import unity_vendor_workflow


def test_doctor_payload_accepts_valid_layout(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Source").mkdir()
    (plugin_root / "native~").mkdir()
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_bytes(b"x" * 16384)
    monkeypatch.setenv("FASTDIS_CESIUM_UNITY_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )

    payload = unity_vendor_workflow.doctor_payload("cesium-unity", "6000.5", None)

    assert payload["status"] == "ok"
    assert payload["package_name"] == "com.cesium.unity"
    assert payload["source_checkout"] is True
    assert payload["source_checkout_prepared"] is True
    assert payload["source_checkout_importability"] == "unproven"
    assert any(check["name"] == "package_manifest" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["name"] == "unity version kind" and check["detail"] == "stable" for check in payload["checks"])
    assert any(check["name"] == "unity_importability" and check["status"] == "warn" for check in payload["checks"])


def test_doctor_payload_adds_root_hint_when_install_missing(monkeypatch) -> None:
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "resolve_install", lambda version=None: None)

    payload = unity_vendor_workflow.doctor_payload("cesium-unity", "6000.5", None)

    assert any(check["name"] == "unity discovery roots" and "FASTDIS_UNITY_ROOTS" in check["detail"] for check in payload["checks"])
    assert any("FASTDIS_UNITY_ROOTS" in step for step in payload["next_steps"])


def test_discover_prints_version_kind_and_hint(monkeypatch, capsys) -> None:
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "describe_host", lambda: {"installs": []})

    rc = unity_vendor_workflow.command_discover(type("Args", (), {"format": "text"})())
    out = capsys.readouterr().out

    assert rc == 1
    assert "No Unity installs discovered." in out
    assert "FASTDIS_UNITY_ROOTS" in out


def test_build_payload_dry_run_materializes_project(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Source" / "Runtime").mkdir(parents=True)
    (plugin_root / "Source" / "Editor").mkdir(parents=True)
    (plugin_root / "Source" / "Runtime" / "ConfigureReinterop.cs").write_text("// runtime\n", encoding="utf-8")
    (plugin_root / "Source" / "Editor" / "ConfigureReinteropEditor.cs").write_text("// editor\n", encoding="utf-8")
    (plugin_root / "Reinterop.dll").write_bytes(b"x" * 16384)
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )
    project_dir = tmp_path / "project"

    payload = unity_vendor_workflow.build_payload(
        vendor="cesium-unity",
        version="6000.5",
        plugin_root_arg=str(plugin_root),
        project_dir_arg=str(project_dir),
        json_out_arg=str(tmp_path / "report.json"),
        md_out_arg=str(tmp_path / "report.md"),
        clean_project=False,
        dry_run=True,
    )

    manifest = json.loads((project_dir / "Packages" / "manifest.json").read_text(encoding="utf-8"))
    assert payload["status"] == "dry-run"
    assert "com.cesium.unity" in manifest["dependencies"]
    assert manifest["dependencies"]["com.unity.modules.unitywebrequest"] == "1.0.0"
    assert Path(payload["staged_plugin_root"]).is_dir()
    assert payload["touched_reinterop_sources"]
    assert (project_dir / "Assets" / "Editor" / "CesiumUnityVendorSmoke.cs").is_file()


def test_inspect_reinterop_activation_collects_rsp_and_meta(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    staged_plugin_root = project_dir / "Packages" / "cesium-unity"
    bee_dir = project_dir / "Library" / "Bee" / "artifacts" / "abc123.dag"
    staged_plugin_root.mkdir(parents=True)
    bee_dir.mkdir(parents=True)
    (staged_plugin_root / "Reinterop.dll.meta").write_text(
        "labels:\n- RoslynAnalyzer\nPluginImporter:\n  platformData:\n  - first:\n      Editor: Editor\n    second:\n      enabled: 0\n",
        encoding="utf-8",
    )
    (staged_plugin_root / "Reinterop.dll").write_bytes(b"x" * 16384)
    (bee_dir / "CesiumForUnity.rsp").write_text(
        '-r:"Packages/cesium-unity/Reinterop.dll"\n-analyzer:"Packages/cesium-unity/Reinterop.dll"\n-langversion:9.0\n/additionalfile:"Library/Bee/artifacts/abc123.dag/CesiumForUnity.UnityAdditionalFile.txt"\n',
        encoding="utf-8",
    )
    (bee_dir / "CesiumForUnity.UnityAdditionalFile.txt").write_text(str(project_dir) + "\n", encoding="utf-8")
    generated_dir = project_dir / "Library" / "Bee" / "generated" / "reinterop"
    generated_dir.mkdir(parents=True)
    (generated_dir / "Reinterop.Generated.cs").write_text("// generated\n", encoding="utf-8")

    payload = unity_vendor_workflow.inspect_reinterop_activation(project_dir, staged_plugin_root)

    assert payload["analyzer_present_in_rsp"] is True
    assert payload["reference_present_in_rsp"] is True
    assert payload["langversion"] == "9.0"
    assert str(bee_dir / "CesiumForUnity.rsp") == payload["rsp_path"]
    assert payload["additional_file_preview"] == [str(project_dir)]
    assert payload["reinterop_meta"]["has_roslyn_label"] is True
    assert payload["reinterop_meta"]["editor_enabled"] is False
    assert payload["reinterop_dll_bytes"] == 16384
    assert payload["generated_reinterop_paths"]


def test_compatibility_findings_identify_stub_reinterop_inactivity_and_unity_api_drift() -> None:
    report = {
        "failure_tail": [
            "Packages\\cesium-unity\\Source\\Runtime\\Foo.cs(0,0): error CS0246: The type or namespace name 'Reinterop' could not be found",
            "Packages\\cesium-unity\\Source\\Runtime\\Foo.cs(1,1): error CS0246: The type or namespace name 'ReinteropNativeImplementationAttribute' could not be found",
            "Packages\\cesium-unity\\Source\\Editor\\IonAssetsTreeView.cs(103,34): error CS0619: 'TreeViewState' is obsolete",
            "Packages\\cesium-unity\\Source\\Runtime\\Foo.cs(2,1): error CS8795: Partial method must have an implementation part",
        ],
        "reinterop_activation": {
            "analyzer_present_in_rsp": True,
            "reference_present_in_rsp": True,
            "reinterop_dll_bytes": 4096,
            "generated_reinterop_paths": [],
            "reinterop_meta": {
                "editor_enabled": False,
            },
        },
    }

    findings = unity_vendor_workflow.compatibility_findings(report)

    assert [finding["kind"] for finding in findings] == [
        "reinterop-staged-artifact-stub",
        "reinterop-generator-inactive",
        "unity-6000-editor-api-drift",
    ]


def test_compatibility_findings_identify_generated_unity_6000_api_drift() -> None:
    report = {
        "failure_tail": [
            "Library\\Bee\\artifacts\\1900b0aE.dag\\Reinterop\\Reinterop.RoslynSourceGenerator\\ReinteropInitializer.cs(10,10): error CS0619: 'Object.GetInstanceID()' is obsolete",
            "Library\\Bee\\artifacts\\1900b0aE.dag\\Reinterop\\Reinterop.RoslynSourceGenerator\\ReinteropInitializer.cs(11,10): error CS0619: 'Physics.BakeMesh(int, bool)' is obsolete",
        ],
        "reinterop_activation": {
            "analyzer_present_in_rsp": True,
            "reference_present_in_rsp": True,
            "reinterop_dll_bytes": 181760,
            "generated_reinterop_paths": [],
            "reinterop_meta": {
                "editor_enabled": True,
            },
        },
    }

    findings = unity_vendor_workflow.compatibility_findings(report)

    assert [finding["kind"] for finding in findings] == [
        "unity-6000-generated-api-drift",
    ]


def test_build_payload_clean_project_uses_fresh_default_project_dir(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_bytes(b"x" * 16384)
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "work_root", lambda: tmp_path / "work")

    payload = unity_vendor_workflow.build_payload(
        vendor="cesium-unity",
        version="6000.5",
        plugin_root_arg=str(plugin_root),
        project_dir_arg=None,
        json_out_arg=str(tmp_path / "report.json"),
        md_out_arg=str(tmp_path / "report.md"),
        clean_project=True,
        dry_run=True,
    )

    assert "_fresh_" in payload["project_dir"]
    assert Path(payload["project_dir"]).is_dir()


def test_prepare_source_runs_reinterop_build_and_stages_outputs(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    build_dir = plugin_root / "Reinterop~" / "bin" / "Debug" / "netstandard2.0"
    obj_dir = plugin_root / "Reinterop~" / "obj" / "Debug" / "netstandard2.0"
    build_dir.mkdir(parents=True)
    obj_dir.mkdir(parents=True)
    (plugin_root / "Build~").mkdir()
    recorded: list[tuple[list[str], Path]] = []

    def fake_run(cmd: list[str], cwd: Path) -> int:
        recorded.append((cmd, cwd))
        (build_dir / "Reinterop.dll").write_bytes(b"x" * 16384)
        (build_dir / "Reinterop.pdb").write_bytes(b"x" * 128)
        (build_dir / "Microsoft.CodeAnalysis.dll").write_bytes(b"x" * 2048)
        (obj_dir / "Reinterop.deps.json").write_text("{}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(unity_vendor_workflow, "run_step_in_dir", fake_run)

    payload = unity_vendor_workflow.prepare_source_checkout("cesium-unity", str(plugin_root), dry_run=False)

    assert payload["status"] == "ok"
    assert recorded == [(["dotnet", "build", "Reinterop~/Reinterop.csproj"], plugin_root)]
    assert (plugin_root / "Reinterop.dll").is_file()
    assert (plugin_root / "Reinterop.pdb").is_file()
    assert (plugin_root / "Microsoft.CodeAnalysis.dll").is_file()
    assert (plugin_root / "Reinterop.deps.json").is_file()
    assert payload["reinterop_dll_bytes"] == 16384
    assert payload["process_provenance"]["process_matters_as_evidence"] is True


def test_doctor_payload_flags_stub_reinterop_artifact(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Source").mkdir()
    (plugin_root / "native~").mkdir()
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_bytes(b"x" * 4096)
    monkeypatch.setenv("FASTDIS_CESIUM_UNITY_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "resolve_install", lambda version=None: None)

    payload = unity_vendor_workflow.doctor_payload("cesium-unity", "6000.5", None)

    unity_importability = next(check for check in payload["checks"] if check["name"] == "unity_importability")
    assert unity_importability["status"] == "fail"
    assert "stub build artifact" in unity_importability["detail"]


def test_remove_tree_clears_read_only_file(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    child = root / "file.txt"
    child.write_text("x\n", encoding="utf-8")
    child.chmod(stat.S_IREAD)

    unity_vendor_workflow.remove_tree(root)

    assert not root.exists()


def test_remove_tree_retries_transient_directory_not_empty(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    calls = {"count": 0}

    def fake_rmtree(path: Path, onexc) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError(145, "directory is not empty")
        root.rmdir()

    monkeypatch.setattr(unity_vendor_workflow.shutil, "rmtree", fake_rmtree)
    monkeypatch.setattr(unity_vendor_workflow.time, "sleep", lambda _: None)

    unity_vendor_workflow.remove_tree(root)

    assert calls["count"] == 2
    assert not root.exists()


def test_handoff_payload_formats_upstream_issue_for_compile_failure(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
    project_dir = tmp_path / "project"
    build_json = tmp_path / "build.json"
    build_md = tmp_path / "build.md"
    build_log = tmp_path / "build.log"
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "describe_host", lambda: {"platform": "windows", "installs": []})

    def fake_run(cmd: list[str]) -> int:
        build_log.write_text(
            "error CS0246: ReinteropNativeImplementation missing\n"
            "error CS0759: partial method without implementation\n",
            encoding="utf-8",
        )
        return 2

    monkeypatch.setattr(unity_vendor_workflow, "run_step", fake_run)

    payload = unity_vendor_workflow.handoff_payload(
        vendor="cesium-unity",
        version="6000.5",
        plugin_root_arg=str(plugin_root),
        project_dir_arg=str(project_dir),
        build_json_out_arg=str(build_json),
        build_md_out_arg=str(build_md),
        clean_project=False,
        dry_run=False,
    )

    assert payload["schema"] == "packet_stoat.cesium_unity_upstream_handoff.v1"
    assert payload["status"] == "ready"
    assert payload["failure_class"] == "compile-or-import"
    assert "## Repro" in payload["issue_body_markdown"]
    assert "error CS0246" in payload["issue_body_markdown"]
    assert "## Reinterop Activation" in payload["issue_body_markdown"]


def test_handoff_payload_includes_compatibility_findings(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
    build_log = tmp_path / "build.json"
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "describe_host", lambda: {"platform": "windows", "installs": []})

    def fake_run(cmd: list[str]) -> int:
        build_log.with_suffix(".log").write_text(
            "error CS0246: ReinteropNativeImplementationAttribute missing\n"
            "error CS0619: 'TreeViewItem' is obsolete\n"
            "error CS8795: partial method without implementation\n",
            encoding="utf-8",
        )
        return 2

    monkeypatch.setattr(unity_vendor_workflow, "run_step", fake_run)
    monkeypatch.setattr(
        unity_vendor_workflow,
        "inspect_reinterop_activation",
        lambda project_dir, staged_plugin_root: {
            "analyzer_present_in_rsp": True,
            "generated_reinterop_paths": [],
            "reinterop_meta": {"editor_enabled": False},
        },
    )
    payload = unity_vendor_workflow.handoff_payload(
        vendor="cesium-unity",
        version="6000.5",
        plugin_root_arg=str(plugin_root),
        project_dir_arg=str(tmp_path / "project"),
        build_json_out_arg=str(build_log),
        build_md_out_arg=str(tmp_path / "build.md"),
        clean_project=False,
        dry_run=False,
    )

    assert "## Compatibility Findings" in payload["issue_body_markdown"]
    assert "reinterop-generator-inactive" in payload["issue_body_markdown"]


def test_build_payload_ignores_stale_json_when_compile_fails_before_smoke(monkeypatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"
    log_out = json_out.with_suffix(".log")
    json_out.write_text(
        json.dumps(
            {
                "staged_plugin_root": "C:\\stale\\Packages\\cesium-unity",
                "project_dir": "C:\\stale\\project",
                "package_imported": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    md_out.write_text("stale\n", encoding="utf-8")
    log_out.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )

    def fake_run(cmd: list[str]) -> int:
        log_out.write_text("error CS0246: compile failed\n", encoding="utf-8")
        return 2

    monkeypatch.setattr(unity_vendor_workflow, "run_step", fake_run)

    payload = unity_vendor_workflow.build_payload(
        vendor="cesium-unity",
        version="6000.5",
        plugin_root_arg=str(plugin_root),
        project_dir_arg=str(tmp_path / "project"),
        json_out_arg=str(json_out),
        md_out_arg=str(md_out),
        clean_project=False,
        dry_run=False,
    )

    assert payload["status"] == "fail"
    assert payload["project_dir"] != "C:\\stale\\project"
    assert "stale" not in payload["staged_plugin_root"]
    assert payload["package_imported"] is False


def test_handoff_command_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    plugin_root = tmp_path / "cesium-unity"
    plugin_root.mkdir()
    (plugin_root / "package.json").write_text(json.dumps({"name": "com.cesium.unity", "unity": "2022.3"}) + "\n", encoding="utf-8")
    (plugin_root / "Reinterop~").mkdir()
    (plugin_root / "Build~").mkdir()
    (plugin_root / "Reinterop.dll").write_text("stub\n", encoding="utf-8")
    build_log = tmp_path / "build.json"
    monkeypatch.setattr(
        unity_vendor_workflow.unity_env,
        "resolve_install",
        lambda version=None: unity_vendor_workflow.unity_env.UnityInstall(
            version="6000.5.0f1",
            install_root=str(tmp_path / "Unity"),
            editor_path=str(tmp_path / "Unity" / "Editor" / "Unity.exe"),
            editor_app_path=None,
            source="env:FASTDIS_UNITY_EDITOR",
            quirks=(),
        ),
    )
    monkeypatch.setattr(unity_vendor_workflow.unity_env, "describe_host", lambda: {"platform": "windows", "installs": []})

    def fake_run(cmd: list[str]) -> int:
        build_log.with_suffix(".log").write_text("error CS0246: compile failed\n", encoding="utf-8")
        return 2

    monkeypatch.setattr(unity_vendor_workflow, "run_step", fake_run)
    json_out = tmp_path / "handoff.json"
    md_out = tmp_path / "handoff.md"

    rc = unity_vendor_workflow.main(
        [
            "handoff",
            "--vendor",
            "cesium-unity",
            "--plugin-root",
            str(plugin_root),
            "--project-dir",
            str(tmp_path / "project"),
            "--build-json-out",
            str(build_log),
            "--build-md-out",
            str(tmp_path / "build.md"),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["handoff_json"] == str(json_out.resolve())
    assert json_out.is_file()
    assert md_out.is_file()
