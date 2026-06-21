#!/usr/bin/env python3
"""List built FastDIS deliverables and write a verification report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

from artifacts import CMAKE_HOST, DIST_DIR, REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPORTS_DIR
DEFAULT_BASENAME = "deliverables_report"


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        try:
            return str(path.absolute().relative_to(root.absolute()))
        except ValueError:
            return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(path: Path, root: Path, *, description: str) -> dict[str, object]:
    exists = path.exists()
    payload: dict[str, object] = {
        "path": _rel(path, root),
        "description": description,
        "exists": exists,
        "kind": "symlink" if path.is_symlink() else ("file" if path.is_file() else "missing"),
    }
    if exists and path.is_file():
        payload["bytes"] = path.stat().st_size
        payload["sha256"] = _sha256(path)
    if exists and path.is_symlink():
        payload["target"] = str(path.readlink())
    return payload


def _glob(root: Path, patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(root.glob(pattern))
    return sorted(set(paths))


def _duplicate_local_artifacts(root: Path) -> list[str]:
    duplicate_pattern = re.compile(r" \d+(?=\.)| \d+$")
    candidates: list[str] = []
    for base in (DIST_DIR if root == ROOT else root / "build" / "dist", root / "generated"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if duplicate_pattern.search(path.name):
                candidates.append(_rel(path, root))
    return sorted(candidates)


def _section(name: str, description: str, artifacts: list[dict[str, object]], *, required: bool = False) -> dict[str, object]:
    present = [artifact for artifact in artifacts if artifact["exists"]]
    if required and not present:
        status = "missing"
    elif not artifacts:
        status = "not-built"
    elif present:
        status = "present"
    else:
        status = "not-built"
    return {
        "name": name,
        "description": description,
        "status": status,
        "artifact_count": len(present),
        "required": required,
        "artifacts": artifacts,
    }


def build_report(root: Path = ROOT) -> dict[str, object]:
    dist_dir = DIST_DIR if root == ROOT else root / "build" / "dist"
    reports_dir = REPORTS_DIR if root == ROOT else root / "build" / "reports"
    cmake_host = CMAKE_HOST if root == ROOT else root / "build" / "cmake" / "host"
    dist_artifacts = [
        _artifact(path, root, description="Python distribution artifact")
        for path in _glob(dist_dir, ("*.whl", "*.tar.gz"))
    ]
    native_artifacts = [
        _artifact(path, root, description="Native shared library")
        for path in _glob(cmake_host, ("libfastdis*.dylib", "libfastdis*.so", "fastdis.dll"))
    ]
    native_tools = [
        _artifact(path, root, description="Native test/example/benchmark executable")
        for path in _glob(cmake_host, ("fastdis_*",))
        if path.is_file() and path.name not in {"fastdisTargets.cmake", "fastdisTargets-release.cmake"}
    ]
    unreal_artifacts = [
        _artifact(root / "examples" / "unreal" / "FastDis" / "FastDis.uplugin", root, description="Unreal plugin descriptor"),
        *[
            _artifact(path, root, description="Unreal staged fastdis header/library")
            for path in _glob(
                root / "examples" / "unreal" / "FastDis" / "ThirdParty" / "fastdis",
                ("include/fastdis/*.h", "include/fastdis/*.hpp", "lib/**/*"),
            )
            if path.is_file() or path.is_symlink()
        ],
    ]
    godot_artifacts = [
        _artifact(root / "examples" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "fastdis.gdextension", root, description="Godot demo extension descriptor"),
        _artifact(root / "examples" / "godot" / "fastdis_orientation_verification" / "addons" / "fastdis" / "fastdis.gdextension", root, description="Godot orientation extension descriptor"),
        *[
            _artifact(path, root, description="Godot staged native library/manifest")
            for base in (
                root / "examples" / "godot" / "fastdis_demo" / "addons" / "fastdis" / "bin",
                root / "examples" / "godot" / "fastdis_orientation_verification" / "addons" / "fastdis" / "bin",
            )
            for path in _glob(base, ("*",))
            if path.is_file() or path.is_symlink()
        ],
    ]
    unity_root = root / "integrations" / "unity" / "com.sheepfling.fastdis"
    unity_artifacts = [
        _artifact(unity_root / "package.json", root, description="Unity UPM package manifest"),
        _artifact(unity_root / "README.md", root, description="Unity package README"),
        *[
            _artifact(path, root, description="Unity package source/sample/documentation file")
            for path in _glob(
                unity_root,
                (
                    "Runtime/**/*.cs",
                    "Runtime/**/*.asmdef",
                    "Runtime/Plugins/**/*.md",
                    "Editor/**/*.cs",
                    "Editor/**/*.asmdef",
                    "Tests/**/*.cs",
                    "Tests/**/*.asmdef",
                    "Samples~/**/*.md",
                    "Samples~/**/*.cs",
                    "Documentation~/*.md",
                    "CHANGELOG.md",
                    "LICENSE.md",
                    "Third Party Notices.md",
                ),
            )
            if path.is_file()
        ],
    ]
    lattice_artifacts = [
        _artifact(root / "integrations" / "lattice" / "pyproject.toml", root, description="Lattice plugin Python package metadata"),
        _artifact(root / "integrations" / "lattice" / "README.md", root, description="Lattice plugin package README"),
        *[
            _artifact(path, root, description="Lattice plugin source/config/fixture/test file")
            for path in _glob(
                root / "integrations" / "lattice",
                (
                    "src/packet_stoat_lattice/*.py",
                    "configs/*.yaml",
                    "examples/*.json",
                    "tests/*.py",
                ),
            )
            if path.is_file()
        ],
    ]
    lattice_package_artifacts = [
        _artifact(path, root, description="Built Lattice plugin distribution artifact")
        for path in _glob(root / "integrations" / "lattice" / "dist", ("*.whl", "*.tar.gz"))
    ]
    lattice_artifacts.extend(lattice_package_artifacts)
    report_artifacts = [
        _artifact(path, root, description="Verification/report artifact")
        for path in _glob(reports_dir, ("*.json", "*.md"))
    ]
    duplicate_local = _duplicate_local_artifacts(root)
    sections = [
        _section("python_packages", "Installable Python sdist/wheel outputs under build/dist/.", dist_artifacts),
        _section("native_core", "C ABI shared library outputs under build/cmake/host/.", native_artifacts),
        _section("native_tools", "Native tests, examples, and benchmark executables under build/cmake/host/.", native_tools),
        _section("unreal_plugin", "Unreal plugin descriptor and staged ThirdParty fastdis payload.", unreal_artifacts),
        _section("godot_extension", "Godot descriptors and staged native extension payloads.", godot_artifacts),
        _section("unity_package", "Unity UPM package scaffold under integrations/unity/com.sheepfling.fastdis.", unity_artifacts),
        _section("lattice_plugin", "Mock-first Anduril Lattice-shaped Python plugin package under integrations/lattice.", lattice_artifacts),
        _section("verification_reports", "Local machine-readable verification reports.", report_artifacts),
    ]
    missing_required = [
        section["name"]
        for section in sections
        if section["required"] and section["status"] == "missing"
    ]
    overall = "pass"
    if missing_required:
        overall = "fail"
    elif duplicate_local:
        overall = "warn"
    return {
        "overall_status": overall,
        "repo_root": str(root),
        "summary": {
            section["name"]: {
                "status": section["status"],
                "artifact_count": section["artifact_count"],
            }
            for section in sections
        },
        "duplicate_local_artifacts": duplicate_local,
        "sections": sections,
        "how_to_rebuild": {
            "default_green_check": "python tools/dev_check.py",
            "full_local_check": "python tools/dev_check.py --all",
            "package_artifacts": "python tools/dev_check.py --package",
            "native_artifacts": "python tools/dev_check.py --native",
            "engine_doctors": "python tools/dev_check.py --engine-doctors",
            "lattice_gap_report": "python tools/dev_check.py --lattice",
            "lattice_package": "python -m build integrations/lattice",
            "release_artifacts": "python tools/dev_check.py --release-artifacts",
            "inspect_release_artifacts": "python tools/inspect_alpha5_release_artifacts.py",
            "clean_local_artifacts": "python tools/clean_artifacts.py --apply",
        },
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# FastDIS Deliverables Report",
        "",
        f"- overall_status: `{report['overall_status']}`",
        f"- repo_root: `{report['repo_root']}`",
        "",
        "## Rebuild Commands",
        "",
    ]
    for label, command in report["how_to_rebuild"].items():
        lines.append(f"- {label}: `{command}`")
    if report["duplicate_local_artifacts"]:
        lines.extend(["", "## Local Duplicate Artifacts", ""])
        for path in report["duplicate_local_artifacts"]:
            lines.append(f"- `{path}`")
    lines.extend(["", "## Deliverables", ""])
    for section in report["sections"]:
        lines.extend(
            [
                f"### {section['name']}",
                "",
                f"- status: `{section['status']}`",
                f"- artifacts: `{section['artifact_count']}`",
                f"- description: {section['description']}",
                "",
            ]
        )
        artifacts = section["artifacts"]
        if not artifacts:
            lines.append("_No artifacts found._")
            lines.append("")
            continue
        for artifact in artifacts:
            status = "present" if artifact["exists"] else "missing"
            size = f", {artifact['bytes']} bytes" if "bytes" in artifact else ""
            sha = f", sha256 `{artifact['sha256'][:12]}...`" if "sha256" in artifact else ""
            lines.append(f"- `{artifact['path']}`: {status}{size}{sha}")
        lines.append("")
    return "\n".join(lines)


def render_summary(report: dict[str, object]) -> str:
    lines = [
        "FastDIS deliverables",
        f"overall_status: {report['overall_status']}",
        "",
        "Groups:",
    ]
    for section in report["sections"]:
        lines.append(
            f"- {section['name']}: {section['status']} "
            f"({section['artifact_count']} artifact(s))"
        )
    if report["duplicate_local_artifacts"]:
        lines.extend(["", "Duplicate local artifacts:"])
        for path in report["duplicate_local_artifacts"]:
            lines.append(f"- {path}")
    lines.extend(["", "Rebuild/check commands:"])
    for label, command in report["how_to_rebuild"].items():
        lines.append(f"- {label}: {command}")
    if "written" in report:
        lines.extend(
            [
                "",
                f"JSON: {report['written']['json']}",
                f"Markdown: {report['written']['markdown']}",
            ]
        )
    return "\n".join(lines)


def write_report(report: dict[str, object], out_dir: Path = DEFAULT_OUT_DIR) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{DEFAULT_BASENAME}.json"
    md_path = out_dir / f"{DEFAULT_BASENAME}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("summary", "text", "json"), default="summary")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--no-write", action="store_true", help="Print only; do not write report files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    if not args.no_write:
        json_path, md_path = write_report(report, args.out_dir)
        report["written"] = {"json": str(json_path), "markdown": str(md_path)}
    if args.format == "json":
        print(json.dumps(report, indent=2))
    elif args.format == "summary":
        print(render_summary(report))
    else:
        print(render_markdown(report))
        if "written" in report:
            print(f"JSON: {report['written']['json']}")
            print(f"Markdown: {report['written']['markdown']}")
    return 1 if report["overall_status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
