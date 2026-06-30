#!/usr/bin/env python3
"""Generate a checked-in GitHub Actions matrix from the workspace manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import workspace_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".github" / "workflows" / "generated" / "workspace-ci-matrix.json"
HOST_OS = {
    "windows": "windows-latest",
    "macos": "macos-latest",
    "linux": "ubuntu-latest",
}


def _route_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route in workspace_manifest.route_specs(manifest):
        route_id = str(route.get("id") or "")
        surface = str(route.get("surface") or "")
        target = str(route.get("target") or "")
        backend = str(route.get("backend") or "")
        proof_kind = str(route.get("proof_kind") or "")
        preferred_version = workspace_manifest.route_preferred_surface_version(route, manifest)
        supported_versions = workspace_manifest.route_supported_surface_versions(route, manifest)
        versions = supported_versions or ([preferred_version] if preferred_version else [""])
        for host_class in [str(value) for value in route.get("supported_host_classes") or []]:
            for version in versions:
                version_kind = "preferred" if version == preferred_version else "compat"
                rows.append(
                    {
                        "route": route_id,
                        "surface": surface,
                        "host_class": host_class,
                        "os": HOST_OS[host_class],
                        "target": target,
                        "backend": backend,
                        "proof_kind": proof_kind,
                        "surface_version": version,
                        "version_kind": version_kind,
                        "bootstrap_capable": workspace_manifest.route_bootstrap_capable(route),
                        "job_name": f"{route_id}-{host_class}-{version or 'default'}",
                    }
                )
    return rows


def build_document(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = manifest or workspace_manifest.load_manifest()
    rows = _route_rows(payload)
    python_rows = [row for row in rows if row["route"] == "python-core"]
    host_python_rows = [
        row for row in rows if row["surface"] == "python" and row["target"] == "host"
    ]
    declared_engine_rows = [row for row in rows if row["surface"] in {"godot", "unity", "unreal"}]
    declared_cross_build_rows = [row for row in rows if row["target"] != "host"]
    native_host_rows = []
    seen_hosts: set[str] = set()
    for row in rows:
        if row["target"] != "host":
            continue
        host_class = row["host_class"]
        if host_class in seen_hosts:
            continue
        native_host_rows.append({"host_class": host_class, "os": HOST_OS[host_class]})
        seen_hosts.add(host_class)

    preferred_python = workspace_manifest.route_preferred_surface_version(
        workspace_manifest.route_spec("python-core", payload),
        payload,
    )
    return {
        "schema": "packet_stoat.workspace_ci_matrix.v1",
        "workspace": workspace_manifest.workspace_metadata(payload),
        "preferred_python_version": preferred_python,
        "python_green": {
            "include": [
                {
                    "os": row["os"],
                    "host_class": row["host_class"],
                    "python-version": row["surface_version"],
                    "version_kind": row["version_kind"],
                    "route": row["route"],
                    "job_name": row["job_name"],
                }
                for row in python_rows
            ]
        },
        "native_green": {"include": native_host_rows},
        "workspace_ci": {"include": rows},
        "workspace_ci_host_python": {"include": host_python_rows},
        "workspace_ci_declared_engine": {"include": declared_engine_rows},
        "workspace_ci_declared_cross_build": {"include": declared_cross_build_rows},
        "quality_green": {"python-version": preferred_python},
        "lattice_green": {"python-version": preferred_python},
        "symbols_proof": {"python-version": preferred_python, "node-version": "22"},
        "build_python_sdist_wheel": {"python-version": preferred_python},
        "build_windows_ctypes_wheel": {"os": "windows-latest", "python-version": preferred_python},
    }


def _render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2) + "\n"


def _render_summary(document: dict[str, Any]) -> str:
    lines = [
        "Packet Stoat workspace CI matrix",
        f"preferred_python_version={document['preferred_python_version']}",
        f"python_green={len(document['python_green']['include'])}",
        f"native_green={len(document['native_green']['include'])}",
        f"workspace_ci={len(document['workspace_ci']['include'])}",
        f"workspace_ci_host_python={len(document['workspace_ci_host_python']['include'])}",
        f"workspace_ci_declared_engine={len(document['workspace_ci_declared_engine']['include'])}",
        f"workspace_ci_declared_cross_build={len(document['workspace_ci_declared_cross_build']['include'])}",
    ]
    return "\n".join(lines) + "\n"


def _write_output(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render(document), encoding="utf-8")


def _load_checked_in(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _emit_github_outputs(path: Path, output_path: Path) -> None:
    document = _load_checked_in(path)
    lines = [
        f"python_green={json.dumps(document['python_green'])}",
        f"native_green={json.dumps(document['native_green'])}",
        f"workspace_ci={json.dumps(document['workspace_ci'])}",
        f"workspace_ci_host_python={json.dumps(document['workspace_ci_host_python'])}",
        f"workspace_ci_declared_engine={json.dumps(document['workspace_ci_declared_engine'])}",
        f"workspace_ci_declared_cross_build={json.dumps(document['workspace_ci_declared_cross_build'])}",
        f"preferred_python={document['preferred_python_version']}",
        f"symbols_proof_python={document['symbols_proof']['python-version']}",
        f"symbols_proof_node={document['symbols_proof']['node-version']}",
        f"build_python_sdist_wheel_python={document['build_python_sdist_wheel']['python-version']}",
        f"build_windows_ctypes_wheel_python={document['build_windows_ctypes_wheel']['python-version']}",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    write_parser = subparsers.add_parser("write", help="Write the generated matrix file")
    write_parser.add_argument("--path", type=Path, default=DEFAULT_OUTPUT)

    check_parser = subparsers.add_parser("check", help="Verify the checked-in matrix matches the manifest")
    check_parser.add_argument("--path", type=Path, default=DEFAULT_OUTPUT)

    print_parser = subparsers.add_parser("print", help="Print the generated matrix")
    print_parser.add_argument("--path", type=Path, default=DEFAULT_OUTPUT)
    print_parser.add_argument("--format", choices=("json", "summary"), default="json")
    print_parser.add_argument(
        "--section",
        choices=(
            "document",
            "python_green",
            "native_green",
            "workspace_ci",
            "workspace_ci_host_python",
            "workspace_ci_declared_engine",
            "workspace_ci_declared_cross_build",
        ),
        default="document",
    )

    outputs_parser = subparsers.add_parser("github-outputs", help="Emit GitHub Actions outputs from the checked-in file")
    outputs_parser.add_argument("--path", type=Path, default=DEFAULT_OUTPUT)
    outputs_parser.add_argument("--output", type=Path, required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    document = build_document()
    if args.command == "write":
        _write_output(args.path, document)
        return 0
    if args.command == "check":
        expected = _render(document)
        actual = args.path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"workspace ci matrix is stale: {args.path}")
            return 1
        return 0
    if args.command == "print":
        selected: Any = document
        if args.section != "document":
            selected = document[args.section]
        if args.format == "summary":
            if args.section == "document":
                sys.stdout.write(_render_summary(document))
            else:
                rows = list(selected.get("include") or [])
                title = f"Packet Stoat workspace CI {args.section}"
                lines = [title]
                for row in rows:
                    lines.append(
                        f"{row['job_name']}="
                        + f"{row['route']};surface={row['surface']};host={row['host_class']};target={row['target']};backend={row['backend']};version={row['surface_version']};kind={row['version_kind']}"
                    )
                if len(lines) == 1:
                    lines.append("none")
                sys.stdout.write("\n".join(lines) + "\n")
        else:
            sys.stdout.write(json.dumps(selected, indent=2) + "\n")
        return 0
    if args.command == "github-outputs":
        _emit_github_outputs(args.path, args.output)
        return 0
    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
