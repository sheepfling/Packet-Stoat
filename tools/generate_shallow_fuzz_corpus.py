#!/usr/bin/env python3
"""Generate shallow fuzz corpus seeds that cover every cataloged DIS 6/7 PDU."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import fastdis  # noqa: E402


DEFAULT_OUT_DIR = ROOT / "generated" / "fuzz_shallow_corpus"
LOCK_DIR = ROOT / "generated" / ".fuzz_shallow_corpus.lock"


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_")


def header_bytes(
    version: int,
    exercise_id: int,
    pdu_type: int,
    protocol_family: int,
    declared_length: int,
    *,
    status: int = 0,
    padding: int = 0,
) -> bytes:
    out = bytearray(12)
    out[0] = version & 0xFF
    out[1] = exercise_id & 0xFF
    out[2] = pdu_type & 0xFF
    out[3] = protocol_family & 0xFF
    out[4:8] = ((version << 24) | (pdu_type << 8) | protocol_family).to_bytes(4, "big", signed=False)
    out[8:10] = declared_length.to_bytes(2, "big", signed=False)
    if version >= fastdis.FASTDIS_PROTOCOL_VERSION_DIS7:
        out[10] = status & 0xFF
        out[11] = padding & 0xFF
    else:
        out[10:12] = padding.to_bytes(2, "big", signed=False)
    return bytes(out)


def seed_map() -> dict[str, bytes]:
    seeds: dict[str, bytes] = {}
    for entry in fastdis.PDU_CATALOG:
        name = f"valid/v{entry.protocol_version}_pdu{entry.pdu_type:03d}_{slugify(entry.name)}.bin"
        seeds[name] = header_bytes(
            entry.protocol_version,
            1,
            entry.pdu_type,
            entry.protocol_family,
            12,
        )

    seeds["malformed/short_packet_11.bin"] = bytes(range(11))
    seeds["malformed/length_too_small_v7.bin"] = header_bytes(7, 1, 1, 1, 11)
    seeds["malformed/declared_length_exceeds_buffer_v7.bin"] = header_bytes(7, 1, 1, 1, 64)
    seeds["malformed/unknown_pdu_v6.bin"] = header_bytes(6, 1, 250, 1, 12)
    seeds["malformed/unknown_pdu_v7.bin"] = header_bytes(7, 1, 250, 13, 12)
    return seeds


def build_manifest(seeds: dict[str, bytes], out_dir: Path) -> dict[str, object]:
    try:
        out_dir_display = str(out_dir.relative_to(ROOT))
    except ValueError:
        out_dir_display = str(out_dir)
    valid = []
    for entry in fastdis.PDU_CATALOG:
        rel = f"valid/v{entry.protocol_version}_pdu{entry.pdu_type:03d}_{slugify(entry.name)}.bin"
        valid.append(
            {
                "protocol_version": entry.protocol_version,
                "pdu_type": entry.pdu_type,
                "protocol_family": entry.protocol_family,
                "class_name": entry.class_name,
                "name": entry.name,
                "path": rel,
            }
        )
    return {
        "generated_from": "fastdis.PDU_CATALOG",
        "out_dir": out_dir_display,
        "seed_count": len(seeds),
        "catalog_seed_count": len(valid),
        "catalog_entry_count": len(fastdis.PDU_CATALOG),
        "malformed_seed_count": len(seeds) - len(valid),
        "valid_catalog_seeds": valid,
        "malformed_seeds": sorted(path for path in seeds if path.startswith("malformed/")),
    }


def acquire_lock(timeout_s: float = 30.0) -> None:
    LOCK_DIR.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            LOCK_DIR.mkdir()
            (LOCK_DIR / "pid").write_text(str(os.getpid()), encoding="utf-8")
            return
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for lock: {LOCK_DIR}")
            time.sleep(0.05)


def release_lock() -> None:
    shutil.rmtree(LOCK_DIR, ignore_errors=True)


def write_output(out_dir: Path, seeds: dict[str, bytes], manifest: dict[str, object]) -> None:
    tmp_dir = out_dir.with_name(f".{out_dir.name}.tmp.{os.getpid()}")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    for rel, data in seeds.items():
        path = tmp_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (tmp_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    tmp_dir.replace(out_dir)


def check_output(out_dir: Path, seeds: dict[str, bytes], manifest: dict[str, object]) -> int:
    expected_paths = {out_dir / rel for rel in seeds}
    expected_paths.add(out_dir / "manifest.json")
    missing = []
    stale = []
    for rel, data in seeds.items():
        path = out_dir / rel
        if not path.exists():
            missing.append(path)
            continue
        if path.read_bytes() != data:
            stale.append(path)
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        missing.append(manifest_path)
    elif manifest_path.read_text(encoding="utf-8") != json.dumps(manifest, indent=2) + "\n":
        stale.append(manifest_path)
    extra = [path for path in out_dir.rglob("*") if path.is_file() and path not in expected_paths]
    for path in missing:
        print(f"missing generated shallow fuzz file: {path.relative_to(ROOT)}", file=sys.stderr)
    for path in stale:
        print(f"stale generated shallow fuzz file: {path.relative_to(ROOT)}", file=sys.stderr)
    for path in extra:
        print(f"unexpected shallow fuzz file: {path.relative_to(ROOT)}", file=sys.stderr)
    return 1 if missing or stale or extra else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--check", action="store_true", help="Verify generated outputs are up to date instead of writing them.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    seeds = seed_map()
    manifest = build_manifest(seeds, out_dir)
    acquire_lock()
    try:
        if args.check:
            rc = check_output(out_dir, seeds, manifest)
            if rc == 0:
                print(f"shallow fuzz corpus is up to date with {len(seeds)} seeds")
            return rc
        write_output(out_dir, seeds, manifest)
        print(f"generated shallow fuzz corpus with {len(seeds)} seeds")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
