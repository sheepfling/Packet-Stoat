#!/usr/bin/env python3
"""Inspect staged Alpha5 release artifacts for publish-blocking mistakes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from artifacts import RELEASE_ARTIFACTS_DIR, REPORTS_DIR


VERSION_TAG = "v0.15.0-alpha5"
PYTHON_VERSION = "0.15.0a5"
MAX_TEXT_SCAN_BYTES = 1024 * 1024

ALLOWED_ROOT_FILES = {"RELEASE_MANIFEST.json", "SHA256SUMS", "SBOM.spdx.json"}
ALLOWED_SUFFIXES = {".zip", ".whl", ".gz", ".json", ".spdx"}
FORBIDDEN_PARTS = {
    ".agent",
    ".agents",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".pyright",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "benchmark_reports",
    "benchmark_results",
    "build",
    "dist",
    "Library",
    "Logs",
    "Obj",
    "release_artifacts",
    "Saved",
    "Temp",
    "UserSettings",
    "verification_reports",
}
FORBIDDEN_SUFFIXES = {".key", ".p12", ".pem", ".pfx", ".pyc", ".pyo"}
FORBIDDEN_FILENAMES = {".DS_Store", ".env", ".env.local", ".envrc", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
BINARY_SUFFIXES = {".dll", ".dylib", ".exe", ".lib", ".so"}

SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "pypi_token": re.compile(r"\bpypi-[A-Za-z0-9_-]{20,}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |)PRIVATE KEY-----"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parts(name: str) -> set[str]:
    return set(Path(name).parts)


def _looks_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _scan_text(data: bytes) -> list[str]:
    if not _looks_text(data):
        return []
    text = data.decode("utf-8", errors="ignore")
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def _issue(kind: str, path: str, detail: str, *, severity: str = "fail") -> dict[str, str]:
    return {"severity": severity, "kind": kind, "path": path, "detail": detail}


def validate_artifact_name(path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    name = path.name
    if name in ALLOWED_ROOT_FILES:
        return issues
    if path.suffix not in ALLOWED_SUFFIXES and not name.endswith(".tar.gz"):
        issues.append(_issue("unexpected_artifact_suffix", name, f"unexpected suffix {path.suffix!r}"))
    if name.endswith(".whl") or name.endswith(".tar.gz"):
        if PYTHON_VERSION not in name:
            issues.append(_issue("unexpected_artifact_version", name, f"expected Python version {PYTHON_VERSION}"))
        return issues
    if VERSION_TAG not in name:
        issues.append(_issue("unexpected_artifact_version", name, f"expected release tag {VERSION_TAG}"))
    return issues


def validate_path(name: str, *, source: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    path = Path(name)
    parts = _parts(name)
    forbidden = sorted(parts & FORBIDDEN_PARTS)
    if forbidden:
        issues.append(_issue("forbidden_path_part", source, f"{name} contains {', '.join(forbidden)}"))
    if path.name in FORBIDDEN_FILENAMES:
        issues.append(_issue("forbidden_filename", source, name))
    if path.suffix in FORBIDDEN_SUFFIXES:
        issues.append(_issue("forbidden_suffix", source, name))
    if "source" in source and path.suffix in BINARY_SUFFIXES:
        issues.append(_issue("binary_in_source_archive", source, name))
    return issues


def inspect_zip(path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            issues.append(_issue("zip_integrity", path.name, f"bad entry {bad}"))
        for info in archive.infolist():
            if info.is_dir():
                continue
            issues.extend(validate_path(info.filename, source=path.name))
            if info.file_size > MAX_TEXT_SCAN_BYTES:
                continue
            with archive.open(info) as handle:
                findings = _scan_text(handle.read())
            for finding in findings:
                issues.append(_issue("secret_pattern", path.name, f"{finding} in {info.filename}"))
    return issues


def inspect_loose_file(path: Path) -> list[dict[str, str]]:
    issues = validate_artifact_name(path)
    issues.extend(validate_path(path.name, source=path.name))
    if path.suffix == ".zip":
        issues.extend(inspect_zip(path))
    elif path.is_file() and path.stat().st_size <= MAX_TEXT_SCAN_BYTES:
        for finding in _scan_text(path.read_bytes()):
            issues.append(_issue("secret_pattern", path.name, finding))
    return issues


def inspect_manifest(artifact_dir: Path) -> list[dict[str, str]]:
    manifest_path = artifact_dir / "RELEASE_MANIFEST.json"
    if not manifest_path.is_file():
        return [_issue("missing_manifest", "RELEASE_MANIFEST.json", "manifest not found")]
    issues: list[dict[str, str]] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    names = {path.name for path in artifact_dir.iterdir() if path.is_file()}
    for artifact in manifest.get("artifacts", []):
        name = str(artifact.get("name", ""))
        path = artifact_dir / name
        if name not in names or not path.is_file():
            issues.append(_issue("manifest_missing_artifact", name, "manifest entry has no matching file"))
            continue
        expected = str(artifact.get("sha256", ""))
        actual = sha256_file(path)
        if expected != actual:
            issues.append(_issue("manifest_checksum_mismatch", name, "sha256 does not match manifest"))
    return issues


def inspect_artifact_dir(artifact_dir: Path) -> dict[str, object]:
    artifact_dir = artifact_dir.resolve()
    issues: list[dict[str, str]] = []
    if not artifact_dir.is_dir():
        issues.append(_issue("missing_artifact_dir", str(artifact_dir), "artifact directory not found"))
        return {"schema": "fastdis.alpha5_release_artifact_inspection.v1", "overall_status": "fail", "artifact_dir": str(artifact_dir), "issues": issues}
    files = sorted(path for path in artifact_dir.iterdir() if path.is_file())
    for path in files:
        issues.extend(inspect_loose_file(path))
    issues.extend(inspect_manifest(artifact_dir))
    fail_count = sum(1 for issue in issues if issue["severity"] == "fail")
    return {
        "schema": "fastdis.alpha5_release_artifact_inspection.v1",
        "overall_status": "pass" if fail_count == 0 else "fail",
        "artifact_dir": str(artifact_dir),
        "artifact_count": len(files),
        "fail_count": fail_count,
        "issues": issues,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Alpha5 Release Artifact Inspection",
        "",
        f"- status: `{report['overall_status']}`",
        f"- artifact_dir: `{report['artifact_dir']}`",
        f"- artifacts: `{report.get('artifact_count', 0)}`",
        f"- fail_count: `{report.get('fail_count', 0)}`",
        "",
        "## Issues",
        "",
    ]
    issues = report.get("issues", [])
    if not issues:
        lines.append("none")
    else:
        for issue in issues:
            lines.append(f"- `{issue['severity']}` `{issue['kind']}` `{issue['path']}`: {issue['detail']}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=RELEASE_ARTIFACTS_DIR / "alpha5")
    parser.add_argument("--out-dir", type=Path, default=REPORTS_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect_artifact_dir(args.artifact_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "alpha5_release_artifact_inspection.json"
    md_path = args.out_dir / "alpha5_release_artifact_inspection.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    if report["overall_status"] == "pass":
        print("artifact inspection passed")
        return 0
    print("artifact inspection failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
