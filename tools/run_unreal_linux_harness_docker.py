#!/usr/bin/env python3
"""Run the Unreal Linux live-harness lanes inside Docker from a non-Linux host."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

import build_unreal_linux_package_docker as docker_build


ROOT = docker_build.ROOT
DEFAULT_PROFILE = ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue57.env"
MODE_TO_TOOL = {
    "verify": "tools/run_unreal_orientation_verification.py",
    "demo": "tools/run_unreal_demo_smoke.py",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("verify", "demo"), required=True)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--engine-version", help="Versioned Unreal env selector, for example 5.7 or 5.8")
    parser.add_argument("--engine-archive", help="Override the Unreal Linux zip archive path")
    parser.add_argument("--engine-path", help="Override the unpacked Unreal Linux engine directory")
    parser.add_argument("--image", help="Override the Docker image")
    parser.add_argument("--engine-stage-dir", type=Path, help="Override the staged engine directory")
    parser.add_argument("--json-out", type=Path, help="Override the JSON report output path")
    parser.add_argument("--md-out", type=Path, help="Override the Markdown report output path")
    parser.add_argument("--force-reextract", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Delegate a dry-run harness execution inside the Linux Docker route")
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Bound the Docker harness execution time")
    return parser.parse_args(argv)


def default_output_path(mode: str, suffix: str) -> Path:
    filename = f"fastdis_unreal_linux_{mode}.{suffix}"
    return ROOT / "verification_reports" / "unreal_fastdis_baseline" / filename


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    profile_path = args.profile.expanduser().resolve()
    values = dict(os.environ)
    values.update(docker_build.parse_env_file(profile_path))
    image = args.image or values.get("UE_LINUX_IMAGE") or docker_build.DEFAULT_IMAGE
    version_label = values.get("UE_VERSION_LABEL", "ue-linux")
    proof_profile = values.get("UE_PROOF_PROFILE", "default")
    safe_label = f"{docker_build.sanitize_label(version_label)}_{docker_build.sanitize_label(proof_profile)}"
    engine_stage_dir = args.engine_stage_dir or docker_build.resolve_path(
        values.get("HOST_ENGINE_STAGE_DIR", f".build/linux_unreal_engine/{docker_build.sanitize_label(version_label)}"),
        base=ROOT,
    )
    engine_path_raw = args.engine_path or values.get("UE_HOST_PATH", "")
    engine_archive_raw = args.engine_archive or values.get("UE_HOST_ARCHIVE", "")
    cli_search_bases = [Path.cwd(), ROOT, profile_path.parent]
    profile_search_bases = [profile_path.parent, ROOT, Path.cwd()]
    engine_path = (
        docker_build.resolve_path_from_bases(
            engine_path_raw,
            bases=cli_search_bases if args.engine_path else profile_search_bases,
        )
        if engine_path_raw
        else None
    )
    engine_archive = (
        docker_build.resolve_path_from_bases(
            engine_archive_raw,
            bases=cli_search_bases if args.engine_archive else profile_search_bases,
        )
        if engine_archive_raw
        else None
    )
    json_out = (args.json_out or default_output_path(args.mode, "json")).expanduser().resolve()
    md_out = (args.md_out or default_output_path(args.mode, "md")).expanduser().resolve()
    return {
        "profile_path": profile_path,
        "image": image,
        "platform": values.get("DOCKER_PLATFORM", docker_build.DEFAULT_PLATFORM),
        "ue_root_in_container": values.get("UE_ROOT_IN_CONTAINER", docker_build.DEFAULT_UE_ROOT),
        "version_label": version_label,
        "proof_profile": proof_profile,
        "safe_label": safe_label,
        "engine_stage_dir": engine_stage_dir.resolve(),
        "engine_path": engine_path,
        "engine_archive": engine_archive,
        "force_reextract": args.force_reextract,
        "json_out": json_out,
        "md_out": md_out,
        "mode": args.mode,
        "engine_version": args.engine_version,
        "dry_run": args.dry_run,
        "timeout_seconds": args.timeout_seconds,
    }


def build_inner_script(config: dict[str, Any], *, archive_present: bool, extract_archive: bool) -> str:
    ue_root = config["ue_root_in_container"]
    lines = ["set -euo pipefail"]
    lines.extend(
        [
            "if ! command -v cmake >/dev/null 2>&1; then",
            "  if command -v apt-get >/dev/null 2>&1; then",
            "    export DEBIAN_FRONTEND=noninteractive",
            "    apt-get update",
            "    apt-get install -y cmake build-essential python3",
            "  else",
            "    echo 'cmake is required inside the Linux Unreal container' >&2",
            "    exit 1",
            "  fi",
            "fi",
        ]
    )
    if archive_present and extract_archive:
        lines.extend(
            [
                f'mkdir -p "{ue_root}"',
                "python3 - <<'PY'",
                "import pathlib, shutil, zipfile",
                "archive = pathlib.Path('/tmp/linux_unreal_engine.zip')",
                f"dest = pathlib.Path({ue_root!r})",
                "for child in list(dest.iterdir()):",
                "    if child.is_dir() and not child.is_symlink():",
                "        shutil.rmtree(child)",
                "    else:",
                "        child.unlink()",
                "with zipfile.ZipFile(archive) as zf:",
                "    zf.extractall(dest)",
                "PY",
            ]
        )
    lines.extend(
        [
            "python3 - <<'PY'",
            "from pathlib import Path",
            f"root = Path({ue_root!r})",
            "def mark_executable(path: Path) -> None:",
            "    try:",
            "        with path.open('rb') as handle:",
            "            head = handle.read(4)",
            "    except OSError:",
            "        return",
            "    if head.startswith(b'#!') or head == b'\\x7fELF':",
            "        path.chmod(path.stat().st_mode | 0o111)",
            "for rel in ['Engine/Build/BatchFiles', 'Engine/Binaries', 'Engine/Extras/ThirdPartyNotUE/SDKs']:",
            "    base = root / rel",
            "    if not base.exists():",
            "        continue",
            "    for path in base.rglob('*'):",
            "        if path.is_file():",
            "            mark_executable(path)",
            "PY",
            "python3 - <<'PY'",
            "from pathlib import Path",
            f"root = Path({ue_root!r})",
            "required = [",
            "    'Engine/Build/BatchFiles/RunUAT.sh',",
            "    'Engine/Binaries/Linux/UnrealEditor',",
            "    'Engine/Build/Build.version',",
            "]",
            "missing = [item for item in required if not (root / item).exists()]",
            "if missing:",
            "    raise SystemExit('missing Unreal engine payload entries: ' + ', '.join(missing))",
            "PY",
            f'export FASTDIS_UNREAL_ENGINE_DIR="{ue_root}"',
            f'export FASTDIS_UNREAL_EDITOR="{ue_root}/Engine/Binaries/Linux/UnrealEditor"',
            'export FASTDIS_UNREAL_WORK_ROOT="/tmp/fastdis_unreal"',
            'export HOME="/tmp/fastdis_unreal/home"',
            'export XDG_CONFIG_HOME="/tmp/fastdis_unreal/home/.config"',
            'export XDG_CACHE_HOME="/tmp/fastdis_unreal/home/.cache"',
            'export XDG_DATA_HOME="/tmp/fastdis_unreal/home/.local/share"',
            'mkdir -p "/tmp/fastdis_unreal/home/.config" "/tmp/fastdis_unreal/home/.cache" "/tmp/fastdis_unreal/home/.local/share" "/tmp/fastdis_unreal/home/.epic"',
            'mkdir -p "/host_reports"',
            'cd "/src"',
        ]
    )
    cmd = ["python3", "tools/run_unreal_linux_harness.py", "--mode", config["mode"]]
    if config["engine_version"]:
        cmd.extend(["--engine-version", config["engine_version"]])
    cmd.extend(
        [
            "--json-out",
            f"/host_reports/{config['json_out'].name}",
            "--md-out",
            f"/host_reports/{config['md_out'].name}",
        ]
    )
    if config["dry_run"]:
        cmd.append("--dry-run")
    if not config["dry_run"] and config["timeout_seconds"] > 0:
        cmd = ["timeout", "--signal=INT", str(config["timeout_seconds"]), *cmd]
    lines.append(" ".join(shlex.quote(part) for part in cmd))
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Unreal Linux {str(report['mode']).title()} Harness",
        "",
        f"- lane: `{report['lane']}`",
        f"- status: `{report['status']}`",
        f"- host_platform: `{report['host']['platform_name']}`",
        f"- machine: `{report['host']['machine']}`",
        f"- target_platform: `{report['target_platform']}`",
        f"- engine_version: `{report.get('engine_version') or 'default'}`",
        f"- executed: `{report['executed']}`",
        f"- exit_code: `{report['exit_code']}`",
        "",
        str(report["claim_boundary"]),
        "",
        "## Delegated Command",
        "",
        f"- runner: `{report['runner']}`",
        f"- command: `{report['command_display']}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = report.get("blockers") or []
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    work_dir = report.get("work_dir")
    if work_dir:
        lines.extend(["", "## Work Dir", "", f"- `{work_dir}`"])
    lines.append("")
    return "\n".join(lines)


def write_report(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    path_md.write_text(render_markdown(payload), encoding="utf-8")


def classify_partial_failure(mode: str, work_root: Path, exit_code: int) -> tuple[str, list[str]]:
    blockers = [f"inner docker harness returned {exit_code}"]
    status = "timeout" if exit_code == 124 else "fail"
    if mode == "demo":
        log_path = work_root / "logs" / "demo" / "FastDisDemoSmoke.log"
        if log_path.is_file():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if "Custom version is too new" in text and "FastDis_Demo.umap" in text:
                status = "fail"
                blockers.append(
                    "FastDis_Demo.umap was saved with a newer Unreal custom version than UE 5.7 can load; "
                    "rerun this lane with a 5.8-compatible engine or resave the demo content for 5.7."
                )
    return status, blockers


def run_capture(config: dict[str, Any]) -> int:
    docker_build.docker_preflight(config["image"], config["platform"])

    archive_present = config["engine_archive"] is not None
    extract_archive = False
    if config["engine_path"] is not None:
        mount_engine_source = config["engine_path"]
    elif config["engine_archive"] is not None:
        mount_engine_source = config["engine_stage_dir"]
        mount_engine_source.mkdir(parents=True, exist_ok=True)
        extract_archive = docker_build.should_extract(
            config["engine_stage_dir"], config["engine_archive"], bool(config["force_reextract"])
        )
    else:
        raise SystemExit("Provide --engine-path or --engine-archive, or set UE_HOST_PATH/UE_HOST_ARCHIVE in the profile.")

    config["json_out"].parent.mkdir(parents=True, exist_ok=True)
    config["md_out"].parent.mkdir(parents=True, exist_ok=True)
    work_root = config["json_out"].parent / "linux_harness_work" / config["mode"]
    work_root.mkdir(parents=True, exist_ok=True)
    if config["json_out"].exists():
        config["json_out"].unlink()
    if config["md_out"].exists():
        config["md_out"].unlink()

    command = [
        "docker",
        "run",
        "--rm",
        "--platform",
        config["platform"],
        "-v",
        f"{ROOT}:/src",
        "-v",
        f"{mount_engine_source}:{config['ue_root_in_container']}",
        "-v",
        f"{config['json_out'].parent}:/host_reports",
        "-v",
        f"{work_root}:/tmp/fastdis_unreal",
    ]
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        command.extend(["--user", f"{os.getuid()}:{os.getgid()}"])
    if archive_present and config["engine_archive"] is not None:
        command.extend(["-v", f"{config['engine_archive']}:/tmp/linux_unreal_engine.zip:ro"])
    command.extend(
        [
            config["image"],
            "bash",
            "-lc",
            build_inner_script(config, archive_present=archive_present, extract_archive=extract_archive),
        ]
    )
    completed = subprocess.run(command, cwd=ROOT)
    if not config["json_out"].exists():
        status, blockers = classify_partial_failure(config["mode"], work_root, completed.returncode)
        payload = {
            "schema": "fastdis.unreal_linux_harness_lane.v1",
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "lane": f"linux-{config['mode']}",
            "mode": config["mode"],
            "status": status,
            "claim_boundary": (
                "Linux Docker harness execution only. This artifact proves the selected Unreal Linux harness lane "
                "was attempted inside the Docker-based Linux route, but the inner harness did not complete cleanly."
            ),
            "host": {
                "platform_system": "Linux",
                "platform_name": "linux",
                "machine": "x86_64",
            },
            "target_platform": "linux",
            "engine_version": config["engine_version"],
            "executed": True,
            "exit_code": completed.returncode,
            "runner": MODE_TO_TOOL[config["mode"]],
            "command": command,
            "command_display": " ".join(str(part) for part in command),
            "blockers": [*blockers, f"inspect mounted work dir for partial Unreal logs and intermediates: {work_root}"],
            "work_dir": str(work_root),
        }
        write_report(config["json_out"], config["md_out"], payload)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_capture(build_config(args))


if __name__ == "__main__":
    raise SystemExit(main())
