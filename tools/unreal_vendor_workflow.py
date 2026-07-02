#!/usr/bin/env python3
"""Operator-facing Unreal vendor-plugin workflow wrapper."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import build_unreal_plugin
import load_local_env
import unreal_env
import workspace_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "unreal_vendor_plugin"
MANIFEST = workspace_manifest.load_manifest()
UNREAL_SURFACE = workspace_manifest.surface_spec("unreal", MANIFEST)
DEFAULT_SUPPORTED_VERSIONS = [
    version["version"] for version in workspace_manifest.surface_versions(UNREAL_SURFACE, MANIFEST)
]


def preferred_unreal_version() -> str:
    return workspace_manifest.surface_preferred_version(UNREAL_SURFACE, MANIFEST)


def supported_unreal_versions_label() -> str:
    return " or ".join(DEFAULT_SUPPORTED_VERSIONS)


def run_step(cmd: list[str]) -> int:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, cwd=ROOT, env=unreal_env.build_env())
    return completed.returncode


def run_step_in_dir(cmd: list[str], cwd: Path) -> int:
    print("+", " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, cwd=cwd, env=unreal_env.build_env())
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
            f"FASTDIS_{env_token}_UNREAL_PLUGIN_ROOT",
            "FASTDIS_UNREAL_VENDOR_PLUGIN_ROOT",
        ]
    )
    return None if candidate is None else candidate.resolve()


def resolve_uplugin_path(vendor: str, plugin_root: Path | None, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute() and plugin_root is not None:
            candidate = plugin_root / candidate
        return candidate.resolve()

    env_token = vendor_env_token(vendor)
    env_candidate = _resolve_env_path(
        [
            f"FASTDIS_{env_token}_UPLUGIN",
            "FASTDIS_UNREAL_VENDOR_UPLUGIN",
        ]
    )
    if env_candidate is not None:
        if not env_candidate.is_absolute() and plugin_root is not None:
            env_candidate = plugin_root / env_candidate
        return env_candidate.resolve()

    if plugin_root is None or not plugin_root.is_dir():
        return None
    matches = sorted(plugin_root.glob("*.uplugin"))
    if not matches:
        return None
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise SystemExit(
            f"Multiple .uplugin files found under {plugin_root}: {names}. "
            "Pass --uplugin to select one explicitly."
        )
    return matches[0].resolve()


def install_for_version(version: str | None) -> unreal_env.UnrealInstall | None:
    installs = unreal_env.discover_installs()
    if version is not None:
        for install in installs:
            if unreal_env.version_matches(version, install.version):
                return install
        return None
    if installs:
        return installs[-1]
    return None


def _version_label(version: str | None) -> str:
    return version or "default"


def plugin_uses_source_checkout(plugin_root: Path | None) -> bool:
    if plugin_root is None:
        return False
    return (plugin_root / "extern" / "CMakeLists.txt").is_file()


def source_third_party_include_dir(plugin_root: Path) -> Path:
    return plugin_root / "Source" / "ThirdParty" / "include"


def source_third_party_lib_dir(plugin_root: Path) -> Path:
    return plugin_root / "Source" / "ThirdParty" / "lib"


def source_checkout_prepared(plugin_root: Path | None) -> bool:
    if plugin_root is None:
        return False
    include_dir = source_third_party_include_dir(plugin_root)
    lib_dir = source_third_party_lib_dir(plugin_root)
    return include_dir.is_dir() and any(lib_dir.glob("*"))


def doctor_payload(
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
) -> dict[str, object]:
    install = install_for_version(version)
    resolved_plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    resolved_uplugin = resolve_uplugin_path(vendor, resolved_plugin_root, uplugin_arg)

    payload: dict[str, object] = {
        "vendor": vendor_slug(vendor),
        "requested_version": version,
        "resolved_version": install.version if install is not None else None,
        "status": "ok",
        "plugin_root": str(resolved_plugin_root) if resolved_plugin_root is not None else None,
        "uplugin": str(resolved_uplugin) if resolved_uplugin is not None else None,
        "install": install.to_dict() if install is not None else None,
        "checks": [],
        "next_steps": [],
        "source_checkout": False,
        "source_checkout_prepared": None,
    }

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if resolved_plugin_root is None:
        add_check("plugin_root", "fail", f"no plugin root configured for vendor {vendor_slug(vendor)}")
    elif not resolved_plugin_root.exists():
        add_check("plugin_root", "fail", f"plugin root does not exist: {resolved_plugin_root}")
    elif not resolved_plugin_root.is_dir():
        add_check("plugin_root", "fail", f"plugin root is not a directory: {resolved_plugin_root}")
    else:
        add_check("plugin_root", "ok", str(resolved_plugin_root))

    if resolved_uplugin is None:
        add_check("plugin_descriptor", "fail", f"no .uplugin resolved for vendor {vendor_slug(vendor)}")
    elif not resolved_uplugin.exists():
        add_check("plugin_descriptor", "fail", f"plugin descriptor does not exist: {resolved_uplugin}")
    else:
        add_check("plugin_descriptor", "ok", str(resolved_uplugin))

    uses_source_checkout = plugin_uses_source_checkout(resolved_plugin_root)
    payload["source_checkout"] = uses_source_checkout
    if uses_source_checkout and resolved_plugin_root is not None:
        prepared = source_checkout_prepared(resolved_plugin_root)
        payload["source_checkout_prepared"] = prepared
        include_dir = source_third_party_include_dir(resolved_plugin_root)
        lib_dir = source_third_party_lib_dir(resolved_plugin_root)
        add_check("source_checkout", "ok", "extern/CMakeLists.txt present")
        add_check(
            "third_party_include",
            "ok" if include_dir.is_dir() else "fail",
            str(include_dir),
        )
        add_check(
            "third_party_lib",
            "ok" if lib_dir.is_dir() and any(lib_dir.glob("*")) else "fail",
            str(lib_dir),
        )
    elif resolved_plugin_root is not None:
        payload["source_checkout_prepared"] = None
        add_check("source_checkout", "ok", "plugin root does not expose the cesium-unreal extern source layout")

    if install is None:
        add_check("engine install", "fail", f"no Unreal install discovered for {_version_label(version)}")
    else:
        add_check("engine root", "ok", install.install_root)
        add_check("editor", "ok" if install.editor_path is not None else "fail", install.editor_path or "missing editor executable")
        add_check("automation tool", "ok" if install.uat_path is not None else "fail", install.uat_path or "missing RunUAT")
        add_check("build tool", "ok" if install.ubt_path is not None else "fail", install.ubt_path or "missing UnrealBuildTool.dll")
        add_check("bundled dotnet", "ok" if install.dotnet_path is not None else "fail", install.dotnet_path or "missing bundled dotnet")
        permissions = unreal_env.permission_probe(install)
        payload["permissions"] = permissions
        for check in permissions["checks"]:
            add_check(f"permission:{check['name']}", str(check["status"]), str(check["detail"]))

    payload["checks"] = checks
    failures = [check for check in checks if check["status"] == "fail"]
    payload["status"] = "ok" if not failures else "needs-attention"

    if failures:
        payload["next_steps"] = [
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT to the local plugin checkout root, or pass --plugin-root.",
            "If the plugin descriptor is not at the plugin root, pass --uplugin with the .uplugin filename or path.",
            "Set FASTDIS_UNREAL_ENGINE_DIR or FASTDIS_UNREAL_ENGINE_DIR_5_8 style variables so Unreal discovery can find a supported install.",
            "If this is a raw cesium-unreal source checkout, run python tools/unreal_vendor_workflow.py prepare-source --vendor cesium --engine-version <version> before BuildPlugin.",
            "Run `python tools/list_unreal_installs.py` to inspect available Unreal versions on this machine.",
        ]
    else:
        suggested_version = install.version or preferred_unreal_version()
        payload["next_steps"] = [
            f"Package the preferred lane: python tools/unreal_vendor_workflow.py build --vendor {vendor_slug(vendor)} --engine-version {suggested_version}",
            f"Run the cross-version matrix: python tools/unreal_vendor_workflow.py matrix --vendor {vendor_slug(vendor)} --versions {' '.join(DEFAULT_SUPPORTED_VERSIONS)}",
        ]
    return payload


def print_doctor(payload: dict[str, object]) -> None:
    requested = payload["requested_version"] or "default"
    resolved = payload["resolved_version"] or "none"
    print(f"Unreal vendor doctor for {payload['vendor']}")
    print(f"status: {payload['status']}")
    print(f"requested_version: {requested}")
    print(f"resolved_version: {resolved}")
    print(f"plugin_root: {payload['plugin_root'] or 'missing'}")
    print(f"uplugin: {payload['uplugin'] or 'missing'}")
    print(f"source_checkout: {payload['source_checkout']}")
    print(f"source_checkout_prepared: {payload['source_checkout_prepared']}")
    print("checks:")
    for check in payload["checks"]:
        print(f"  - {check['name']}: {check['status']} ({check['detail']})")
    print("next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")


def default_package_dir(vendor: str, descriptor: Path, version: str | None) -> Path:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    return ROOT / "build" / "unreal_vendor_plugins" / vendor_slug(vendor) / version_slug / descriptor.stem


def _target_platforms(raw: str | None) -> list[str]:
    return build_unreal_plugin.parse_target_platforms(raw, build_unreal_plugin.host_platform_name())


def package_plugin(
    *,
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    uplugin_arg: str | None,
    package_dir_arg: str | None,
    target_platforms_arg: str | None,
    clean_package: bool,
    skip_platform_probe: bool,
    dry_run: bool,
) -> dict[str, object]:
    install = install_for_version(version)
    if install is None:
        raise SystemExit(
            "Could not locate an Unreal Engine install. Set --engine-version or a FASTDIS_UNREAL_ENGINE_DIR style variable."
        )

    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    if plugin_root is None:
        raise SystemExit(
            f"Could not resolve plugin root for vendor {vendor_slug(vendor)}. "
            f"Set FASTDIS_{vendor_env_token(vendor)}_PLUGIN_ROOT or pass --plugin-root."
        )
    if not plugin_root.is_dir():
        raise SystemExit(f"Plugin root is not a directory: {plugin_root}")
    if plugin_uses_source_checkout(plugin_root) and not source_checkout_prepared(plugin_root):
        raise SystemExit(
            f"Plugin root {plugin_root} is a raw cesium-unreal source checkout without Source/ThirdParty output. "
            "Run `python tools/unreal_vendor_workflow.py prepare-source --vendor cesium --engine-version <version>` first."
        )

    descriptor = resolve_uplugin_path(vendor, plugin_root, uplugin_arg)
    if descriptor is None or not descriptor.is_file():
        raise SystemExit(
            f"Could not resolve a .uplugin descriptor under {plugin_root}. Pass --uplugin if needed."
        )

    target_platforms = _target_platforms(target_platforms_arg)
    host_platform = build_unreal_plugin.host_platform_name()
    if any(target != host_platform for target in target_platforms):
        raise SystemExit(
            "This workflow is host-oriented. Run it on the target OS or request only the host target platform. "
            f"Host platform is {host_platform}; requested targets were {target_platforms}."
        )

    engine_root = Path(install.install_root)
    package_dir = (
        Path(package_dir_arg).expanduser().resolve()
        if package_dir_arg
        else default_package_dir(vendor, descriptor, install.version or version)
    )
    package_dir_for_uat = build_unreal_plugin.unreal_safe_dir(
        package_dir,
        f"{vendor_slug(vendor)}_{descriptor.stem}_{(install.version or version or preferred_unreal_version()).replace('.', '_')}",
    )

    if not skip_platform_probe:
        build_unreal_plugin.validate_host_platform_or_warn(engine_root, install.version or version)

    build_unreal_plugin.ensure_build_rules_compatibility(engine_root)
    if clean_package and package_dir.exists():
        shutil.rmtree(package_dir)
    if package_dir_for_uat != package_dir and package_dir_for_uat.exists():
        shutil.rmtree(package_dir_for_uat)

    command = [
        str(build_unreal_plugin.uat_path(engine_root)),
        "BuildPlugin",
        f"-Plugin={descriptor}",
        f"-Package={package_dir_for_uat}",
        f"-TargetPlatforms={'+'.join(target_platforms)}",
    ]
    if dry_run:
        print("+", " ".join(command))
    else:
        build_unreal_plugin.run(command)

    packaged_descriptor = package_dir / descriptor.name
    if not dry_run and not packaged_descriptor.is_file():
        raise SystemExit(f"BuildPlugin completed without producing {packaged_descriptor}")

    return {
        "vendor": vendor_slug(vendor),
        "engine_version": install.version or version,
        "plugin_root": str(plugin_root),
        "uplugin": str(descriptor),
        "package_dir": str(package_dir),
        "target_platforms": target_platforms,
        "status": "dry-run" if dry_run else "ok",
    }


def prepare_source_checkout(
    *,
    vendor: str,
    version: str | None,
    plugin_root_arg: str | None,
    clean_build: bool,
    build_type: str,
    dry_run: bool,
) -> dict[str, object]:
    install = install_for_version(version)
    if install is None:
        raise SystemExit(
            "Could not locate an Unreal Engine install. Set --engine-version or a FASTDIS_UNREAL_ENGINE_DIR style variable."
        )
    plugin_root = resolve_plugin_root(vendor, plugin_root_arg)
    if plugin_root is None or not plugin_root.is_dir():
        raise SystemExit(f"Could not resolve plugin root for vendor {vendor_slug(vendor)}.")
    extern_root = plugin_root / "extern"
    if not extern_root.is_dir() or not (extern_root / "CMakeLists.txt").is_file():
        raise SystemExit(f"Plugin root {plugin_root} does not look like a cesium-unreal source checkout.")

    build_dir = extern_root / "build-fastdis"
    if clean_build and build_dir.exists():
        shutil.rmtree(build_dir)

    env = unreal_env.build_env()
    env["UNREAL_ENGINE_ROOT"] = install.install_root
    configure_cmd = ["cmake", "-B", str(build_dir), "-S", str(extern_root), f"-DCMAKE_BUILD_TYPE={build_type}"]
    build_cmd = ["cmake", "--build", str(build_dir), "--target", "install", "--config", build_type]

    if dry_run:
        print("+", " ".join(configure_cmd))
        print("+", " ".join(build_cmd))
    else:
        print("+", " ".join(configure_cmd))
        configured = subprocess.run(configure_cmd, cwd=extern_root, env=env)
        if configured.returncode != 0:
            raise SystemExit("Cesium Unreal source prep configure failed.")
        print("+", " ".join(build_cmd))
        built = subprocess.run(build_cmd, cwd=extern_root, env=env)
        if built.returncode != 0:
            raise SystemExit("Cesium Unreal source prep build/install failed.")

    return {
        "vendor": vendor_slug(vendor),
        "engine_version": install.version or version,
        "plugin_root": str(plugin_root),
        "extern_root": str(extern_root),
        "build_dir": str(build_dir),
        "build_type": build_type,
        "status": "dry-run" if dry_run else ("ok" if source_checkout_prepared(plugin_root) else "needs-attention"),
        "third_party_include": str(source_third_party_include_dir(plugin_root)),
        "third_party_lib": str(source_third_party_lib_dir(plugin_root)),
    }


def _add_common_vendor_args(parser: argparse.ArgumentParser, *, include_engine: bool) -> None:
    parser.add_argument("--vendor", required=True, help="Vendor id, for example cesium")
    if include_engine:
        parser.add_argument("--engine-version", default=preferred_unreal_version())
    parser.add_argument("--plugin-root", help="Vendor plugin root containing the .uplugin")
    parser.add_argument("--uplugin", help="Explicit .uplugin path or filename")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="List detected Unreal installs")
    discover.add_argument("--format", choices=("table", "json"), default="table")

    doctor = subparsers.add_parser("doctor", help="Validate a vendor plugin root against a selected Unreal lane")
    _add_common_vendor_args(doctor, include_engine=False)
    doctor.add_argument("--engine-version", help=f"Versioned Unreal env selector, for example {supported_unreal_versions_label()}")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Package a vendor Unreal plugin with BuildPlugin")
    _add_common_vendor_args(build, include_engine=True)
    build.add_argument("--package-dir", help="Override the BuildPlugin package directory")
    build.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    build.add_argument("--clean-package", action="store_true", help="Delete the package directory before BuildPlugin")
    build.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    build.add_argument("--dry-run", action="store_true")

    prepare = subparsers.add_parser("prepare-source", help="Prepare a cesium-unreal source checkout by installing ThirdParty dependencies")
    _add_common_vendor_args(prepare, include_engine=True)
    prepare.add_argument("--clean-build", action="store_true", help="Delete the source-prep build directory before configuring CMake")
    prepare.add_argument("--build-type", default="Release", choices=("Debug", "Release", "RelWithDebInfo"))
    prepare.add_argument("--dry-run", action="store_true")

    package = subparsers.add_parser("package", help="Alias for build")
    _add_common_vendor_args(package, include_engine=True)
    package.add_argument("--package-dir", help="Override the BuildPlugin package directory")
    package.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    package.add_argument("--clean-package", action="store_true", help="Delete the package directory before BuildPlugin")
    package.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    package.add_argument("--dry-run", action="store_true")

    install_smoke = subparsers.add_parser("install-smoke", help="Install the packaged vendor plugin into a clean scratch project and verify the editor can open it")
    _add_common_vendor_args(install_smoke, include_engine=True)
    install_smoke.add_argument("--package-dir", help="Packaged plugin directory produced by BuildPlugin")
    install_smoke.add_argument("--project-dir", help="Scratch project directory for this install smoke")
    install_smoke.add_argument("--json-out", help="JSON report output path")
    install_smoke.add_argument("--md-out", help="Markdown report output path")
    install_smoke.add_argument("--clean-project", action="store_true")
    install_smoke.add_argument("--dry-run", action="store_true")

    matrix = subparsers.add_parser("matrix", help="Package one vendor plugin across multiple Unreal versions")
    _add_common_vendor_args(matrix, include_engine=False)
    matrix.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS)
    matrix.add_argument("--package-root", help="Override the base output directory for versioned packages")
    matrix.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    matrix.add_argument("--clean-package", action="store_true", help="Delete each versioned package directory before BuildPlugin")
    matrix.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    matrix.add_argument("--dry-run", action="store_true")
    matrix.add_argument("--json-out")
    matrix.add_argument("--md-out")

    full = subparsers.add_parser("full", help="Doctor the vendor plugin, then run the supported-version packaging matrix")
    _add_common_vendor_args(full, include_engine=False)
    full.add_argument("--versions", nargs="+", default=DEFAULT_SUPPORTED_VERSIONS)
    full.add_argument("--package-root", help="Override the base output directory for versioned packages")
    full.add_argument("--target-platforms", help="Unreal BuildPlugin target platforms, for example Mac or Win64")
    full.add_argument("--clean-package", action="store_true", help="Delete each versioned package directory before BuildPlugin")
    full.add_argument("--skip-platform-probe", action="store_true", help="Skip the host compatibility preflight")
    full.add_argument("--dry-run", action="store_true")
    full.add_argument("--json-out")
    full.add_argument("--md-out")

    return parser.parse_args(argv)


def command_discover(args: argparse.Namespace) -> int:
    installs = [install.to_dict() for install in unreal_env.discover_installs()]
    if args.format == "json":
        print(json.dumps(installs, indent=2))
        return 0 if installs else 1
    if not installs:
        print("No Unreal installs discovered.")
        return 1
    for install in installs:
        version = install["version"] or "unknown"
        quirks = ", ".join(install["quirks"]) if install["quirks"] else "none"
        print(f"{version}: {install['install_root']}")
        print(f"  editor: {install['editor_path'] or 'missing'}")
        print(f"  uat:    {install['uat_path'] or 'missing'}")
        print(f"  ubt:    {install['ubt_path'] or 'missing'}")
        print(f"  dotnet: {install['dotnet_path'] or 'missing'}")
        print(f"  source: {install['source']}")
        print(f"  quirks: {quirks}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.vendor, args.engine_version, args.plugin_root, args.uplugin)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print_doctor(payload)
    return 0 if payload["status"] == "ok" else 2


def command_build(args: argparse.Namespace) -> int:
    package_plugin(
        vendor=args.vendor,
        version=args.engine_version,
        plugin_root_arg=args.plugin_root,
        uplugin_arg=args.uplugin,
        package_dir_arg=args.package_dir,
        target_platforms_arg=args.target_platforms,
        clean_package=args.clean_package,
        skip_platform_probe=args.skip_platform_probe,
        dry_run=args.dry_run,
    )
    return 0


def command_prepare_source(args: argparse.Namespace) -> int:
    payload = prepare_source_checkout(
        vendor=args.vendor,
        version=args.engine_version,
        plugin_root_arg=args.plugin_root,
        clean_build=args.clean_build,
        build_type=args.build_type,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"ok", "dry-run"} else 2


def _default_install_project_dir(vendor: str, version: str | None, plugin_name: str) -> Path:
    version_slug = (version or preferred_unreal_version()).replace(".", "_")
    return unreal_env.work_root() / "vendor_install_smoke" / vendor_slug(vendor) / version_slug / plugin_name


def command_install_smoke(args: argparse.Namespace) -> int:
    plugin_root = resolve_plugin_root(args.vendor, args.plugin_root)
    descriptor = resolve_uplugin_path(args.vendor, plugin_root, args.uplugin)
    if descriptor is None:
        raise SystemExit("Could not resolve a .uplugin for install smoke.")
    package_dir = (
        Path(args.package_dir).expanduser().resolve()
        if args.package_dir
        else default_package_dir(args.vendor, descriptor, args.engine_version)
    )
    project_dir = (
        Path(args.project_dir).expanduser().resolve()
        if args.project_dir
        else _default_install_project_dir(args.vendor, args.engine_version, descriptor.stem)
    )
    json_out = (
        Path(args.json_out).expanduser().resolve()
        if args.json_out
        else DEFAULT_REPORT_DIR / f"{vendor_slug(args.vendor)}_{(args.engine_version or preferred_unreal_version()).replace('.', '_')}_install_smoke.json"
    )
    md_out = (
        Path(args.md_out).expanduser().resolve()
        if args.md_out
        else DEFAULT_REPORT_DIR / f"{vendor_slug(args.vendor)}_{(args.engine_version or preferred_unreal_version()).replace('.', '_')}_install_smoke.md"
    )
    cmd = unreal_env.python_command() + [
        "tools/run_unreal_vendor_install_smoke.py",
        "--vendor",
        vendor_slug(args.vendor),
        "--engine-version",
        args.engine_version or preferred_unreal_version(),
        "--package-dir",
        str(package_dir),
        "--project-dir",
        str(project_dir),
        "--json-out",
        str(json_out),
        "--markdown-out",
        str(md_out),
    ]
    if args.clean_project:
        cmd.append("--clean-project")
    if args.dry_run:
        cmd.append("--dry-run")
    return run_step(cmd)


def _matrix_package_dir(package_root: Path | None, vendor: str, version: str, descriptor_name: str) -> Path:
    base = package_root if package_root is not None else (ROOT / "build" / "unreal_vendor_plugins" / vendor_slug(vendor))
    return base / version.replace(".", "_") / descriptor_name


def _report_paths(vendor: str, json_out: str | None, md_out: str | None) -> tuple[Path, Path]:
    base = DEFAULT_REPORT_DIR / vendor_slug(vendor)
    return (
        Path(json_out).expanduser().resolve() if json_out else base.with_name(f"{vendor_slug(vendor)}_matrix.json"),
        Path(md_out).expanduser().resolve() if md_out else base.with_name(f"{vendor_slug(vendor)}_matrix.md"),
    )


def _write_matrix_report(report: dict[str, object], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Unreal Vendor Plugin Matrix",
        "",
        f"- vendor: `{report['vendor']}`",
        f"- overall_status: `{report['overall_status']}`",
        "",
        "| version | status | package_dir | detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["results"]:
        lines.append(
            f"| {row['version']} | {row['status']} | {row.get('package_dir') or ''} | {row.get('detail') or ''} |"
        )
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_matrix(args: argparse.Namespace) -> int:
    resolved_plugin_root = resolve_plugin_root(args.vendor, args.plugin_root)
    resolved_uplugin = resolve_uplugin_path(args.vendor, resolved_plugin_root, args.uplugin)
    descriptor_name = resolved_uplugin.stem if resolved_uplugin is not None else vendor_slug(args.vendor)
    package_root = Path(args.package_root).expanduser().resolve() if args.package_root else None
    json_out, md_out = _report_paths(args.vendor, args.json_out, args.md_out)
    results: list[dict[str, object]] = []

    for version in args.versions:
        package_dir = _matrix_package_dir(package_root, args.vendor, version, descriptor_name)
        try:
            row = package_plugin(
                vendor=args.vendor,
                version=version,
                plugin_root_arg=args.plugin_root,
                uplugin_arg=args.uplugin,
                package_dir_arg=str(package_dir),
                target_platforms_arg=args.target_platforms,
                clean_package=args.clean_package,
                skip_platform_probe=args.skip_platform_probe,
                dry_run=args.dry_run,
            )
            results.append(
                {
                    "version": version,
                    "status": row["status"],
                    "package_dir": row["package_dir"],
                    "detail": "",
                }
            )
            install_cmd = argparse.Namespace(
                vendor=args.vendor,
                engine_version=version,
                plugin_root=args.plugin_root,
                uplugin=args.uplugin,
                package_dir=str(package_dir),
                project_dir=None,
                json_out=None,
                md_out=None,
                clean_project=True,
                dry_run=args.dry_run,
            )
            install_code = command_install_smoke(install_cmd)
            results[-1]["install_smoke_status"] = "ok" if install_code == 0 else "fail"
            if install_code != 0:
                results[-1]["status"] = "fail"
                results[-1]["detail"] = "install smoke failed"
        except (SystemExit, subprocess.CalledProcessError) as exc:
            results.append(
                {
                    "version": version,
                    "status": "fail",
                    "package_dir": str(package_dir),
                    "detail": str(exc),
                }
            )

    overall_status = "ok" if all(row["status"] in {"ok", "dry-run"} for row in results) else "fail"
    report = {
        "schema": "packet_stoat.unreal_vendor_plugin_matrix.v1",
        "vendor": vendor_slug(args.vendor),
        "overall_status": overall_status,
        "results": results,
    }
    _write_matrix_report(report, json_out, md_out)
    return 0 if overall_status == "ok" else 2


def command_full(args: argparse.Namespace) -> int:
    doctor_code = command_doctor(
        argparse.Namespace(
            vendor=args.vendor,
            engine_version=None,
            plugin_root=args.plugin_root,
            uplugin=args.uplugin,
            format="text",
        )
    )
    if doctor_code != 0:
        return doctor_code
    return command_matrix(args)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    if args.command == "discover":
        return command_discover(args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command in {"build", "package"}:
        return command_build(args)
    if args.command == "prepare-source":
        return command_prepare_source(args)
    if args.command == "install-smoke":
        return command_install_smoke(args)
    if args.command == "matrix":
        return command_matrix(args)
    if args.command == "full":
        return command_full(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
