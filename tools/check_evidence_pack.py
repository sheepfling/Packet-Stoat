#!/usr/bin/env python3
"""Verify a generated FastDIS evidence pack manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from artifacts import ROOT


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(path_value: object) -> Path:
    path = Path(str(path_value))
    if path.is_absolute():
        return path
    return ROOT / path


def _check_rows(rows: list[Mapping[str, Any]], *, default_required: bool) -> list[str]:
    errors: list[str] = []
    for row in rows:
        path = _resolve(row.get("path", ""))
        required = bool(row.get("required", default_required))
        expected_hash = row.get("sha256")
        if not path.exists():
            if required:
                errors.append(f"missing required file: {path}")
            continue
        if expected_hash and path.is_file() and _sha256(path) != expected_hash:
            errors.append(f"hash mismatch: {path}")
    return errors


def check(manifest_path: Path) -> tuple[bool, list[str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "fastdis.evidence_pack.v1":
        return False, ["unexpected manifest schema"]
    artifacts = manifest.get("artifacts", [])
    sources = manifest.get("sources", [])
    if not isinstance(artifacts, list) or not isinstance(sources, list):
        return False, ["manifest artifacts/sources must be arrays"]
    artifact_rows = [row for row in artifacts if isinstance(row, Mapping)]
    source_rows = [row for row in sources if isinstance(row, Mapping)]
    errors = _check_rows(artifact_rows, default_required=True)
    errors.extend(_check_rows(source_rows, default_required=True))
    if manifest.get("status") != "pass":
        errors.append(f"manifest status is {manifest.get('status')!r}")
    return not errors, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)

    ok, errors = check(args.manifest)
    if ok:
        print(f"evidence pack verified: {args.manifest}")
        return 0
    for error in errors:
        print(f"error: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
