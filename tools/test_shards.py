#!/usr/bin/env python3
"""List and run named FastDIS verification shards."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from artifacts import CMAKE_HOST
from artifacts import REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = REPORTS_DIR / "test_shards_report.json"


@dataclass(frozen=True)
class HostFacts:
    host_class: str
    docker_available: bool
    can_run_native_engine_evidence: bool
    can_run_linux_docker_evidence: bool
    preferred_runtime_hosts: tuple[str, ...]
    cross_build_targets: tuple[str, ...]


@dataclass(frozen=True)
class StepSpec:
    label: str
    command: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class ShardSpec:
    name: str
    description: str
    commands: tuple[StepSpec, ...] = ()
    children: tuple[str, ...] = ()
    host_scope: str = "all"
    notes: tuple[str, ...] = ()


def host_facts() -> HostFacts:
    system = platform.system().lower()
    if system == "darwin":
        host_class = "macos"
        cross_build_targets = ("macos", "linux", "windows")
        preferred_runtime_hosts = ("macos", "linux-docker")
    elif system == "windows":
        host_class = "windows"
        cross_build_targets = ("windows", "linux", "macos")
        preferred_runtime_hosts = ("windows", "linux-docker")
    else:
        host_class = "linux"
        cross_build_targets = ("linux",)
        preferred_runtime_hosts = ("linux",)
    docker_available = shutil.which("docker") is not None
    return HostFacts(
        host_class=host_class,
        docker_available=docker_available,
        can_run_native_engine_evidence=host_class in {"macos", "windows", "linux"},
        can_run_linux_docker_evidence=docker_available,
        preferred_runtime_hosts=preferred_runtime_hosts,
        cross_build_targets=cross_build_targets,
    )


def _py() -> str:
    return sys.executable


SHARDS: dict[str, ShardSpec] = {
    "python-green": ShardSpec(
        name="python-green",
        description="Core Python import/CLI/test shard.",
        commands=(
            StepSpec("python import", (_py(), "-c", "import fastdis; print(fastdis.HAS_C_ACCELERATOR)")),
            StepSpec("fastdis doctor", (_py(), "-m", "fastdis", "doctor")),
            StepSpec("pytest", (_py(), "-m", "pytest")),
        ),
        notes=(
            "This shard is the lowest-friction repo green for Python/core work.",
            "It intentionally excludes linting, typing, docs audits, and engine/plugin receipts.",
        ),
    ),
    "quality-green": ShardSpec(
        name="quality-green",
        description="Static quality shard: generated freshness, docs, lint, typing.",
        commands=(
            StepSpec("generated freshness", (_py(), "tools/check_generated_fresh.py")),
            StepSpec("source cleanliness audit", (_py(), "tools/audit_source_cleanliness.py")),
            StepSpec("documentation audit", (_py(), "tools/check_docs.py")),
            StepSpec("ruff", (_py(), "-m", "ruff", "check", "src", "tests", "tools")),
            StepSpec("pyright", (_py(), "-m", "pyright")),
        ),
        notes=("This is the shard behind linting, typing, and docs-link liveness.",),
    ),
    "native-green": ShardSpec(
        name="native-green",
        description="Native library build and CTest shard.",
        commands=(
            StepSpec("native build", (_py(), "tools/build_native.py")),
            StepSpec(
                "native ctest",
                ("ctest", "--test-dir", str(CMAKE_HOST), "--build-config", "Release", "--output-on-failure"),
            ),
        ),
        notes=("This shard keeps the C/C++ runtime honest independently of Python-only checks.",),
    ),
    "lattice-green": ShardSpec(
        name="lattice-green",
        description="Lattice adapter/package shard on the canonical packages/lattice route.",
        commands=(
            StepSpec(
                "Lattice focused pytest",
                (
                    _py(),
                    "-m",
                    "pytest",
                    "tests/test_lattice_adapter_scaffold.py",
                    "tests/test_lattice_mapping_egress_contracts.py",
                    "tests/test_lattice_dis_mapping_plan.py",
                    "tests/test_lattice_shim_tool.py",
                    "tests/test_lattice_compatibility_harness.py",
                    "tests/test_deliverables_report.py",
                    "tests/test_alpha4_release_audit.py",
                    "packages/lattice/tests/test_lattice_plugin_entrypoints.py",
                ),
            ),
            StepSpec("Lattice SDK gap report", (_py(), "tools/run_alpha4_1_sdk_gap_report.py")),
            StepSpec("Lattice package build", (_py(), "-m", "build", "packages/lattice")),
        ),
        notes=(
            "This is the plugin(adapter) green shard.",
            "The package route is packages/lattice; integrations/lattice is no longer canonical.",
        ),
    ),
    "unreal-green": ShardSpec(
        name="unreal-green",
        description="Unreal host-readiness and current-evidence shard.",
        commands=(
            StepSpec("Unreal doctor", (_py(), "tools/unreal_workflow.py", "doctor", "--engine-version", "5.8")),
            StepSpec("Unreal host lane matrix", (_py(), "tools/unreal_workflow.py", "host-lane-matrix")),
        ),
        notes=(
            "macOS and Windows are the preferred native Unreal runtime/evidence hosts.",
            "Linux Docker is the preferred Linux proof lane when Docker and staged engines are available.",
            "This shard summarizes current host truth without forcing every heavy engine rerun on every invocation.",
        ),
    ),
    "unity-green": ShardSpec(
        name="unity-green",
        description="Unity host-readiness shard with native-matrix readiness.",
        commands=(
            StepSpec("Unity doctor", (_py(), "tools/unity_workflow.py", "doctor", "--unity-version", "6000.5")),
            StepSpec("Unity native matrix doctor", (_py(), "tools/build_unity_native_matrix.py", "doctor")),
            StepSpec("Unity workflow report", (_py(), "tools/unity_workflow.py", "report", "--unity-version", "6000.5")),
        ),
        notes=(
            "Local Unity runtime proof stays host-specific.",
            "Cross-host signoff is a separate aggregate receipt, not a requirement for one host to be locally green.",
        ),
    ),
    "godot-green": ShardSpec(
        name="godot-green",
        description="Godot host-readiness shard.",
        commands=(StepSpec("Godot doctor", (_py(), "tools/godot_workflow.py", "doctor")),),
        notes=("Godot remains a native-host runtime lane.",),
    ),
    "evidence-green": ShardSpec(
        name="evidence-green",
        description="Evidence-pack and experiment-report shard.",
        commands=(
            StepSpec("evidence pack", (_py(), "tools/generate_evidence_pack.py", "--clean", "--render-symbols", "never")),
            StepSpec(
                "evidence pack check",
                (_py(), "tools/check_evidence_pack.py", str(ROOT / "artifacts" / "verification_reports" / "evidence" / "latest" / "manifest.json")),
            ),
            StepSpec("Epic 2 audit", (_py(), "tools/run_epic2_audit.py")),
            StepSpec("Epic 2 milestones", (_py(), "tools/generate_epic2_milestones.py")),
            StepSpec("deliverables report", (_py(), "tools/list_deliverables.py"), required=False),
        ),
        notes=(
            "This shard is the source-truth evidence receipt lane.",
            "It is the right place to hang experiment/result regeneration that should stay honest but credential-free.",
        ),
    ),
    "release-green": ShardSpec(
        name="release-green",
        description="Credential-free release packaging/artifact shard.",
        commands=(
            StepSpec("stage Alpha5 release artifacts", (_py(), "tools/build_alpha5_release_artifacts.py", "--clean")),
            StepSpec("smoke Alpha5 release artifacts", (_py(), "tools/smoke_alpha5_release_artifacts.py")),
            StepSpec("inspect Alpha5 release artifacts", (_py(), "tools/inspect_alpha5_release_artifacts.py")),
        ),
        notes=("This shard is heavier than day-to-day green and is closer to release-candidate validation.",),
    ),
    "overall-green": ShardSpec(
        name="overall-green",
        description="Aggregate local green: core, quality, engines, plugin, and evidence.",
        children=(
            "python-green",
            "evidence-green",
            "quality-green",
            "native-green",
            "lattice-green",
            "unreal-green",
            "unity-green",
            "godot-green",
        ),
        notes=(
            "Overall green is host-tempered: it should reflect what this host can honestly prove.",
            "Release packaging is intentionally separate in release-green.",
        ),
    ),
    "release-ready": ShardSpec(
        name="release-ready",
        description="Aggregate credential-free release gate.",
        children=("overall-green", "release-green"),
        notes=("Use this before publishing or handing off a release candidate.",),
    ),
}


def shard_names() -> list[str]:
    return sorted(SHARDS)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    return env


def resolve_steps(shard_name: str, seen: set[str] | None = None) -> list[tuple[str, StepSpec]]:
    if shard_name not in SHARDS:
        raise KeyError(f"unknown shard: {shard_name}")
    seen = set() if seen is None else seen
    if shard_name in seen:
        return []
    seen.add(shard_name)
    shard = SHARDS[shard_name]
    rows: list[tuple[str, StepSpec]] = []
    for child in shard.children:
        rows.extend(resolve_steps(child, seen))
    rows.extend((shard_name, step) for step in shard.commands)
    return rows


def shard_summary(name: str) -> dict[str, object]:
    shard = SHARDS[name]
    return {
        "name": shard.name,
        "description": shard.description,
        "host_scope": shard.host_scope,
        "notes": list(shard.notes),
        "children": list(shard.children),
        "command_count": len(resolve_steps(name)),
    }


def run_step(shard_name: str, step: StepSpec) -> dict[str, object]:
    print(f"\n== {shard_name}: {step.label} ==")
    print("+", " ".join(step.command))
    started = time.monotonic()
    completed = subprocess.run(list(step.command), cwd=ROOT, env=_env(), text=True)
    elapsed = round(time.monotonic() - started, 3)
    status = "pass" if completed.returncode == 0 else ("fail" if step.required else "warn")
    print(f"[{status}] {shard_name}: {step.label} ({elapsed}s)")
    return {
        "shard": shard_name,
        "label": step.label,
        "command": list(step.command),
        "required": step.required,
        "returncode": completed.returncode,
        "status": status,
        "elapsed_seconds": elapsed,
    }


def write_report(path: Path, selected: list[str], results: list[dict[str, object]]) -> None:
    payload = {
        "schema": "fastdis.test_shards_report.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "selected_shards": selected,
        "host": asdict(host_facts()),
        "overall_status": "pass" if all(row["status"] != "fail" for row in results) else "fail",
        "results": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nreport: {path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available shards")
    list_parser.add_argument("--format", choices=("text", "json"), default="text")

    host_parser = subparsers.add_parser("host", help="Describe current host shard capabilities")
    host_parser.add_argument("--format", choices=("text", "json"), default="text")

    run_parser = subparsers.add_parser("run", help="Run one or more shards")
    run_parser.add_argument("shards", nargs="+", choices=shard_names())
    run_parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    return parser.parse_args(argv)


def command_list(fmt: str) -> int:
    payload = [shard_summary(name) for name in shard_names()]
    if fmt == "json":
        print(json.dumps(payload, indent=2))
        return 0
    for row in payload:
        print(f"{row['name']}: {row['description']}")
        if row["children"]:
            print(f"  children: {', '.join(row['children'])}")
        print(f"  commands: {row['command_count']}")
    return 0


def command_host(fmt: str) -> int:
    payload = asdict(host_facts())
    if fmt == "json":
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


def command_run(shards: list[str], report_path: str) -> int:
    selected = list(dict.fromkeys(shards))
    results: list[dict[str, object]] = []
    for shard_name in selected:
        for resolved_shard, step in resolve_steps(shard_name):
            results.append(run_step(resolved_shard, step))
    write_report(Path(report_path).expanduser().resolve(), selected, results)
    failures = [row for row in results if row["status"] == "fail"]
    if failures:
        print("\nfailed lanes:")
        for row in failures:
            print(f"  - {row['shard']}: {row['label']}")
        return 1
    print("\nselected shards passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "list":
        return command_list(args.format)
    if args.command == "host":
        return command_host(args.format)
    if args.command == "run":
        return command_run(args.shards, args.report_path)
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
