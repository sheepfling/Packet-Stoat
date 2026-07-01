#!/usr/bin/env python3
"""Audit tracked files for generated/intermediate/source-control clutter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from artifacts import REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = REPORTS_DIR / "source_cleanliness_audit.json"
REPORT_MD = REPORTS_DIR / "source_cleanliness_audit.md"

FORBIDDEN_PATH_PARTS = {
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".pyright",
    ".venv",
    "__pycache__",
    "benchmark_reports",
    "benchmark_results",
    "build",
    "dist",
    "generated",
    "release_artifacts",
    "verification_reports",
    "Binaries",
    "DerivedDataCache",
    "Intermediate",
    "Library",
    "Logs",
    "Obj",
    "Saved",
    "Temp",
    "UserSettings",
}
FORBIDDEN_FILENAMES = {
    ".DS_Store",
    ".env",
    ".env.local",
    ".envrc",
    "CHECKSUMS.sha256",
    "SHA256SUMS",
}
FORBIDDEN_SUFFIXES = {
    ".7z",
    ".a",
    ".app",
    ".dll",
    ".dylib",
    ".exe",
    ".gz",
    ".lib",
    ".o",
    ".obj",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".rar",
    ".so",
    ".tar",
    ".tgz",
    ".whl",
    ".zip",
}
ALLOWED_FORBIDDEN_PART_PATHS = {
    ".github/workflows/generated/workspace-ci-matrix.json",
}
STALE_REFERENCES = {
    "examples/unity/" + "FastDISUnity": "old Unity UPM scaffold; use packages/unity/com.sheepfling.fastdis",
}


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def issue(kind: str, path: str, detail: str, *, severity: str = "fail") -> dict[str, str]:
    return {"severity": severity, "kind": kind, "path": path, "detail": detail}


def tracked_files() -> list[str]:
    return git_lines(["ls-files"])


def tracked_ignored_files() -> list[str]:
    return git_lines(["ls-files", "-ci", "--exclude-standard"])


def audit_paths(paths: list[str]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for raw in paths:
        path = Path(raw)
        if raw in ALLOWED_FORBIDDEN_PART_PATHS:
            forbidden_parts = []
        else:
            parts = set(path.parts)
            forbidden_parts = sorted(parts & FORBIDDEN_PATH_PARTS)
        if forbidden_parts:
            issues.append(issue("forbidden_path_part", raw, ", ".join(forbidden_parts)))
        if path.name in FORBIDDEN_FILENAMES:
            issues.append(issue("forbidden_filename", raw, path.name))
        if path.suffix in FORBIDDEN_SUFFIXES or raw.endswith(".tar.gz"):
            issues.append(issue("forbidden_suffix", raw, path.suffix or ".tar.gz"))
    for raw in tracked_ignored_files():
        issues.append(issue("tracked_ignored_file", raw, "tracked file matches .gitignore"))
    return issues


def audit_stale_references(paths: list[str]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    text_suffixes = {
        ".cs",
        ".cpp",
        ".c",
        ".gd",
        ".h",
        ".hpp",
        ".ini",
        ".json",
        ".md",
        ".py",
        ".sample",
        ".toml",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
    for raw in paths:
        if raw == "tools/audit_source_cleanliness.py":
            continue
        path = ROOT / raw
        if path.suffix not in text_suffixes or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for needle, detail in STALE_REFERENCES.items():
            if needle in content:
                issues.append(issue("stale_reference", raw, detail))
    return issues


def build_report() -> dict[str, object]:
    paths = tracked_files()
    issues = audit_paths(paths)
    issues.extend(audit_stale_references(paths))
    fail_count = sum(1 for row in issues if row["severity"] == "fail")
    return {
        "schema": "fastdis.source_cleanliness_audit.v1",
        "overall_status": "pass" if fail_count == 0 else "fail",
        "tracked_files": len(paths),
        "fail_count": fail_count,
        "issues": issues,
        "policy": {
            "generated_outputs": "not tracked; regenerate with tools/dev_check.py or tools/check_generated_fresh.py",
            "tracked_generated_source": "allowed only when it is imported, packaged, or engine-consumed source with freshness gates",
            "build_outputs": "kept under build/ and release_artifacts/ and ignored",
        },
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Source Cleanliness Audit",
        "",
        f"- status: `{report['overall_status']}`",
        f"- tracked_files: `{report['tracked_files']}`",
        f"- fail_count: `{report['fail_count']}`",
        "",
        "## Issues",
        "",
    ]
    issues = report["issues"]
    if not issues:
        lines.append("none")
    else:
        for item in issues:
            lines.append(f"- `{item['severity']}` `{item['kind']}` `{item['path']}`: {item['detail']}")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Generated outputs, benchmark results, release artifacts, verification reports, and build products are not source-controlled.",
            "- Generated source is source-controlled only when it is imported, packaged, or consumed by engine/plugin code and covered by freshness checks.",
            "- Engine package metadata, descriptors, sample scenes, fixtures, schemas, and `.meta` files are source inputs when they are required to load examples or packages.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write", action="store_true", help="Do not write artifacts/reports outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    if not args.no_write:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
        print(f"JSON: {REPORT_JSON}")
        print(f"Markdown: {REPORT_MD}")
    if report["overall_status"] == "pass":
        print("source cleanliness audit passed")
        return 0
    print("source cleanliness audit failed", file=sys.stderr)
    for item in report["issues"]:
        print(f"  - {item['kind']} {item['path']}: {item['detail']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
