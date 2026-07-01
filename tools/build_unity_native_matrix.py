#!/usr/bin/env python3
"""Build and stage Unity native plug-in payloads for macOS, Windows, and Linux."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from artifacts import CMAKE_HOST, CMAKE_LINUX_X86_64, CMAKE_MINGW_WIN64, REPORTS_DIR
from build_windows_dll import resolve_rc_tool
from linux_native_build import (
    DEFAULT_IMAGE as SHARED_DEFAULT_LINUX_IMAGE,
    DEFAULT_TOOLCHAIN as SHARED_DEFAULT_LINUX_TOOLCHAIN,
    clear_if_incompatible_cmake_cache as shared_clear_if_incompatible_cmake_cache,
    build_direct as shared_build_linux_direct,
    build_docker as shared_build_linux_docker,
    direct_backend_probe as linux_direct_backend_probe,
    docker_backend_probe,
    latest_linux_shared_library as shared_latest_linux_shared_library,
    path_is_file as shared_path_is_file,
    remove_if_present as shared_remove_if_present,
    resolve_backend as resolve_linux_backend,
)
import stage_unity_native


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPORTS_DIR
DEFAULT_LINUX_IMAGE = SHARED_DEFAULT_LINUX_IMAGE
DEFAULT_LINUX_TOOLCHAIN = SHARED_DEFAULT_LINUX_TOOLCHAIN


def run(cmd: list[str], *, required: bool = True) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, check=False)
    if required and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def tool_status(name: str) -> dict[str, object]:
    path = shutil.which(name)
    return {"tool": name, "path": path, "available": path is not None}


_path_is_file = shared_path_is_file
_latest_linux_shared_library = shared_latest_linux_shared_library
_remove_if_present = shared_remove_if_present
_clear_if_incompatible_cmake_cache = shared_clear_if_incompatible_cmake_cache


def _materialize_linux_alias(build_dir: Path) -> Path:
    lib = _latest_linux_shared_library(build_dir)
    if lib is None:
        raise SystemExit("Linux build completed but libfastdis.so was not found")
    alias = build_dir / "libfastdis.so"
    if alias != lib or not _path_is_file(alias):
        _remove_if_present(alias)
        shutil.copy2(lib, alias)
    return alias


def doctor_payload() -> dict[str, object]:
    linux_direct = linux_direct_backend_probe(DEFAULT_LINUX_TOOLCHAIN)
    linux_docker = docker_backend_probe()
    mingw_windres = resolve_rc_tool("x86_64-w64-mingw32")
    tools = {
        "cmake": tool_status("cmake"),
        "docker": tool_status("docker"),
        "zig": tool_status("zig"),
        "mingw_gcc": tool_status("x86_64-w64-mingw32-gcc"),
        "mingw_gxx": tool_status("x86_64-w64-mingw32-g++"),
        "mingw_windres": {"tool": "x86_64-w64-mingw32-windres or windres", "path": mingw_windres, "available": mingw_windres is not None},
    }
    return {
        "status": "ok" if tools["cmake"]["available"] else "needs-attention",
        "targets": {
            "macos": {"available": tools["cmake"]["available"], "method": "host CMake"},
            "windows": {
                "available": all(tools[name]["available"] for name in ("cmake", "mingw_gcc", "mingw_gxx", "mingw_windres")),
                "method": "MinGW-w64 cross compile",
            },
            "linux": {
                "available": bool(linux_direct["available"] or linux_docker["available"]),
                "method": "direct CMake toolchain or Docker linux/amd64 CMake build",
                "backends": {
                    "direct": linux_direct,
                    "docker": linux_docker,
                },
            },
        },
        "tools": tools,
    }


def build_macos(config: str) -> Path:
    build_dir = CMAKE_HOST
    run(
        [
            sys.executable,
            "tools/build_native.py",
            "--build-dir",
            str(build_dir),
            "--config",
            config,
        ]
    )
    lib = build_dir / "libfastdis.dylib"
    if not lib.is_file():
        matches = sorted(build_dir.rglob("libfastdis.dylib"))
        if not matches:
            raise SystemExit("macOS build completed but libfastdis.dylib was not found")
        lib = matches[-1]
    return lib


def build_windows(config: str, mingw_prefix: str) -> Path:
    build_dir = CMAKE_MINGW_WIN64
    run(
        [
            sys.executable,
            "tools/build_windows_dll.py",
            "--build-dir",
            str(build_dir),
            "--config",
            config,
            "--mingw-prefix",
            mingw_prefix,
        ]
    )
    matches = sorted(build_dir.rglob("fastdis.dll")) + sorted(build_dir.rglob("libfastdis.dll"))
    if not matches:
        raise SystemExit("Windows build completed but fastdis.dll was not found")
    return matches[-1]


def build_linux_docker(config: str, image: str) -> Path:
    return shared_build_linux_docker(
        build_dir=CMAKE_LINUX_X86_64,
        config=config,
        image=image,
        clean=False,
        target="fastdis_shared",
        root=ROOT,
        install_packages="cmake g++ make ninja-build ca-certificates",
        run_fn=lambda cmd: run(cmd),
        clear_cache_fn=_clear_if_incompatible_cmake_cache,
        materialize_alias_fn=_materialize_linux_alias,
    )


def build_linux_direct(config: str, toolchain_file: Path, generator: str | None) -> Path:
    return shared_build_linux_direct(
        build_dir=CMAKE_LINUX_X86_64,
        config=config,
        toolchain_file=toolchain_file,
        generator=generator,
        clean=False,
        target="fastdis_shared",
        root=ROOT,
        run_fn=lambda cmd: run(cmd),
        probe_fn=linux_direct_backend_probe,
        clear_cache_fn=_clear_if_incompatible_cmake_cache,
        materialize_alias_fn=_materialize_linux_alias,
    )


def stage_targets(targets: list[str], out_dir: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for target in targets:
        native_build = {
            "macos": CMAKE_HOST,
            "windows": CMAKE_MINGW_WIN64,
            "linux": CMAKE_LINUX_X86_64,
        }[target]
        reports.append(stage_unity_native.stage(target, stage_unity_native.DEFAULT_PACKAGE, native_build, out_dir))
    return reports


def build_targets(args: argparse.Namespace) -> dict[str, object]:
    results: dict[str, object] = {"status": "pass", "targets": {}}
    built: list[str] = []
    for target in args.targets:
        try:
            if target == "macos":
                artifact = build_macos(args.config)
            elif target == "windows":
                artifact = build_windows(args.config, args.mingw_prefix)
            elif target == "linux":
                linux_backend = resolve_linux_backend(args.linux_backend, Path(args.linux_toolchain_file))
                if linux_backend == "direct":
                    artifact = build_linux_direct(args.config, Path(args.linux_toolchain_file), args.linux_generator)
                else:
                    artifact = build_linux_docker(args.config, args.linux_image)
            else:
                raise ValueError(f"unknown target: {target}")
        except SystemExit as exc:
            results["status"] = "fail"
            results["targets"][target] = {"status": "fail", "code": exc.code}
            if not args.keep_going:
                raise
            continue
        built.append(target)
        results["targets"][target] = {"status": "pass", "artifact": str(artifact)}
    if built:
        results["staged"] = stage_targets(built, Path(args.out_dir))
    return results


def render_report(results: dict[str, object]) -> str:
    lines = [
        "# Unity Native Matrix",
        "",
        f"- status: `{results['status']}`",
        "",
        "## Targets",
        "",
    ]
    targets = results.get("targets", {})
    if isinstance(targets, dict):
        for target in ("macos", "windows", "linux"):
            target_result = targets.get(target, {})
            if not isinstance(target_result, dict):
                target_result = {}
            artifact = str(target_result.get("artifact") or target_result.get("code") or "missing")
            lines.append(f"- `{target}` `{target_result.get('status', 'missing')}`: {artifact}")
    staged = results.get("staged", [])
    lines.extend(["", "## Staged", ""])
    if isinstance(staged, list) and staged:
        for row in staged:
            if isinstance(row, dict):
                lines.append(f"- `{row.get('platform', 'unknown')}` -> `{row.get('native_library', 'unknown')}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_report(results: dict[str, object], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "unity_native_matrix.json"
    md_path = out_dir / "unity_native_matrix.md"
    json_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_report(results), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Show local cross-build readiness")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    build = subparsers.add_parser("build", help="Build and stage selected Unity native targets")
    build.add_argument("--targets", nargs="+", choices=("macos", "windows", "linux"), default=["macos", "windows", "linux"])
    build.add_argument("--config", default="Release")
    build.add_argument("--mingw-prefix", default="x86_64-w64-mingw32")
    build.add_argument("--linux-image", default=DEFAULT_LINUX_IMAGE)
    build.add_argument("--linux-backend", choices=("auto", "direct", "docker"), default="auto")
    build.add_argument("--linux-toolchain-file", default=str(DEFAULT_LINUX_TOOLCHAIN))
    build.add_argument("--linux-generator", help="Optional explicit CMake generator for the direct Linux backend")
    build.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    build.add_argument("--keep-going", action="store_true", help="Continue building other targets after a target failure")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "doctor":
        payload = doctor_payload()
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print("Unity native matrix doctor")
            print(f"status: {payload['status']}")
            for name, target in payload["targets"].items():
                print(f"{name}: {'ok' if target['available'] else 'missing'} ({target['method']})")
                if name == "linux":
                    for backend_name, backend in target.get("backends", {}).items():
                        print(f"  - {backend_name}: {'ok' if backend['available'] else 'missing'} ({backend['detail']})")
            print("tools:")
            for tool in payload["tools"].values():
                print(f"  - {tool['tool']}: {tool['path'] or 'missing'}")
        return 0 if payload["status"] == "ok" else 2
    if args.command == "build":
        results = build_targets(args)
        write_report(results, Path(args.out_dir))
        print(json.dumps(results, indent=2))
        return 0 if results["status"] == "pass" else 1
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
