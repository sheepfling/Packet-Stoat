#!/usr/bin/env python3
"""Stage shared orientation fixtures into engine harness projects."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FIXTURE = ROOT / "tests" / "data" / "orientation_engine_cases.json"
DESTINATIONS = {
    "godot": ROOT / "examples" / "godot" / "fastdis_orientation_verification" / "tests" / "orientation_engine_cases.json",
    "unreal": ROOT / "examples" / "unreal" / "FastDisOrientationVerification" / "Tests" / "orientation_engine_cases.json",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_fixture_copy(destination: Path, source: Path = SOURCE_FIXTURE) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8")
    parsed = json.loads(text)
    destination.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
    checksum = file_sha256(destination)
    checksum_path = destination.with_suffix(destination.suffix + ".sha256")
    checksum_path.write_text(f"{checksum}  {destination.name}\n", encoding="utf-8")
    return {
        "destination": str(destination),
        "sha256": checksum,
        "cases": len(parsed.get("cases", [])),
    }


def sync_all() -> list[dict[str, object]]:
    return [write_fixture_copy(path) for path in DESTINATIONS.values()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=("all", "godot", "unreal"),
        default="all",
        help="Which harness fixture copy to refresh.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.target == "all":
        results = sync_all()
    else:
        results = [write_fixture_copy(DESTINATIONS[args.target])]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"{result['destination']}: sha256={result['sha256']} cases={result['cases']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
