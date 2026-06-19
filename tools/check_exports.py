#!/usr/bin/env python3
"""Check that a fastdis shared library exports the public C ABI symbols."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HEADER = ROOT / "include" / "fastdis" / "fastdis.h"
SYMBOL_RE = re.compile(r"\bFASTDIS_API\b[^;]*?\bFASTDIS_CALL\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.S)


def expected_symbols_from_header(header: Path) -> list[str]:
    text = header.read_text(encoding="utf-8")
    return sorted(set(SYMBOL_RE.findall(text)))


def run(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"required tool not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        raise RuntimeError(f"{' '.join(command)} failed: {detail}") from exc
    return completed.stdout


def symbols_with_nm(library: Path) -> set[str]:
    nm = shutil.which("nm")
    if not nm:
        raise RuntimeError("nm is not available")

    if library.suffix.lower() == ".dylib":
        output = run([nm, "-gU", str(library)])
    else:
        output = run([nm, "-D", "--defined-only", str(library)])

    symbols: set[str] = set()
    for line in output.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        symbol = parts[-1]
        if symbol.startswith("_fastdis_"):
            symbol = symbol[1:]
        if symbol.startswith("fastdis_"):
            symbols.add(symbol)
    return symbols


def symbols_with_dumpbin(library: Path) -> set[str]:
    dumpbin = shutil.which("dumpbin")
    if not dumpbin:
        raise RuntimeError("dumpbin is not available")

    output = run([dumpbin, "/EXPORTS", str(library)])
    symbols: set[str] = set()
    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4 and parts[-1].startswith("fastdis_"):
            symbols.add(parts[-1])
    return symbols


def exported_symbols(library: Path) -> set[str]:
    suffix = library.suffix.lower()
    errors: list[str] = []

    if suffix == ".dll":
        try:
            return symbols_with_dumpbin(library)
        except RuntimeError as exc:
            errors.append(str(exc))

    try:
        return symbols_with_nm(library)
    except RuntimeError as exc:
        errors.append(str(exc))

    if suffix != ".dll":
        try:
            return symbols_with_dumpbin(library)
        except RuntimeError as exc:
            errors.append(str(exc))

    raise RuntimeError("; ".join(errors))


def write_symbols(path: Path, symbols: list[str]) -> None:
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(symbols, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text("\n".join(symbols) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", type=Path, help="Path to libfastdis.so, libfastdis.dylib, or fastdis.dll")
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER, help="Public C ABI header")
    parser.add_argument("--write-expected", type=Path, help="Write expected symbols to .txt or .json")
    parser.add_argument("--write-exported", type=Path, help="Write exported symbols to .txt or .json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    library = args.library
    header = args.header

    if not header.is_file():
        print(f"header not found: {header}", file=sys.stderr)
        return 2
    if not library.is_file():
        print(f"library not found: {library}", file=sys.stderr)
        return 2

    expected = expected_symbols_from_header(header)
    try:
        exported = sorted(exported_symbols(library))
    except RuntimeError as exc:
        print(f"could not inspect exports: {exc}", file=sys.stderr)
        return 2

    if args.write_expected:
        write_symbols(args.write_expected, expected)
    if args.write_exported:
        write_symbols(args.write_exported, exported)

    missing = sorted(set(expected) - set(exported))
    extra = sorted(set(exported) - set(expected))

    print(f"expected fastdis symbols: {len(expected)}")
    print(f"exported fastdis symbols: {len(exported)}")

    if missing:
        print("missing exports:", file=sys.stderr)
        for symbol in missing:
            print(f"  {symbol}", file=sys.stderr)
    if extra:
        print("extra fastdis exports:")
        for symbol in extra:
            print(f"  {symbol}")

    if missing:
        return 1

    print("export check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
