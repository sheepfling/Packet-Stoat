#!/usr/bin/env python3
"""Operator-facing Unity vendor-package workflow wrapper."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time

import load_local_env
import run_unity_editor_tests
import unity_env
import workspace_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "unity_vendor_plugin"
MANIFEST = workspace_manifest.load_manifest()
UNITY_SURFACE = workspace_manifest.surface_spec("unity", MANIFEST)
PACKAGE_NAME = "com.cesium.unity"
SCRATCH_PROJECT_DEPENDENCIES: dict[str, str] = {
    "com.unity.feature.development": "1.0.2",
    "com.unity.ide.visualstudio": "2.0.23",
    "com.unity.inputsystem": "1.14.2",
    "com.unity.test-framework": "1.6.4",
    "com.unity.textmeshpro": "3.2.0-pre.10",
    "com.unity.timeline": "1.8.7",
    "com.unity.ugui": "2.0.0",
    "com.unity.visualscripting": "1.9.9",
    "com.unity.modules.imageconversion": "1.0.0",
    "com.unity.modules.imgui": "1.0.0",
    "com.unity.modules.jsonserialize": "1.0.0",
    "com.unity.modules.ui": "1.0.0",
    "com.unity.modules.uielements": "1.0.0",
    "com.unity.modules.unitywebrequest": "1.0.0",
    "com.unity.modules.unitywebrequestassetbundle": "1.0.0",
    "com.unity.modules.unitywebrequestaudio": "1.0.0",
    "com.unity.modules.unitywebrequesttexture": "1.0.0",
}


def preferred_unity_version() -> str:
    return workspace_manifest.surface_preferred_version(UNITY_SURFACE, MANIFEST)


def preferred_unity_editor_build() -> str:
    version = preferred_unity_version()
    return version if version.count(".") >= 2 else f"{version}.0f1"


def process_provenance(plugin_root: Path | None = None) -> dict[str, object]:
    global_json = plugin_root / "global.json" if plugin_root is not None else None
    sdk_version = None
    if global_json is not None and global_json.is_file():
        try:
            sdk_version = json.loads(global_json.read_text(encoding="utf-8")).get("sdk", {}).get("version")
        except (OSError, json.JSONDecodeError, AttributeError):
            sdk_version = None
    return {
        "leading_edge_reporting": True,
        "process_matters_as_evidence": True,
        "operator_interventions": [
            {
                "kind": "source-prep",
                "value": "dotnet publish Reinterop~ -o .",
                "reason": "materialize Reinterop.dll so the raw source checkout becomes importable by Unity",
            },
            {
                "kind": "generator-trigger",
                "value": "stage the package into the scratch project and touch ConfigureReinterop.cs plus ConfigureReinteropEditor.cs",
                "reason": "match Cesium's upstream guidance for forcing Reinterop to regenerate C# and C++ glue during source-checkout verification",
            }
        ],
        "sdk_pin": sdk_version,
        "reporting_expectation": "Report SDK pin changes, package-manifest tweaks, and any manual import-enablement steps together with the compile result.",
    }


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, cwd=ROOT, env=unity_env.build_env())
    return completed.returncode


def run_step_in_dir(cmd: list[str], cwd: Path) -> int:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, cwd=cwd, env=unity_env.build_env())
    return completed.returncode


def vendor_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        raise SystemExit("Vendor id must not be empty.")
    return slug


def vendor_env_token(value: str) -> str:
    return vendor_slug(value).replace("-", "_").upper()


def _resolve_env_path(keys: list[str]) -> Path | None:
    for key in keys:
        raw = os.environ.get(key)
        if raw:
            return Path(raw).expanduser()
    return None


def resolve_plugin_root(vendor: str, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_token = vendor_env_token(vendor)
    candidate = _resolve_env_path(
        [
            f"FASTDIS_{env_token}_PLUGIN_ROOT",
            f"FASTDIS_{env_token}_UNITY_PLUGIN_ROOT",
            "FASTDIS_UNITY_VENDOR_PLUGIN_ROOT",
        ]
    )
    return None if candidate is None else candidate.resolve()


def resolve_package_manifest(plugin_root: Path | None) -> Path | None:
    if plugin_root is None:
        return None
    package_json = plugin_root / "package.json"
    return package_json if package_json.is_file() else None


def load_package_metadata(package_manifest: Path | None) -> dict[str, object] | None:
    if package_manifest is None:
        return None
    try:
        return json.loads(package_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def resolve_install(version: str | None) -> unity_env.UnityInstall | None:
    return unity_env.resolve_install(version)


def plugin_uses_source_checkout(plugin_root: Path | None) -> bool:
    if plugin_root is None:
        return False
    return (plugin_root / "Reinterop~").is_dir() and (plugin_root / "Build~").is_dir()


def reinterop_dll_path(plugin_root: Path) -> Path:
    return plugin_root / "Reinterop.dll"


def source_checkout_prepared(plugin_root: Path | None) -> bool:
    if plugin_root is None:
        return False
    return reinterop_dll_path(plugin_root).is_file()


def source_checkout_importability_status(plugin_root: Path | None) -> tuple[str, str]:
    if plugin_root is None:
        return "fail", "plugin root missing"
    if not plugin_uses_source_checkout(plugin_root):
        return "ok", "plugin root is not using the raw cesium-unity source-checkout path"
    if not source_checkout_prepared(plugin_root):
        return "fail", "Reinterop.dll is missing, so the source checkout is not even prepped"
    return (
        "warn",
        "Reinterop.dll exists, but Unity importability is still unproven until the scratch-project import smoke passes.",
    )


def _unity_root_hint() -> str:
    system = unity_env.platform.system().lower()
    if system == "windows":
        return r'FASTDIS_UNITY_ROOTS="C:\Program Files\Unity\Hub\Editor;D:\Unity\Hub\Editor"'
    if system == "darwin":
        return 'FASTDIS_UNITY_ROOTS="/Applications/Unity/Hub/Editor:$HOME/Applications/Unity/Hub/Editor"'
    return 'FASTDIS_UNITY_ROOTS="$HOME/Unity/Hub/Editor:/opt/Unity/Hub/Editor"'


def _selected_stable_over_newer_prerelease(install: unity_env.UnityInstall | None) -> str | None:
    if install is None or unity_env.version_kind(install.version) != "stable":
        return None
    host = unity_env.describe_host()
    selected_parsed = unity_env._parse_unity_version(install.version)
    if selected_parsed is None:
        return None
    selected_base = tuple(selected_parsed["base"])
    newer_prereleases: list[str] = []
    for row in host.get("installs") or []:
        if str(row.get("install_root") or "") == install.install_root:
            continue
        row_version = str(row.get("version") or "")
        if not unity_env.version_kind(row_version).startswith("prerelease:"):
            continue
        parsed = unity_env._parse_unity_version(row_version)
        if parsed is None:
            continue
        if tuple(parsed["base"]) > selected_base:
            newer_prereleases.append(row_version)
    if not newer_prereleases:
        return None
    return ",".join(newer_prereleases)


def doctor_payload(vendor: str, version: str | None, plugin_root_arg: str | None) -> dict[str, object]:
    install = resolve_install(version)
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    package_manifest = resolve_package_manifest(plugin_root)
    package_metadata = load_package_metadata(package_manifest)

    payload: dict[str, object] = {
        "vendor": vendor_slug(vendor),
        "requested_version": version,
        "resolved_version": install.version if install is not None else None,
        "status": "ok",
        "plugin_root": str(plugin_root) if plugin_root is not None else None,
        "package_manifest": str(package_manifest) if package_manifest is not None else None,
        "package_name": package_metadata.get("name") if isinstance(package_metadata, dict) else None,
        "package_unity": package_metadata.get("unity") if isinstance(package_metadata, dict) else None,
        "install": install.to_dict() if install is not None else None,
        "checks": [],
        "next_steps": [],
        "source_checkout": False,
        "source_checkout_prepared": None,
        "source_checkout_importability": "unproven",
    }

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if plugin_root is None:
        add_check("plugin_root", "fail", f"no plugin root configured for vendor {vendor_slug(vendor)}")
    elif not plugin_root.is_dir():
        add_check("plugin_root", "fail", f"plugin root is not a directory: {plugin_root}")
    else:
        add_check("plugin_root", "ok", str(plugin_root))

    add_check(
        "package_manifest",
        "ok" if package_manifest is not None else "fail",
        str(package_manifest) if package_manifest is not None else "missing package.json at plugin root",
    )
    add_check(
        "package_name",
        "ok" if isinstance(package_metadata, dict) and package_metadata.get("name") == PACKAGE_NAME else "fail",
        str(package_metadata.get("name")) if isinstance(package_metadata, dict) and package_metadata.get("name") else f"expected {PACKAGE_NAME}",
    )
    add_check(
        "source_dir",
        "ok" if plugin_root is not None and (plugin_root / "Source").is_dir() else "fail",
        str(plugin_root / "Source") if plugin_root is not None else "missing Source path",
    )
    add_check(
        "native_dir",
        "ok" if plugin_root is not None and (plugin_root / "native~").is_dir() else "fail",
        str(plugin_root / "native~") if plugin_root is not None else "missing native~ path",
    )
    uses_source_checkout = plugin_uses_source_checkout(plugin_root)
    payload["source_checkout"] = uses_source_checkout
    if uses_source_checkout and plugin_root is not None:
        prepared = source_checkout_prepared(plugin_root)
        payload["source_checkout_prepared"] = prepared
        add_check("source_checkout", "ok", "Reinterop~/ and Build~/ present")
        add_check(
            "reinterop_dll",
            "ok" if prepared else "fail",
            str(reinterop_dll_path(plugin_root)),
        )
        importability_status, importability_detail = source_checkout_importability_status(plugin_root)
        payload["source_checkout_importability"] = "unproven" if importability_status == "warn" else ("prepared" if importability_status == "ok" else "not-ready")
        add_check("unity_importability", importability_status, importability_detail)
    elif plugin_root is not None:
        payload["source_checkout_prepared"] = None
        payload["source_checkout_importability"] = "n/a"
        add_check("source_checkout", "ok", "plugin root does not expose the cesium-unity source layout")
    if install is None:
        add_check("unity_editor", "fail", f"no Unity install discovered for {version or preferred_unity_version()}")
        add_check("unity discovery roots", "warn", f"no install discovered; try {_unity_root_hint()}")
    else:
        add_check("unity_editor", "ok" if install.editor_path is not None else "fail", install.editor_path or "missing editor executable")
        add_check("unity_version", "ok", install.version)
        add_check("unity version kind", "ok", unity_env.version_kind(install.version))
        prerelease_note = _selected_stable_over_newer_prerelease(install)
        if prerelease_note:
            add_check("version selection", "ok", f"selected stable {install.version}; newer prerelease installs also exist: {prerelease_note}")

    payload["checks"] = checks
    failures = [check for check in checks if check["status"] == "fail"]
    payload["status"] = "ok" if not failures else "needs-attention"
    if failures:
        payload["next_steps"] = [
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT to the local Cesium Unity checkout root, or pass --plugin-root.",
            "Point FASTDIS_UNITY_EDITOR at a supported Unity Editor if discovery does not find the right install.",
            f"If Unity is installed outside the standard Hub roots, try {_unity_root_hint()}.",
            "Verify the checkout root exposes package.json, Source/, and native~/ like the public cesium-unity source route.",
            "If this is a raw cesium-unity source checkout, run python tools/unity_vendor_workflow.py prepare-source --vendor cesium-unity before the import smoke.",
        ]
    else:
        payload["next_steps"] = [
            f"Run the scratch-project compile lane: python tools/unity_vendor_workflow.py build --vendor {vendor_slug(vendor)} --unity-version {install.version or preferred_unity_version()}",
            "Do not treat a prepared source checkout as importable until that scratch-project lane passes.",
            "Keep the vendor compile lane green before claiming example-project parity.",
        ]
    return payload


def print_doctor(payload: dict[str, object]) -> None:
    print(f"Unity vendor doctor for {payload['vendor']}")
    print(f"status: {payload['status']}")
    print(f"requested_version: {payload['requested_version'] or 'default'}")
    print(f"resolved_version: {payload['resolved_version'] or 'none'}")
    print(f"plugin_root: {payload['plugin_root'] or 'missing'}")
    print(f"package_manifest: {payload['package_manifest'] or 'missing'}")
    print(f"source_checkout: {payload['source_checkout']}")
    print(f"source_checkout_prepared: {payload['source_checkout_prepared']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _remove_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def _onexc(func, entry_path, exc) -> None:
        if isinstance(exc, PermissionError):
            try:
                os.chmod(entry_path, stat.S_IWRITE)
            except OSError:
                pass
            try:
                func(entry_path)
            except OSError:
                pass
            return
        raise exc

    last_error: OSError | None = None
    for attempt in range(6):
        try:
            shutil.rmtree(path, onexc=_onexc)
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
            if not path.exists():
                return
            time.sleep(0.25 * (attempt + 1))
    if last_error is not None:
        raise last_error


def _package_file_reference(plugin_root: Path, project_dir: Path) -> str:
    relative = os.path.relpath(plugin_root, project_dir / "Packages").replace("\\", "/")
    return f"file:{relative}"


def _staged_plugin_root(project_dir: Path, plugin_root: Path) -> Path:
    return project_dir / "Packages" / plugin_root.name


def _copy_plugin_tree(plugin_root: Path, destination: Path) -> None:
    ignore = shutil.ignore_patterns(".git", ".vs", "bin", "obj")
    shutil.copytree(plugin_root, destination, ignore=ignore, dirs_exist_ok=True)


def _touch_reinterop_sources(plugin_root: Path) -> list[str]:
    touched: list[str] = []
    for relative in ("Source/Runtime/ConfigureReinterop.cs", "Source/Editor/ConfigureReinteropEditor.cs"):
        path = plugin_root / relative
        if path.is_file():
            os.utime(path, None)
            touched.append(str(path))
    return touched


def stage_plugin_root(project_dir: Path, plugin_root: Path) -> tuple[Path, list[str]]:
    staged_root = _staged_plugin_root(project_dir, plugin_root)
    _copy_plugin_tree(plugin_root, staged_root)
    touched = _touch_reinterop_sources(staged_root) if plugin_uses_source_checkout(plugin_root) else []
    return staged_root, touched


def create_project(project_dir: Path, plugin_root: Path) -> tuple[Path, list[str]]:
    if project_dir.exists():
        remove_tree(project_dir)
    (project_dir / "Assets" / "Editor").mkdir(parents=True)
    (project_dir / "Packages").mkdir(parents=True)
    (project_dir / "ProjectSettings").mkdir(parents=True)
    package_root, touched_reinterop = stage_plugin_root(project_dir, plugin_root)
    manifest = {
        "dependencies": {
            **SCRATCH_PROJECT_DEPENDENCIES,
            PACKAGE_NAME: _package_file_reference(package_root, project_dir),
        }
    }
    _write_text(project_dir / "Packages" / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    _write_text(
        project_dir / "ProjectSettings" / "ProjectVersion.txt",
        f"m_EditorVersion: {preferred_unity_editor_build()}\nm_EditorVersionWithRevision: {preferred_unity_editor_build()}\n",
    )
    _write_text(
        project_dir / "Assets" / "Editor" / "CesiumUnityVendorSmoke.cs",
        """
using System;
using System.IO;
using System.Linq;
using UnityEditor;

public static class CesiumUnityVendorSmoke
{
    public static void Run()
    {
        string reportPath = GetArgument("-fastdisReportPath");
        string packageCache = Path.Combine(Environment.CurrentDirectory, "Library", "PackageCache");
        bool packageCacheExists = Directory.Exists(packageCache);
        bool packageImported = packageCacheExists && Directory.GetDirectories(packageCache, "com.cesium.unity@*").Any();

        string json = "{\\n"
            + "  \\"status\\": \\"" + (packageImported ? "pass" : "fail") + "\\",\\n"
            + "  \\"package_imported\\": " + (packageImported ? "true" : "false") + ",\\n"
            + "  \\"package_cache\\": \\"" + packageCache.Replace("\\\\", "/") + "\\"\\n"
            + "}\\n";

        if (!string.IsNullOrEmpty(reportPath))
        {
            File.WriteAllText(reportPath, json);
        }

        EditorApplication.Exit(packageImported ? 0 : 3);
    }

    private static string GetArgument(string name)
    {
        string[] args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == name)
            {
                return args[i + 1];
            }
        }
        return string.Empty;
    }
}
""".strip()
        + "\n",
    )
    return package_root, touched_reinterop


def build_unity_command(editor: str, project_dir: Path, log_path: Path, report_path: Path) -> list[str]:
    cmd = [editor]
    cmd.extend(["-batchmode", *run_unity_editor_tests.unity_graphics_args()])
    cmd.extend(
        [
            "-accept-apiupdate",
            "-quit",
            "-projectPath",
            str(project_dir),
            "-executeMethod",
            "CesiumUnityVendorSmoke.Run",
            "-fastdisReportPath",
            str(report_path),
            "-logFile",
            str(log_path),
        ]
    )
    return cmd


def _default_project_dir(vendor: str, version: str | None) -> Path:
    version_slug = (version or preferred_unity_version()).replace(".", "_")
    return unity_env.work_root() / "vendor_install_smoke" / vendor_slug(vendor) / version_slug


def _fresh_project_dir(base_dir: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return base_dir.parent / f"{base_dir.name}_fresh_{stamp}"


def _default_report_paths(vendor: str, version: str | None) -> tuple[Path, Path]:
    version_slug = (version or preferred_unity_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Unity Vendor Install Smoke",
        "",
        f"- vendor: `{report['vendor']}`",
        f"- unity_version: `{report.get('unity_version', 'unknown')}`",
        f"- status: `{report['status']}`",
        f"- plugin_root: `{report.get('plugin_root', '')}`",
        f"- project_dir: `{report.get('project_dir', '')}`",
        f"- log: `{report.get('log', '')}`",
        "",
        "## Checks",
        "",
        f"- package_imported: `{report.get('package_imported', False)}`",
        f"- package_cache: `{report.get('package_cache', '')}`",
        "",
    ]
    activation = report.get("reinterop_activation")
    if isinstance(activation, dict):
        lines.extend(
            [
                "## Reinterop Activation",
                "",
                f"- rsp_path: `{activation.get('rsp_path') or ''}`",
                f"- analyzer_present_in_rsp: `{activation.get('analyzer_present_in_rsp', False)}`",
                f"- langversion: `{activation.get('langversion') or ''}`",
                f"- additional_file_path: `{activation.get('additional_file_path') or ''}`",
                f"- generated_reinterop_paths: `{len(activation.get('generated_reinterop_paths') or [])}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_report(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")


def _default_handoff_paths(vendor: str, version: str | None) -> tuple[Path, Path]:
    version_slug = (version or preferred_unity_version()).replace(".", "_")
    base = DEFAULT_REPORT_DIR / f"{vendor_slug(vendor)}_{version_slug}_upstream_handoff"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _tail_file(path: Path, lines: int = 20) -> list[str]:
    if not path.is_file():
        return []
    try:
        rows = [row for row in path.read_text(encoding="utf-8", errors="replace").splitlines() if row.strip()]
    except OSError:
        return []
    return rows[-lines:]


def _extract_first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else None


def _parse_reinterop_meta(meta_path: Path) -> dict[str, object]:
    if not meta_path.is_file():
        return {"meta_path": str(meta_path), "exists": False}
    try:
        text = meta_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"meta_path": str(meta_path), "exists": True, "readable": False}
    return {
        "meta_path": str(meta_path),
        "exists": True,
        "readable": True,
        "has_roslyn_label": "RoslynAnalyzer" in text,
        "editor_enabled": bool(re.search(r"first:\s+Editor: Editor\s+second:\s+enabled:\s+1", text, flags=re.MULTILINE)),
        "any_enabled": bool(re.search(r"enabled:\s+1", text)),
    }


def _find_rsp_with_reinterop(project_dir: Path, staged_plugin_root: Path) -> Path | None:
    library_dir = project_dir / "Library"
    if not library_dir.is_dir():
        return None
    needle = f'-analyzer:"Packages/{staged_plugin_root.name}/Reinterop.dll"'
    for rsp_path in library_dir.rglob("*.rsp"):
        try:
            text = rsp_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if needle in text:
            return rsp_path
    return None


def _list_generated_reinterop_paths(project_dir: Path) -> list[str]:
    library_dir = project_dir / "Library"
    if not library_dir.is_dir():
        return []
    generated: list[str] = []
    for path in library_dir.rglob("*"):
        if not path.exists():
            continue
        name = path.name.lower()
        full = str(path).lower()
        if "reinterop" in name and ("generated" in full or path.suffix.lower() in {".cs", ".cpp", ".h"}):
            generated.append(str(path))
            if len(generated) >= 20:
                break
    return generated


def inspect_reinterop_activation(project_dir: Path, staged_plugin_root: Path) -> dict[str, object]:
    rsp_path = _find_rsp_with_reinterop(project_dir, staged_plugin_root)
    analyzer_present = False
    additional_file_path: str | None = None
    additional_file_preview: list[str] = []
    langversion: str | None = None
    if rsp_path is not None:
        try:
            rsp_text = rsp_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            rsp_text = ""
        analyzer_present = f'-analyzer:"Packages/{staged_plugin_root.name}/Reinterop.dll"' in rsp_text
        additional_file_path = _extract_first_match(rsp_text, r'/additionalfile:"([^"]+)"')
        langversion = _extract_first_match(rsp_text, r"-langversion:([^\r\n]+)")
        if additional_file_path is not None:
            candidate = project_dir / Path(additional_file_path)
            if candidate.is_file():
                try:
                    additional_file_preview = candidate.read_text(encoding="utf-8", errors="replace").splitlines()[:5]
                except OSError:
                    additional_file_preview = []
    return {
        "reinterop_meta": _parse_reinterop_meta(staged_plugin_root / "Reinterop.dll.meta"),
        "rsp_path": str(rsp_path) if rsp_path is not None else None,
        "analyzer_present_in_rsp": analyzer_present,
        "langversion": langversion,
        "additional_file_path": additional_file_path,
        "additional_file_preview": additional_file_preview,
        "generated_reinterop_paths": _list_generated_reinterop_paths(project_dir),
    }


def classify_build_failure(report: dict[str, object]) -> str:
    status = str(report.get("status") or "")
    if status == "pass":
        return "verified-build"
    if status == "dry-run":
        return "dry-run"
    if not report.get("plugin_root") or not report.get("unity_version"):
        return "setup-missing"
    failure_text = "\n".join(str(line) for line in report.get("failure_tail", []))
    lowered = failure_text.lower()
    if any(token in lowered for token in ("cs0246", "cs0759", "error cs", "compile errors", "all compiler errors")):
        return "compile-or-import"
    if any(token in lowered for token in ("could not locate a unity editor", "missing editor executable")):
        return "toolchain-missing"
    if report.get("returncode") is not None:
        return "build-failed"
    return "needs-triage"


def compatibility_findings(report: dict[str, object]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    failure_tail = [str(line) for line in report.get("failure_tail", [])]
    failure_text = "\n".join(failure_tail)
    activation = report.get("reinterop_activation") if isinstance(report.get("reinterop_activation"), dict) else {}
    generated_reinterop_paths = activation.get("generated_reinterop_paths") if isinstance(activation, dict) else []
    analyzer_present = bool(activation.get("analyzer_present_in_rsp")) if isinstance(activation, dict) else False
    meta = activation.get("reinterop_meta") if isinstance(activation.get("reinterop_meta"), dict) else {}
    editor_enabled = bool(meta.get("editor_enabled")) if isinstance(meta, dict) else False

    if (
        analyzer_present
        and not generated_reinterop_paths
        and (
            "ReinteropNativeImplementationAttribute" in failure_text
            or "ReinteropAttribute" in failure_text
            or "error CS8795" in failure_text
        )
    ):
        findings.append(
            {
                "kind": "reinterop-generator-inactive",
                "summary": "Unity includes Reinterop.dll in Bee/Roslyn compilation, but no generated Reinterop outputs appear before compile fails.",
                "detail": (
                    f"analyzer_present_in_rsp={analyzer_present}; "
                    f"generated_reinterop_paths={len(generated_reinterop_paths)}; "
                    f"reinterop_meta_editor_enabled={editor_enabled}"
                ),
            }
        )

    if "TreeViewItem' is obsolete" in failure_text or "TreeViewState' is obsolete" in failure_text:
        findings.append(
            {
                "kind": "unity-6000-editor-api-drift",
                "summary": "Unity 6000.5 surfaces deprecated TreeView editor APIs in Cesium's editor code as compile errors.",
                "detail": "IonAssetsTreeView.cs still uses TreeViewItem / TreeViewState legacy APIs.",
            }
        )

    return findings


def render_handoff_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Cesium Unity Upstream Handoff",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- status: `{payload['status']}`",
        f"- failure_class: `{payload['failure_class']}`",
        f"- source_repo: `{payload['source_repo']}`",
        f"- build_report_json: `{payload['build_report_json']}`",
        f"- build_log: `{payload['build_log']}`",
        "",
        "## Suggested Title",
        "",
        payload["title"],
        "",
        "## Suggested Issue Body",
        "",
        payload["issue_body_markdown"].rstrip(),
        "",
    ]
    return "\n".join(lines)


def write_handoff(payload: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_handoff_markdown(payload), encoding="utf-8")


def build_payload(
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    project_dir_arg: str | None,
    json_out_arg: str | None,
    md_out_arg: str | None,
    clean_project: bool,
    dry_run: bool,
) -> dict[str, object]:
    install = resolve_install(version)
    if install is None or not install.editor_path:
        raise SystemExit("Could not locate a Unity Editor. Set --unity-version or FASTDIS_UNITY_EDITOR.")
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    if plugin_root is None or not plugin_root.is_dir():
        raise SystemExit(f"Could not resolve plugin root for vendor {vendor_slug(vendor)}.")
    package_manifest = resolve_package_manifest(plugin_root)
    if package_manifest is None:
        raise SystemExit(f"Could not find package.json under {plugin_root}.")
    if plugin_uses_source_checkout(plugin_root) and not source_checkout_prepared(plugin_root):
        raise SystemExit(
            f"Plugin root {plugin_root} is a raw cesium-unity source checkout without Reinterop.dll. "
            "Run `python tools/unity_vendor_workflow.py prepare-source --vendor cesium-unity` first."
        )

    if project_dir_arg:
        project_dir = Path(project_dir_arg).expanduser().resolve()
    else:
        project_dir = _default_project_dir(vendor, version)
        if clean_project:
            project_dir = _fresh_project_dir(project_dir)
    json_out, md_out = _default_report_paths(vendor, version)
    if json_out_arg:
        json_out = Path(json_out_arg).expanduser().resolve()
    if md_out_arg:
        md_out = Path(md_out_arg).expanduser().resolve()
    log_path = json_out.with_suffix(".log")

    if clean_project and project_dir.exists():
        remove_tree(project_dir)
    _remove_if_exists(json_out)
    _remove_if_exists(md_out)
    _remove_if_exists(log_path)
    staged_plugin_root, touched_reinterop = create_project(project_dir, plugin_root)
    cmd = build_unity_command(install.editor_path, project_dir, log_path, json_out)

    if dry_run:
        print("+", " ".join(str(part) for part in cmd))
        return {
            "vendor": vendor_slug(vendor),
            "unity_version": install.version,
            "status": "dry-run",
            "plugin_root": str(plugin_root),
            "staged_plugin_root": str(staged_plugin_root),
            "touched_reinterop_sources": touched_reinterop,
            "project_dir": str(project_dir),
            "json_out": str(json_out),
            "md_out": str(md_out),
            "log": str(log_path),
            "build_command": [str(part) for part in cmd],
            "package_imported": False,
            "package_cache": str(project_dir / "Library" / "PackageCache"),
            "process_provenance": process_provenance(plugin_root),
        }

    rc = run_step(cmd)
    report: dict[str, object] = {
        "vendor": vendor_slug(vendor),
        "unity_version": install.version,
        "status": "fail",
        "plugin_root": str(plugin_root),
        "staged_plugin_root": str(staged_plugin_root),
        "touched_reinterop_sources": touched_reinterop,
        "project_dir": str(project_dir),
        "json_out": str(json_out),
        "md_out": str(md_out),
        "log": str(log_path),
        "build_command": [str(part) for part in cmd],
        "returncode": rc,
        "package_imported": False,
        "package_cache": str(project_dir / "Library" / "PackageCache"),
        "process_provenance": process_provenance(plugin_root),
    }
    if json_out.is_file():
        try:
            loaded = json.loads(json_out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            report.update(loaded)
    report["failure_tail"] = _tail_file(log_path)
    report["reinterop_activation"] = inspect_reinterop_activation(project_dir, staged_plugin_root)
    report["compatibility_findings"] = compatibility_findings(report)
    report["status"] = "pass" if report.get("package_imported") and rc == 0 else "fail"
    write_report(report, json_out, md_out)
    return report


def handoff_payload(
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    project_dir_arg: str | None,
    build_json_out_arg: str | None,
    build_md_out_arg: str | None,
    clean_project: bool,
    dry_run: bool,
) -> dict[str, object]:
    build_report = build_payload(
        vendor=vendor,
        version=version,
        plugin_root_arg=plugin_root_arg,
        project_dir_arg=project_dir_arg,
        json_out_arg=build_json_out_arg,
        md_out_arg=build_md_out_arg,
        clean_project=clean_project,
        dry_run=dry_run,
    )
    failure_class = classify_build_failure(build_report)
    handoff_json, handoff_md = _default_handoff_paths(vendor, version)
    host = unity_env.describe_host()
    title = (
        f"{vendor_slug(vendor)} import fails on Unity {build_report.get('unity_version', 'unknown')}"
        if build_report.get("status") == "fail"
        else f"{vendor_slug(vendor)} import verification on Unity {build_report.get('unity_version', 'unknown')}"
    )
    repro_command = " ".join(str(part) for part in build_report.get("build_command", [])) or "unavailable"
    body_lines = [
        "## Summary",
        f"- classification: `{failure_class}`",
        f"- vendor: `{build_report['vendor']}`",
        f"- unity_version: `{build_report.get('unity_version') or 'unknown'}`",
        f"- host_platform: `{host.get('platform') or 'unknown'}`",
        f"- status: `{build_report.get('status')}`",
        "",
        "## Repro",
        f"```bash\n{repro_command}\n```",
        "",
        "## Evidence",
        f"- build_report_json: `{build_report['json_out']}`",
        f"- build_report_markdown: `{build_report['md_out']}`",
        f"- build_log: `{build_report['log']}`",
    ]
    activation = build_report.get("reinterop_activation")
    if isinstance(activation, dict):
        body_lines.extend(
            [
                "",
                "## Reinterop Activation",
                f"- rsp_path: `{activation.get('rsp_path') or 'missing'}`",
                f"- analyzer_present_in_rsp: `{activation.get('analyzer_present_in_rsp', False)}`",
                f"- langversion: `{activation.get('langversion') or 'unknown'}`",
                f"- additional_file_path: `{activation.get('additional_file_path') or 'missing'}`",
                f"- generated_reinterop_paths: `{len(activation.get('generated_reinterop_paths') or [])}`",
            ]
        )
        meta = activation.get("reinterop_meta")
        if isinstance(meta, dict):
            body_lines.extend(
                [
                    f"- reinterop_meta_has_roslyn_label: `{meta.get('has_roslyn_label', False)}`",
                    f"- reinterop_meta_editor_enabled: `{meta.get('editor_enabled', False)}`",
                    f"- reinterop_meta_any_enabled: `{meta.get('any_enabled', False)}`",
                ]
            )
    findings = build_report.get("compatibility_findings")
    if isinstance(findings, list) and findings:
        body_lines.extend(["", "## Compatibility Findings"])
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            body_lines.append(
                f"- `{finding.get('kind', 'finding')}`: {finding.get('summary', '').strip()} "
                f"({finding.get('detail', '').strip()})"
            )
    failure_tail = [str(line) for line in build_report.get("failure_tail", [])]
    if failure_tail:
        body_lines.extend(["", "## Failure Tail", "```text", *failure_tail, "```"])
    body_lines.extend(
        [
            "",
            "## Notes",
            "- This packet was generated from the Packet Stoat Cesium Unity vendor lane.",
            "- SDK pin shifts, source-prep steps, and import-enablement hacks should be reported together with the compile result.",
        ]
    )
    return {
        "schema": "packet_stoat.cesium_unity_upstream_handoff.v1",
        "mode": "handoff",
        "status": "ready" if failure_class in {"verified-build", "compile-or-import", "build-failed"} else "needs-attention",
        "vendor": build_report["vendor"],
        "source_repo": "https://github.com/CesiumGS/cesium-unity",
        "title": title,
        "failure_class": failure_class,
        "repro_command": repro_command,
        "build_report_json": build_report["json_out"],
        "build_report_markdown": build_report["md_out"],
        "build_log": build_report["log"],
        "handoff_json": str(handoff_json),
        "handoff_markdown": str(handoff_md),
        "issue_body_markdown": "\n".join(body_lines) + "\n",
        "build_report": build_report,
    }


def prepare_source_checkout(
    vendor: str,
    plugin_root_arg: str | None,
    dry_run: bool,
) -> dict[str, object]:
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    if plugin_root is None or not plugin_root.is_dir():
        raise SystemExit(f"Could not resolve plugin root for vendor {vendor_slug(vendor)}.")
    if not plugin_uses_source_checkout(plugin_root):
        raise SystemExit(f"Plugin root {plugin_root} does not look like a cesium-unity source checkout.")

    command = ["dotnet", "publish", "Reinterop~", "-o", "."]
    if dry_run:
        print("+", " ".join(command))
    else:
        rc = run_step_in_dir(command, plugin_root)
        if rc != 0:
            raise SystemExit("Cesium Unity source prep failed while publishing Reinterop.")

    return {
        "vendor": vendor_slug(vendor),
        "plugin_root": str(plugin_root),
        "reinterop_dll": str(reinterop_dll_path(plugin_root)),
        "status": "dry-run" if dry_run else ("ok" if source_checkout_prepared(plugin_root) else "needs-attention"),
        "process_provenance": process_provenance(plugin_root),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List discovered Unity installs")
    discover.add_argument("--format", choices=("text", "json"), default="text")

    doctor = subparsers.add_parser("doctor", help="Validate a vendor Unity package root against a selected Unity lane")
    doctor.add_argument("--vendor", required=True, help="Vendor id, for example cesium-unity")
    doctor.add_argument("--plugin-root", help="Vendor plugin checkout root")
    doctor.add_argument("--unity-version", help=f"Unity editor version prefix, for example {preferred_unity_version()}")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Import a vendor Unity package into a scratch project and verify package compilation/import")
    build.add_argument("--vendor", required=True, help="Vendor id, for example cesium-unity")
    build.add_argument("--plugin-root", help="Vendor plugin checkout root")
    build.add_argument("--unity-version", default=preferred_unity_version())
    build.add_argument("--project-dir", help="Scratch project directory")
    build.add_argument("--json-out", help="JSON report output path")
    build.add_argument("--md-out", help="Markdown report output path")
    build.add_argument("--clean-project", action="store_true")
    build.add_argument("--dry-run", action="store_true")

    prepare = subparsers.add_parser("prepare-source", help="Prepare a cesium-unity source checkout by publishing Reinterop")
    prepare.add_argument("--vendor", required=True, help="Vendor id, for example cesium-unity")
    prepare.add_argument("--plugin-root", help="Vendor plugin checkout root")
    prepare.add_argument("--dry-run", action="store_true")

    handoff = subparsers.add_parser("handoff", help="Run the Unity vendor smoke and emit an upstream-facing handoff packet")
    handoff.add_argument("--vendor", required=True, help="Vendor id, for example cesium-unity")
    handoff.add_argument("--plugin-root", help="Vendor plugin checkout root")
    handoff.add_argument("--unity-version", default=preferred_unity_version())
    handoff.add_argument("--project-dir", help="Scratch project directory")
    handoff.add_argument("--build-json-out", help="Build JSON report output path")
    handoff.add_argument("--build-md-out", help="Build Markdown report output path")
    handoff.add_argument("--json-out", help="Handoff JSON output path")
    handoff.add_argument("--md-out", help="Handoff Markdown output path")
    handoff.add_argument("--clean-project", action="store_true")
    handoff.add_argument("--dry-run", action="store_true")

    full = subparsers.add_parser("full", help="Doctor the vendor package, then run the scratch-project import smoke")
    full.add_argument("--vendor", required=True, help="Vendor id, for example cesium-unity")
    full.add_argument("--plugin-root", help="Vendor plugin checkout root")
    full.add_argument("--unity-version", default=preferred_unity_version())
    full.add_argument("--project-dir", help="Scratch project directory")
    full.add_argument("--json-out", help="JSON report output path")
    full.add_argument("--md-out", help="Markdown report output path")
    full.add_argument("--clean-project", action="store_true")
    full.add_argument("--dry-run", action="store_true")

    return parser.parse_args(argv)


def command_discover(args: argparse.Namespace) -> int:
    payload = unity_env.describe_host()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        if not payload["installs"]:
            print("No Unity installs discovered.")
            print(f"Hint: try {_unity_root_hint()}")
            return 1
        for install in payload["installs"]:
            print(f"{install['version']}: {install['install_root']}")
            print(f"  editor: {install['editor_path'] or 'missing'}")
            print(f"  source: {install['source']}")
            print(f"  version_kind: {install.get('version_kind') or unity_env.version_kind(install['version'])}")
        return 0
    return 0 if payload["installs"] else 1


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.vendor, args.unity_version, args.plugin_root)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    payload = build_payload(
        vendor=args.vendor,
        version=args.unity_version,
        plugin_root_arg=args.plugin_root,
        project_dir_arg=args.project_dir,
        json_out_arg=args.json_out,
        md_out_arg=args.md_out,
        clean_project=args.clean_project,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"pass", "dry-run"} else 2


def command_prepare_source(args: argparse.Namespace) -> int:
    payload = prepare_source_checkout(
        vendor=args.vendor,
        plugin_root_arg=args.plugin_root,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"ok", "dry-run"} else 2


def command_handoff(args: argparse.Namespace) -> int:
    payload = handoff_payload(
        vendor=args.vendor,
        version=args.unity_version,
        plugin_root_arg=args.plugin_root,
        project_dir_arg=args.project_dir,
        build_json_out_arg=args.build_json_out,
        build_md_out_arg=args.build_md_out,
        clean_project=args.clean_project,
        dry_run=args.dry_run,
    )
    json_out, md_out = _default_handoff_paths(args.vendor, args.unity_version)
    if args.json_out:
        json_out = Path(args.json_out).expanduser().resolve()
    if args.md_out:
        md_out = Path(args.md_out).expanduser().resolve()
    payload["handoff_json"] = str(json_out)
    payload["handoff_markdown"] = str(md_out)
    write_handoff(payload, json_out, md_out)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "ready" else 2


def command_full(args: argparse.Namespace) -> int:
    doctor_code = command_doctor(
        argparse.Namespace(
            vendor=args.vendor,
            plugin_root=args.plugin_root,
            unity_version=args.unity_version,
            format="text",
        )
    )
    if doctor_code != 0:
        return doctor_code
    return command_build(args)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "build":
        return command_build(args)
    if args.command == "prepare-source":
        return command_prepare_source(args)
    if args.command == "handoff":
        return command_handoff(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
