#!/usr/bin/env python3
"""Stage FastDIS native libraries into the Unity UPM package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "integrations" / "unity" / "com.sheepfling.fastdis"
DEFAULT_NATIVE_BUILD = ROOT / "build"
DEFAULT_OUT_DIR = ROOT / "build" / "reports"


PLATFORM_LAYOUT = {
    "macos": {
        "source_names": ("libfastdis.dylib",),
        "target": Path("Runtime/Plugins/macOS/libfastdis.dylib"),
        "guid": "7b8f9d8f9d6a4a16a00fe1f6bda10001",
    },
    "windows": {
        "source_names": ("fastdis.dll", "libfastdis.dll"),
        "target": Path("Runtime/Plugins/Windows/x86_64/fastdis.dll"),
        "guid": "7b8f9d8f9d6a4a16a00fe1f6bda10003",
    },
    "linux": {
        "source_names": ("libfastdis.so",),
        "target": Path("Runtime/Plugins/Linux/x86_64/libfastdis.so"),
        "guid": "7b8f9d8f9d6a4a16a00fe1f6bda10002",
    },
}


def host_platform() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_native_library(build_dir: Path, platform_name: str) -> Path | None:
    layout = PLATFORM_LAYOUT[platform_name]
    for name in layout["source_names"]:
        direct = build_dir / name
        if direct.is_file():
            return direct
        matches = sorted(build_dir.rglob(name))
        if matches:
            return matches[0]
    return None


def unity_meta_for(target: Path, guid: str) -> str:
    return (
        "fileFormatVersion: 2\n"
        f"guid: {guid}\n"
        "PluginImporter:\n"
        "  externalObjects: {}\n"
        "  serializedVersion: 2\n"
        "  iconMap: {}\n"
        "  executionOrder: {}\n"
        "  defineConstraints: []\n"
        "  isPreloaded: 0\n"
        "  isOverridable: 0\n"
        "  isExplicitlyReferenced: 0\n"
        "  validateReferences: 1\n"
        "  platformData: []\n"
        "  userData: \n"
        "  assetBundleName: \n"
        "  assetBundleVariant: \n"
    )


def stage(platform_name: str, package: Path, native_build: Path, out_dir: Path, *, check: bool = False) -> dict[str, object]:
    if platform_name not in PLATFORM_LAYOUT:
        raise ValueError(f"unsupported platform: {platform_name}")

    source = find_native_library(native_build, platform_name)
    target = package / PLATFORM_LAYOUT[platform_name]["target"]
    meta = target.with_name(target.name + ".meta")
    report: dict[str, object] = {
        "platform": platform_name,
        "package": str(package),
        "native_build": str(native_build),
        "native_library": str(target.relative_to(package)),
        "source": str(source) if source else None,
        "exists": False,
        "size_bytes": 0,
        "sha256": None,
        "status": "fail",
    }
    if source is None:
        report["error"] = f"could not find native library for {platform_name} under {native_build}"
    else:
        report["exists"] = True
        report["size_bytes"] = source.stat().st_size
        report["sha256"] = sha256(source)
        report["status"] = "pass"
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            expected_meta = unity_meta_for(target, str(PLATFORM_LAYOUT[platform_name]["guid"]))
            if not meta.exists() or "fastdisnativepluginplaceholder" in meta.read_text(encoding="utf-8", errors="replace"):
                meta.write_text(expected_meta, encoding="utf-8")

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"unity_native_stage_{platform_name}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"report: {report_path}")
    if report["status"] == "pass":
        print(f"staged {platform_name}: {target}" if not check else f"found {platform_name}: {source}")
    else:
        print(report["error"])
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--native-build", type=Path, default=DEFAULT_NATIVE_BUILD)
    parser.add_argument("--platform", choices=sorted(PLATFORM_LAYOUT), default=host_platform())
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--check", action="store_true", help="Only check that a native library can be found.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = stage(args.platform, args.package, args.native_build, args.out_dir, check=args.check)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
