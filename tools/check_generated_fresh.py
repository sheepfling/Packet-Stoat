#!/usr/bin/env python3
"""Check that generated Alpha 3 catalog/IR/fuzz artifacts are fresh."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = [
    ("pdu catalog", [sys.executable, str(ROOT / "tools" / "generate_pdu_catalog.py"), "--check"]),
    ("normalized IR", [sys.executable, str(ROOT / "tools" / "generate_fastdis_ir.py"), "--check"]),
    ("message views", [sys.executable, str(ROOT / "tools" / "generate_message_views.py"), "--check"]),
    ("PDU coverage", [sys.executable, str(ROOT / "tools" / "generate_pdu_coverage.py"), "--check"]),
    ("typed PDU parsers", [sys.executable, str(ROOT / "tools" / "generate_typed_pdu_parsers.py"), "--check"]),
    ("semantic PDU parsers", [sys.executable, str(ROOT / "tools" / "generate_semantic_pdu_parsers.py"), "--check"]),
    ("Epic 2 semantic waves", [sys.executable, str(ROOT / "tools" / "generate_epic2_semantic_waves.py"), "--check"]),
    ("Epic 2 milestones", [sys.executable, str(ROOT / "tools" / "generate_epic2_milestones.py"), "--check"]),
    ("PDU logging catalog", [sys.executable, str(ROOT / "tools" / "generate_pdu_log_catalog.py"), "--check"]),
    ("standards status", [sys.executable, str(ROOT / "tools" / "generate_standards_status.py"), "--check"]),
    (
        "dead-reckoning coverage",
        [sys.executable, str(ROOT / "tools" / "generate_dead_reckoning_coverage.py"), "--check"],
    ),
    (
        "version translation manifest",
        [sys.executable, str(ROOT / "tools" / "generate_version_translation_manifest.py"), "--check"],
    ),
    ("endpoint mapping", [sys.executable, str(ROOT / "tools" / "generate_endpoint_mapping_manifest.py"), "--check"]),
    ("shallow fuzz corpus", [sys.executable, str(ROOT / "tools" / "generate_shallow_fuzz_corpus.py"), "--check"]),
]


def main() -> int:
    failures = 0
    for label, command in CHECKS:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures += 1
            if result.stdout:
                print(result.stdout, end="", file=sys.stderr)
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            print(f"[fail] {label}", file=sys.stderr)
            continue
        print(f"[ok] {label}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
