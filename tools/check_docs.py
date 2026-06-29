#!/usr/bin/env python3
"""Audit tracked Markdown docs for local links, orphans, and absolute paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
from typing import Iterable, cast
from urllib.parse import unquote, urlsplit

from artifacts import REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = REPORTS_DIR / "docs_audit.json"
REPORT_MD = REPORTS_DIR / "docs_audit.md"

INLINE_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s+(\S+)", re.MULTILINE)
LOCAL_ABSOLUTE_RE = re.compile(
    r"(?P<path>"
    r"file://[^\s)>\"]+"
    r"|/Users/[^\s)>\"]+"
    r"|/private/[^\s)>\"]+"
    r"|/tmp/[^\s)>\"]+"
    r"|[A-Za-z]:\\[^\s)>\"]+"
    r")"
)
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "data"}
DOC_FRONT_DOORS = {
    "README.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/README.md",
    "benchmarks/README.md",
    "examples/common/README.md",
    "packages/lattice/README.md",
    "references/open-dis/README.md",
    "schemas/patches/dis6/README.md",
    "schemas/patches/dis7/README.md",
}
README_ENTRYPOINT_PARTS = {
    "examples",
    "integrations",
    "references",
    "schemas",
}
IGNORED_DOC_ROOTS = {
    ".build",
    "build",
    "dist",
    "verification_reports",
    "release_artifacts",
    "benchmark_results",
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


def source_markdown() -> list[str]:
    tracked = set(git_lines(["ls-files", "*.md"]))
    untracked = set(git_lines(["ls-files", "--others", "--exclude-standard", "*.md"]))
    return sorted(
        path
        for path in (tracked | untracked)
        if (ROOT / path).is_file() and Path(path).parts and Path(path).parts[0] not in IGNORED_DOC_ROOTS
    )


def issue(kind: str, path: str, detail: str, *, line: int | None = None) -> dict[str, object]:
    item: dict[str, object] = {"kind": kind, "path": path, "detail": detail}
    if line is not None:
        item["line"] = line
    return item


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if " " in target:
        target = target.split(" ", 1)[0]
    return target.strip()


def split_local_target(target: str) -> tuple[str, str]:
    parsed = urlsplit(target)
    if parsed.scheme:
        return target, ""
    path = target.split("#", 1)[0].split("?", 1)[0]
    fragment = ""
    if "#" in target:
        fragment = target.split("#", 1)[1].split("?", 1)[0]
    return unquote(path), fragment


def is_windows_absolute(target: str) -> bool:
    try:
        return PureWindowsPath(target).is_absolute()
    except ValueError:
        return False


def link_targets(text: str) -> Iterable[tuple[int, str]]:
    for match in INLINE_LINK_RE.finditer(text):
        yield match.start(1), normalize_target(match.group(1))
    for match in REFERENCE_LINK_RE.finditer(text):
        yield match.start(1), normalize_target(match.group(1))


def audit_absolute_paths(path: str, text: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for match in LOCAL_ABSOLUTE_RE.finditer(text):
        issues.append(
            issue(
                "absolute_local_path",
                path,
                f"replace local absolute path `{match.group('path')}` with a relative path or env-var placeholder",
                line=line_number(text, match.start()),
            )
        )
    return issues


def audit_links(path: str, text: str) -> tuple[list[dict[str, object]], set[str]]:
    issues: list[dict[str, object]] = []
    linked_docs: set[str] = set()
    source = ROOT / path
    for offset, raw_target in link_targets(text):
        if not raw_target or raw_target.startswith("#"):
            continue
        parsed = urlsplit(raw_target)
        if parsed.scheme in EXTERNAL_SCHEMES:
            continue
        if raw_target.startswith("file://") or raw_target.startswith("/") or is_windows_absolute(raw_target):
            issues.append(
                issue(
                    "absolute_link",
                    path,
                    f"local Markdown links must be relative: `{raw_target}`",
                    line=line_number(text, offset),
                )
            )
            continue
        if parsed.scheme and parsed.scheme not in EXTERNAL_SCHEMES:
            issues.append(
                issue(
                    "unsupported_link_scheme",
                    path,
                    f"unsupported local link scheme in `{raw_target}`",
                    line=line_number(text, offset),
                )
            )
            continue
        local_path, _fragment = split_local_target(raw_target)
        if not local_path:
            continue
        target = (source.parent / local_path).resolve()
        try:
            relative_target = target.relative_to(ROOT)
        except ValueError:
            issues.append(
                issue(
                    "link_escapes_repo",
                    path,
                    f"local link escapes the repository: `{raw_target}`",
                    line=line_number(text, offset),
                )
            )
            continue
        if not target.exists():
            issues.append(
                issue(
                    "dead_local_link",
                    path,
                    f"target does not exist: `{raw_target}`",
                    line=line_number(text, offset),
                )
            )
            continue
        if target.is_file() and target.suffix.lower() == ".md":
            linked_docs.add(relative_target.as_posix())
    return issues, linked_docs


def audit_orphans(paths: list[str], linked_docs: set[str]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for path in paths:
        if path in DOC_FRONT_DOORS:
            continue
        parts = Path(path).parts
        if parts and parts[0] in README_ENTRYPOINT_PARTS and Path(path).name == "README.md":
            continue
        if path not in linked_docs:
            issues.append(
                issue(
                    "orphan_doc",
                    path,
                    "tracked Markdown file is not linked from another tracked Markdown document",
                )
            )
    return issues


def build_report() -> dict[str, object]:
    paths = source_markdown()
    issues: list[dict[str, object]] = []
    linked_docs: set[str] = set()
    for path in paths:
        text = (ROOT / path).read_text(encoding="utf-8")
        issues.extend(audit_absolute_paths(path, text))
        link_issues, doc_links = audit_links(path, text)
        issues.extend(link_issues)
        linked_docs.update(doc_links)
    issues.extend(audit_orphans(paths, linked_docs))
    return {
        "schema": "fastdis.docs_audit.v1",
        "overall_status": "pass" if not issues else "fail",
        "source_markdown_files": len(paths),
        "linked_markdown_files": len(linked_docs),
        "issue_count": len(issues),
        "issues": issues,
        "policy": {
            "local_links": "must be relative and resolve inside the repository",
            "absolute_paths": "local machine paths are not allowed in tracked Markdown",
            "orphans": "tracked Markdown files must be linked by another tracked Markdown file unless listed as a front door",
        },
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Documentation Audit",
        "",
        f"- status: `{report['overall_status']}`",
        f"- source_markdown_files: `{report['source_markdown_files']}`",
        f"- linked_markdown_files: `{report['linked_markdown_files']}`",
        f"- issue_count: `{report['issue_count']}`",
        "",
        "## Issues",
        "",
    ]
    issues = cast(list[dict[str, object]], report["issues"])
    if not issues:
        lines.append("none")
    else:
        for item in issues:
            location = f"{item['path']}:{item['line']}" if "line" in item else str(item["path"])
            lines.append(f"- `{item['kind']}` `{location}`: {item['detail']}")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Tracked Markdown links to repo files must be relative and must resolve.",
            "- Tracked Markdown must not contain local absolute paths such as `/Users/...`, `/tmp/...`, `file://...`, or `C:\\...`.",
            "- Tracked Markdown files should be linked from the front-door README or docs index unless they are local package README entry points.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write", action="store_true", help="Do not write build/reports outputs")
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
        print("documentation audit passed")
        return 0
    print("documentation audit failed", file=sys.stderr)
    for item in cast(list[dict[str, object]], report["issues"]):
        location = f"{item['path']}:{item['line']}" if "line" in item else item["path"]
        print(f"  - {item['kind']} {location}: {item['detail']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
