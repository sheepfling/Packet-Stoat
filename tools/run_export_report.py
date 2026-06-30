#!/usr/bin/env python3
"""Generate bundled export-check artifacts for a built fastdis shared library."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import check_exports


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "verification_reports" / "alpha2_sample"


def host_tag(library: Path | None = None) -> str:
    if library is not None:
        suffixes = "".join(library.suffixes).lower()
        name = library.name.lower()
        if name.endswith(".dll"):
            return "windows"
        if ".dylib" in suffixes or name.endswith(".dylib"):
            return "macos"
        if ".so" in suffixes or ".so." in name:
            return "linux"
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def candidate_libraries(root: Path) -> list[Path]:
    build = root / "build"
    candidates = [
        build / "Release" / "fastdis.dll",
        build / "fastdis.dll",
        build / "libfastdis.dylib",
        build / "libfastdis.0.12.0.dylib",
        build / "libfastdis.0.dylib",
        build / "libfastdis.so",
        build / "libfastdis.so.0.12.0",
        build / "libfastdis.so.0",
    ]
    return candidates


def detect_library(root: Path) -> Path:
    for candidate in candidate_libraries(root):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("could not find a built fastdis shared library under build/")


def write_lines(path: Path, values: list[str]) -> None:
    path.write_text("\n".join(values) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(summary: dict[str, object]) -> str:
    missing = summary["missing"]
    extra = summary["extra"]
    lines = [
        "# Export Check Report",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- host_platform: `{summary['host_platform']}`",
        f"- library: `{summary['library']}`",
        f"- expected_symbol_count: `{summary['expected_symbol_count']}`",
        f"- exported_symbol_count: `{summary['exported_symbol_count']}`",
        f"- status: `{summary['status']}`",
        "",
        "## Artifacts",
        "",
        f"- expected manifest: `{summary['expected_manifest']}`",
        f"- exported manifest: `{summary['exported_manifest']}`",
    ]
    if missing:
        lines.extend(["", "## Missing Exports", ""])
        lines.extend(f"- `{symbol}`" for symbol in missing)
    if extra:
        lines.extend(["", "## Extra Exports", ""])
        lines.extend(f"- `{symbol}`" for symbol in extra)
    if not missing and not extra:
        lines.extend(["", "Export check passed with no missing or extra `fastdis_*` symbols."])
    lines.append("")
    return "\n".join(lines)


def generate_report(library: Path, output_dir: Path) -> tuple[dict[str, object], Path, Path]:
    expected = check_exports.expected_symbols_from_header(check_exports.DEFAULT_HEADER)
    exported = sorted(check_exports.exported_symbols(library))
    output_dir.mkdir(parents=True, exist_ok=True)
    platform_tag = host_tag(library)

    expected_manifest = output_dir / "expected_exports.txt"
    exported_manifest = output_dir / f"exported_symbols_{platform_tag}.txt"
    write_lines(expected_manifest, expected)
    write_lines(exported_manifest, exported)

    missing = sorted(set(expected) - set(exported))
    extra = sorted(set(exported) - set(expected))
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host_platform": platform_tag,
        "library": str(library),
        "expected_symbol_count": len(expected),
        "exported_symbol_count": len(exported),
        "status": "passed" if not missing else "failed",
        "expected_manifest": display_path(expected_manifest),
        "exported_manifest": display_path(exported_manifest),
        "missing": missing,
        "extra": extra,
    }
    return summary, expected_manifest, exported_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, help="Built shared library to inspect")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for manifests and summaries")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    library = args.library or detect_library(ROOT)
    output_dir = args.output_dir

    summary, _, _ = generate_report(library, output_dir)
    (output_dir / "export_check_report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "export_check_report.md").write_text(render_markdown(summary), encoding="utf-8")

    print(f"expected manifest: {summary['expected_manifest']}")
    print(f"exported manifest: {summary['exported_manifest']}")
    print(f"status: {summary['status']}")
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
