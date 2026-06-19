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
    "unity": ROOT / "examples" / "unity" / "FastDisOrientationVerification" / "Assets" / "StreamingAssets" / "orientation_engine_cases.json",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def checksum_path_for(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".sha256")


def _canonical_json_text(path: Path) -> str:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(parsed, indent=2) + "\n"


def write_fixture_copy(destination: Path, source: Path = SOURCE_FIXTURE) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = _canonical_json_text(source)
    parsed = json.loads(text)
    destination.write_text(text, encoding="utf-8")
    checksum = file_sha256(destination)
    checksum_path = checksum_path_for(destination)
    checksum_path.write_text(f"{checksum}  {destination.name}\n", encoding="utf-8")
    return {
        "destination": str(destination),
        "sha256": checksum,
        "cases": len(parsed.get("cases", [])),
    }


def verify_fixture_copy(destination: Path, source: Path = SOURCE_FIXTURE) -> dict[str, object]:
    if not destination.is_file():
        raise FileNotFoundError(f"Missing staged orientation fixture: {destination}")
    checksum_path = checksum_path_for(destination)
    if not checksum_path.is_file():
        raise FileNotFoundError(f"Missing staged orientation fixture checksum: {checksum_path}")

    source_text = _canonical_json_text(source)
    dest_text = _canonical_json_text(destination)
    if dest_text != source_text:
        raise ValueError(
            f"Staged orientation fixture drifted from canonical source: {destination} != {source}"
        )

    actual_checksum = file_sha256(destination)
    checksum_record = checksum_path.read_text(encoding="utf-8").strip()
    expected_record = f"{actual_checksum}  {destination.name}"
    if checksum_record != expected_record:
        raise ValueError(
            "Staged orientation fixture checksum mismatch: "
            f"expected '{expected_record}', found '{checksum_record}'"
        )

    parsed = json.loads(dest_text)
    return {
        "destination": str(destination),
        "sha256": actual_checksum,
        "cases": len(parsed.get("cases", [])),
    }


def sync_all() -> list[dict[str, object]]:
    return [write_fixture_copy(path) for path in DESTINATIONS.values()]


def verify_all() -> list[dict[str, object]]:
    return [verify_fixture_copy(path) for path in DESTINATIONS.values()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=("all", "godot", "unreal", "unity"),
        default="all",
        help="Which harness fixture copy to refresh.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify staged copies and checksums instead of rewriting them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify:
        if args.target == "all":
            results = verify_all()
        else:
            results = [verify_fixture_copy(DESTINATIONS[args.target])]
    else:
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
