#!/usr/bin/env python3
"""List discovered Unreal Engine installs and quirks."""

from __future__ import annotations

import argparse
import json

import load_local_env
import unreal_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table")
    return parser.parse_args()


def main() -> int:
    load_local_env.load()
    installs = [install.to_dict() for install in unreal_env.discover_installs()]

    if parse_args().format == "json":
        print(json.dumps(installs, indent=2))
        return 0

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
        print(f"  source: {install['source']}")
        print(f"  quirks: {quirks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
