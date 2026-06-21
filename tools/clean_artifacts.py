#!/usr/bin/env python3
"""Report or remove local FastDIS build products.

Default mode is a dry run so this is safe for junior operators. Use
``--apply`` to delete the reported paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from artifacts import BUILD_ROOT, LEGACY_ARTIFACT_DIRS, ROOT, rel


def collect_cache_dirs(root: Path) -> list[Path]:
    names = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
    found: list[Path] = []
    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.is_dir() and path.name in names:
            found.append(path)
    return found


def collect_windows_mangled_dirs(root: Path) -> list[Path]:
    return [path for path in root.iterdir() if path.is_dir() and ":\\" in path.name]


def collect_paths(*, include_caches: bool, include_legacy: bool, include_build: bool) -> list[Path]:
    paths: list[Path] = []
    if include_build and BUILD_ROOT.exists():
        paths.append(BUILD_ROOT)
    if include_legacy:
        paths.extend(path for path in LEGACY_ARTIFACT_DIRS if path.exists())
        paths.extend(collect_windows_mangled_dirs(ROOT))
    if include_caches:
        paths.extend(collect_cache_dirs(ROOT))
    sorted_paths = sorted(set(paths), key=lambda path: (len(path.parts), str(path)))
    compact: list[Path] = []
    for path in sorted_paths:
        if any(path != parent and path.is_relative_to(parent) for parent in compact):
            continue
        compact.append(path)
    return compact


def remove_path(path: Path) -> dict[str, object]:
    row: dict[str, object] = {"path": rel(path), "removed": False}
    try:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        row["removed"] = True
    except OSError as exc:
        row["error"] = str(exc)
    return row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Delete paths instead of only reporting them")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--keep-build", action="store_true", help="Do not remove the build/ artifact root")
    parser.add_argument("--keep-legacy", action="store_true", help="Do not remove legacy root artifact folders")
    parser.add_argument("--keep-caches", action="store_true", help="Do not remove Python/test cache folders")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = collect_paths(
        include_caches=not args.keep_caches,
        include_legacy=not args.keep_legacy,
        include_build=not args.keep_build,
    )
    report: dict[str, object] = {
        "schema": "fastdis.clean_artifacts.v1",
        "mode": "apply" if args.apply else "dry-run",
        "count": len(paths),
        "paths": [rel(path) for path in paths],
    }
    if args.apply:
        report["results"] = [remove_path(path) for path in paths]

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"clean artifacts: {report['mode']}")
        if not paths:
            print("no local artifacts found")
        for path in paths:
            print(f"- {rel(path)}")
        if not args.apply:
            print("\nRun with --apply to delete these paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
