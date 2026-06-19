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
