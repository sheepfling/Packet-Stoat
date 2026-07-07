#!/usr/bin/env python3
"""Guard against consuming Markdown report artifacts as machine inputs."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

from artifacts import REPORTS_DIR
from report_contract import is_report_markdown_path
from report_envelope import write_json_report


ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = REPORTS_DIR / "report_input_audit.json"
REPORT_MD = REPORTS_DIR / "report_input_audit.md"
PYTHON_SOURCES = ("tools", "src")
READ_CALL_RE = re.compile(r"(read_text|open)")
REPORT_MD_LITERAL_RE = re.compile(r"""(?P<quote>["'])(?P<path>[^"']*\.md)(?P=quote)""")


def git_python_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    files: list[Path] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        path = Path(line)
        if path.parts and path.parts[0] in PYTHON_SOURCES:
            files.append(ROOT / path)
    return files


def issue(path: Path, line: int, detail: str) -> dict[str, object]:
    try:
        display_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        display_path = path.as_posix()
    return {
        "path": display_path,
        "line": line,
        "detail": detail,
    }


def audit_file(path: Path) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return issues
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not READ_CALL_RE.search(line):
            continue
        for match in REPORT_MD_LITERAL_RE.finditer(line):
            candidate = match.group("path")
            if not (
                is_report_markdown_path(candidate)
                or (
                    ".md" in candidate.lower()
                    and any(fragment in line.replace("\\", "/").lower() for fragment in ("artifacts/reports", "artifacts/verification_reports", "verification_reports"))
                )
            ):
                continue
            issues.append(
                issue(
                    path,
                    line_number,
                    f"machine-readable report consumers must not read Markdown artifact `{candidate}`; consume the sibling JSON instead",
                )
            )
    return issues


def audit_sources() -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for path in git_python_files():
        issues.extend(audit_file(path))
    return issues


def render_markdown(issues: list[dict[str, object]]) -> str:
    lines = [
        "# Report Input Audit",
        "",
        "- policy: `JSON is canonical; Markdown is leaf output only`",
        f"- issue_count: `{len(issues)}`",
        "",
    ]
    if not issues:
        lines.append("- status: no Markdown report inputs detected")
        return "\n".join(lines) + "\n"
    lines.extend(["## Issues", ""])
    for row in issues:
        lines.append(f"- `{row['path']}:{row['line']}` {row['detail']}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write", action="store_true", help="Do not write artifacts/reports outputs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues = audit_sources()
    payload = {
        "schema": "fastdis.report_input_audit.v1",
        "status": "pass" if not issues else "fail",
        "issues": issues,
    }
    if not args.no_write:
        write_json_report(
            REPORT_JSON,
            payload,
            schema="fastdis.report_input_audit.v1",
            producer="tools/check_report_inputs.py",
        )
        REPORT_MD.write_text(render_markdown(issues), encoding="utf-8")
        print(f"json: {REPORT_JSON}")
        print(f"md: {REPORT_MD}")
    if issues:
        for row in issues:
            print(f"{row['path']}:{row['line']}: {row['detail']}")
        return 1
    print("report input audit: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
