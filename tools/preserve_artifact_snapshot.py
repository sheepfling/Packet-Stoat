#!/usr/bin/env python3
"""Copy expensive proof outputs into a local preserved artifact snapshot."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

from artifacts import PRESERVED_ARTIFACTS_DIR, ROOT, rel


PATH_HINTS = (
    "path",
    "paths",
    "log",
    "json",
    "markdown",
    "artifact",
    "artifacts",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip()).strip("-")
    return cleaned or "snapshot"


def stable_snapshot_dir(root: Path, lane: str, label: str, timestamp: str | None = None) -> Path:
    stamp = timestamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return root / slug(lane) / f"{stamp}_{slug(label)}"


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def should_collect_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in PATH_HINTS)


def collect_paths_from_payload(value: Any, *, parent_key: str = "") -> list[Path]:
    paths: list[Path] = []
    if isinstance(value, dict):
        for key, child in value.items():
            paths.extend(collect_paths_from_payload(child, parent_key=str(key)))
        return paths
    if isinstance(value, list):
        for child in value:
            paths.extend(collect_paths_from_payload(child, parent_key=parent_key))
        return paths
    if isinstance(value, str) and should_collect_key(parent_key):
        paths.append(resolve_path(value))
    return paths


def dedupe_existing(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def snapshot_relative_path(path: Path) -> Path:
    try:
        return Path("files") / path.relative_to(ROOT)
    except ValueError:
        external_id = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
        return Path("files") / "external" / external_id / path.name


def preserve_files(paths: list[Path], *, out_dir: Path, lane: str, label: str) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    for source in dedupe_existing(paths):
        relative_dest = snapshot_relative_path(source)
        dest = out_dir / relative_dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        rows.append(
            {
                "source": rel(source),
                "snapshot_path": relative_dest.as_posix(),
                "bytes": source.stat().st_size,
                "sha256": sha256_file(source),
            }
        )
    manifest = {
        "schema": "packet_stoat.preserved_artifact_snapshot.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "lane": lane,
        "label": label,
        "snapshot_dir": str(out_dir),
        "artifact_count": len(rows),
        "artifacts": rows,
    }
    manifest_path = out_dir / "SNAPSHOT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_snapshot_from_report(report: Path, *, out_root: Path, lane: str, label: str) -> dict[str, Any]:
    payload = json.loads(report.read_text(encoding="utf-8"))
    paths = [report.resolve(), *collect_paths_from_payload(payload)]
    out_dir = stable_snapshot_dir(out_root.resolve(), lane, label)
    return preserve_files(paths, out_dir=out_dir, lane=lane, label=label)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True, help="JSON report to scan for logs, handoffs, and artifact paths")
    parser.add_argument("--lane", required=True, help="Snapshot lane, for example cesium-godot-linux-docker")
    parser.add_argument("--label", default="manual", help="Human label included in the snapshot directory name")
    parser.add_argument("--out-root", type=Path, default=PRESERVED_ARTIFACTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_snapshot_from_report(args.report.expanduser().resolve(), out_root=args.out_root, lane=args.lane, label=args.label)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
