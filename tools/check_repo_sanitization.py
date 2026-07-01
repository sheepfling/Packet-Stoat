#!/usr/bin/env python3
"""Fail when tracked files contain generated evidence or host-local receipts."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DISALLOWED_TRACKED_PREFIXES = (
    "artifacts/",
    "verification_reports/",
    "benchmark_reports/",
    "benchmark_results/",
    "release_artifacts/",
    "dist/",
)


def git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def find_violations(paths: list[str]) -> list[str]:
    return [path for path in sorted(paths) if any(path.startswith(prefix) for prefix in DISALLOWED_TRACKED_PREFIXES)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="Only print violations when the guard fails")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    violations = find_violations(git_tracked_files())
    if violations:
        print("Tracked generated outputs are not allowed. Move local evidence into ignored artifact roots or export/import host bundles instead:")
        for path in violations:
            print(f"- {path}")
        return 1
    if not args.quiet:
        print("Repo sanitization check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
