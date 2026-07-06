#!/usr/bin/env python3
"""Run the Cesium Unreal vendor-plugin lane inside a Linux Docker proof container."""

from __future__ import annotations

import argparse
from collections import deque
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import shlex
import subprocess
import threading
import time
from typing import Any

from artifacts import PRESERVED_ARTIFACTS_DIR
import build_unreal_linux_package_docker as docker_build
import preserve_artifact_snapshot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VENDOR = "cesium"
DEFAULT_ENGINE_VERSION = "5.8"
DEFAULT_BASELINE_VERSION = "5.7"
DEFAULT_PROFILE = ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue58.env"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "unreal_vendor_plugin"
DEFAULT_MANIFEST_DIR = ROOT / "artifacts" / "manifests" / "unreal_vendor_plugin"
DEFAULT_IMAGE = "fastdis-linux-proof:ubuntu24.04"
DEFAULT_PLATFORM = "linux/amd64"
DEFAULT_DOCKER_USER = "1000:1000"
DEFAULT_CONTAINER_NAME_PREFIX = "packet-stoat-unreal-linux-proof"
INSTALL_SMOKE_PROJECT_NAME = "CesiumForUnrealInstallSmoke"


def _version_slug(version: str) -> str:
    return version.replace(".", "_")


def default_json_out(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker.json"


def default_md_out(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker.md"


def default_handoff_json(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_handoff.json"


def default_handoff_md(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_handoff.md"


def default_build_json(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_build.json"


def default_build_md(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_build.md"


def default_install_json(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_install_smoke.json"


def default_install_md(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_install_smoke.md"


def default_progress_json(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_progress.json"


def default_progress_md(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_progress.md"


def default_progress_events(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_progress.jsonl"


def default_inner_log(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_inner.log"


def default_docker_log(version: str) -> Path:
    return DEFAULT_REPORT_DIR / f"cesium_{_version_slug(version)}_linux_docker_stdout.log"


def default_package_dir(version: str) -> Path:
    return ROOT / "build" / "unreal_vendor_plugins" / "cesium" / f"linux_docker_{_version_slug(version)}" / "CesiumForUnreal"


def default_project_dir(version: str) -> Path:
    return ROOT / "artifacts" / "scratch" / "unreal_vendor_plugin" / f"cesium_{_version_slug(version)}_linux_docker_project"


def default_lane_manifest_json(version: str) -> Path:
    return DEFAULT_MANIFEST_DIR / f"cesium_{_version_slug(version)}_linux_docker_lane_manifest.json"


def default_lane_manifest_md(version: str) -> Path:
    return DEFAULT_MANIFEST_DIR / f"cesium_{_version_slug(version)}_linux_docker_lane_manifest.md"


def _default_repo_staged_engine_dir(version_label: str) -> Path:
    return ROOT / "artifacts" / "staging" / "unreal" / "linux" / docker_build.sanitize_label(version_label)


def discover_engine_compiler_dir(engine_root: Path) -> Path | None:
    host_linux = engine_root / "Engine" / "Extras" / "ThirdPartyNotUE" / "SDKs" / "HostLinux" / "Linux_x64"
    if not host_linux.is_dir():
        return None
    candidates: list[Path] = []
    for toolchain_root in sorted(host_linux.iterdir()):
        candidate = toolchain_root / "x86_64-unknown-linux-gnu"
        if (candidate / "bin" / "clang").is_file() and (candidate / "bin" / "clang++").is_file():
            candidates.append(candidate.resolve())
    return candidates[-1] if candidates else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", default=DEFAULT_VENDOR)
    parser.add_argument("--engine-version", default=DEFAULT_ENGINE_VERSION)
    parser.add_argument("--baseline-version", default=DEFAULT_BASELINE_VERSION)
    parser.add_argument("--plugin-root", default="external/cesium/cesium-unreal")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--image", default="", help="Override Docker image; defaults to the selected profile value")
    parser.add_argument("--platform", default="", help="Override Docker platform; defaults to the selected profile value")
    parser.add_argument("--engine-archive", help="Override the Linux Unreal engine archive path")
    parser.add_argument("--engine-path", help="Override the unpacked Linux Unreal engine directory")
    parser.add_argument("--engine-stage-dir", type=Path, help="Override the staged Linux Unreal engine directory")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    parser.add_argument("--handoff-json-out", type=Path)
    parser.add_argument("--handoff-md-out", type=Path)
    parser.add_argument("--build-json-out", type=Path)
    parser.add_argument("--build-md-out", type=Path)
    parser.add_argument("--install-json-out", type=Path)
    parser.add_argument("--install-md-out", type=Path)
    parser.add_argument("--progress-json-out", type=Path)
    parser.add_argument("--progress-md-out", type=Path)
    parser.add_argument("--progress-events-out", type=Path)
    parser.add_argument("--inner-log-out", type=Path)
    parser.add_argument("--docker-log-out", type=Path)
    parser.add_argument("--package-dir", type=Path)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--lane-manifest-json-out", type=Path)
    parser.add_argument("--lane-manifest-md-out", type=Path)
    parser.add_argument("--target-platforms", default="Linux")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--docker-log-mode", choices=("capture", "tee"), default="tee")
    parser.add_argument("--log-tail-lines", type=int, default=80)
    parser.add_argument("--container-name")
    parser.add_argument("--preserve", action="store_true")
    parser.add_argument("--preserve-label", default="unreal-linux-docker")
    parser.add_argument("--preserve-root", type=Path, default=PRESERVED_ARTIFACTS_DIR)
    parser.add_argument("--force-reextract", action="store_true")
    parser.add_argument("--inner-dry-run", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def resolved_container_name(args: argparse.Namespace) -> str:
    return args.container_name or f"{DEFAULT_CONTAINER_NAME_PREFIX}-{os.getpid()}"


def output_paths(args: argparse.Namespace) -> dict[str, Path]:
    version = args.engine_version
    return {
        "json_out": (args.json_out or default_json_out(version)).expanduser().resolve(),
        "md_out": (args.md_out or default_md_out(version)).expanduser().resolve(),
        "handoff_json": (args.handoff_json_out or default_handoff_json(version)).expanduser().resolve(),
        "handoff_md": (args.handoff_md_out or default_handoff_md(version)).expanduser().resolve(),
        "build_json": (args.build_json_out or default_build_json(version)).expanduser().resolve(),
        "build_md": (args.build_md_out or default_build_md(version)).expanduser().resolve(),
        "install_json": (args.install_json_out or default_install_json(version)).expanduser().resolve(),
        "install_md": (args.install_md_out or default_install_md(version)).expanduser().resolve(),
        "progress_json": (args.progress_json_out or default_progress_json(version)).expanduser().resolve(),
        "progress_md": (args.progress_md_out or default_progress_md(version)).expanduser().resolve(),
        "progress_events": (args.progress_events_out or default_progress_events(version)).expanduser().resolve(),
        "inner_log": (args.inner_log_out or default_inner_log(version)).expanduser().resolve(),
        "docker_log": (args.docker_log_out or default_docker_log(version)).expanduser().resolve(),
        "package_dir": (args.package_dir or default_package_dir(version)).expanduser().resolve(),
        "project_dir": (args.project_dir or default_project_dir(version)).expanduser().resolve(),
        "lane_manifest_json": (args.lane_manifest_json_out or default_lane_manifest_json(version)).expanduser().resolve(),
        "lane_manifest_md": (args.lane_manifest_md_out or default_lane_manifest_md(version)).expanduser().resolve(),
    }


def _container_repo_path(path: Path) -> str:
    relative = path.resolve().relative_to(ROOT)
    return "/src/" + relative.as_posix()


def _container_parent_mkdir_commands(*paths: Path) -> list[str]:
    seen: set[str] = set()
    commands: list[str] = []
    for path in paths:
        parent = _container_repo_path(path.parent)
        if parent in seen:
            continue
        seen.add(parent)
        commands.append(f'mkdir -p "{parent}"')
    return commands


def _tail(text: str, lines: int) -> list[str]:
    rows = [row for row in text.splitlines() if row.strip()]
    return rows[-max(1, lines):]


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _file_fact(path: Path | None, *, include_sha256: bool = False) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        stat = path.stat()
    except OSError:
        return {"path": str(path), "exists": False}
    fact: dict[str, Any] = {
        "path": str(path),
        "exists": True,
        "size": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
    }
    if include_sha256 and path.is_file():
        fact["sha256"] = _sha256_file(path)
    return fact


def _git_rev_parse(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = (result.stdout or "").strip()
    return value or None


def _docker_image_digest(image: str) -> str | None:
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
            text=True,
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = (result.stdout or "").strip()
    return value or None


def cleanup_container(container_name: str) -> None:
    try:
        subprocess.run(["docker", "rm", "-f", container_name], text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        pass


def docker_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(["docker", "info"], text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    detail = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, detail.splitlines()[0] if detail else f"returncode={result.returncode}"


def image_available(image: str) -> bool:
    try:
        result = subprocess.run(["docker", "image", "inspect", image], text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    profile_path = args.profile.expanduser().resolve()
    values = dict(os.environ)
    values.update(docker_build.parse_env_file(profile_path))
    discovered_inputs = docker_build.discover_linux_engine_inputs()
    selected_input = docker_build.select_linux_engine_input(args.engine_version, discovered_inputs)
    image = args.image or values.get("UE_LINUX_IMAGE") or DEFAULT_IMAGE
    platform = args.platform or values.get("DOCKER_PLATFORM") or DEFAULT_PLATFORM
    version_label = (
        str(selected_input.get("version_label") or "")
        if selected_input is not None
        else (values.get("UE_VERSION_LABEL") or f"ue{args.engine_version}-linux")
    )
    engine_stage_dir_value = args.engine_stage_dir or docker_build.resolve_path(
        values.get("HOST_ENGINE_STAGE_DIR", "") or f"artifacts/staging/unreal/linux/{docker_build.sanitize_label(version_label)}",
        base=ROOT,
    )
    cli_search_bases = [Path.cwd(), ROOT, profile_path.parent]
    profile_search_bases = [profile_path.parent, ROOT, Path.cwd()]
    engine_path_raw = args.engine_path or values.get("UE_HOST_PATH", "")
    engine_archive_raw = args.engine_archive or values.get("UE_HOST_ARCHIVE", "")
    engine_path = (
        docker_build.resolve_path_from_bases(
            engine_path_raw,
            bases=cli_search_bases if args.engine_path else profile_search_bases,
        )
        if engine_path_raw
        else Path(selected_input["engine_path"]).resolve() if selected_input and selected_input.get("engine_path") else None
    )
    engine_archive = (
        docker_build.resolve_path_from_bases(
            engine_archive_raw,
            bases=cli_search_bases if args.engine_archive else profile_search_bases,
        )
        if engine_archive_raw
        else Path(selected_input["archive_path"]).resolve() if selected_input and selected_input.get("archive_path") else None
    )
    stage_engine_path = engine_stage_dir_value.resolve()
    repo_staged_engine_path = _default_repo_staged_engine_dir(version_label).resolve()
    if engine_path is None and docker_build.engine_is_valid(stage_engine_path):
        engine_path = stage_engine_path
    if engine_path is not None and discover_engine_compiler_dir(engine_path) is None:
        if docker_build.engine_is_valid(repo_staged_engine_path) and discover_engine_compiler_dir(repo_staged_engine_path) is not None:
            engine_path = repo_staged_engine_path
    compiler_dir = discover_engine_compiler_dir(engine_path) if engine_path is not None else None
    return {
        "profile_path": profile_path,
        "image": image,
        "platform": platform,
        "docker_user": values.get("DOCKER_USER") or DEFAULT_DOCKER_USER,
        "ue_root_in_container": values.get("UE_ROOT_IN_CONTAINER", docker_build.DEFAULT_UE_ROOT),
        "version_label": version_label,
        "proof_profile": values.get("UE_PROOF_PROFILE", "default"),
        "engine_path": engine_path,
        "engine_archive": engine_archive,
        "engine_stage_dir": engine_stage_dir_value.resolve(),
        "repo_staged_engine_dir": repo_staged_engine_path,
        "engine_compiler_dir": compiler_dir,
        "engine_source_mode": "stage-dir" if engine_path == stage_engine_path else ("engine-path" if engine_path is not None else "archive"),
        "force_reextract": bool(args.force_reextract),
        "selected_input": selected_input,
        "discovered_inputs": discovered_inputs,
        "search_roots": [path.resolve() for path in docker_build.default_linux_engine_search_roots()],
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(inner) for inner in value]
    return value


def _mark_executables_script(ue_root: str) -> list[str]:
    return [
        "echo '[bootstrap] normalizing executable bits in staged Unreal tree'",
        "python3 - <<'PY'",
        "from pathlib import Path",
        f"root = Path({ue_root!r})",
        "stamp = root / '.packet_stoat_exec_ready'",
        "if stamp.exists():",
        "    print('[bootstrap] executable normalization already stamped; skipping')",
        "    raise SystemExit(0)",
        "def mark_exec(path: Path) -> None:",
        "    try:",
        "        path.chmod(path.stat().st_mode | 0o111)",
        "    except OSError:",
        "        return",
        "def iter_candidates(base: Path, *, mode: str):",
        "    if not base.exists():",
        "        return",
        "    for path in base.rglob('*'):",
        "        if not path.is_file():",
        "            continue",
        "        suffixes = {suffix.lower() for suffix in path.suffixes}",
        "        suffix = path.suffix.lower()",
        "        if mode == 'scripts':",
        "            if suffix in {'.sh', '.command', '.py', '.pl'}:",
        "                yield path",
        "        elif mode == 'linux-binaries':",
        "            if suffix == '' or '.so' in suffixes:",
        "                yield path",
        "        elif mode == 'toolchain-binaries':",
        "            if path.parent.name in {'bin', 'libexec'} or suffix in {'.sh', '.py'}:",
        "                yield path",
        "phases = [",
        "    ('batchfiles', root / 'Engine/Build/BatchFiles', 'scripts'),",
        "    ('linux-binaries', root / 'Engine/Binaries/Linux', 'linux-binaries'),",
        "    ('hostlinux-sdk', root / 'Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux', 'toolchain-binaries'),",
        "]",
        "total = 0",
        "for label, base, mode in phases:",
        "    print(f'[bootstrap] normalization phase {label}: scanning {base}')",
        "    phase_count = 0",
        "    for phase_count, path in enumerate(iter_candidates(base, mode=mode), start=1):",
        "        mark_exec(path)",
        "        if phase_count % 250 == 0:",
        "            print(f'[bootstrap] normalization phase {label}: marked {phase_count}')",
        "    print(f'[bootstrap] normalization phase {label}: done marked={phase_count}')",
        "    total += phase_count",
        "stamp.write_text('ok\\n', encoding='utf-8')",
        "print(f'[bootstrap] marked executable candidates: {total}')",
        "PY",
        "echo '[bootstrap] executable normalization complete'",
    ]


def build_inner_command(args: argparse.Namespace, config: dict[str, Any], paths: dict[str, Path], *, archive_present: bool, extract_archive: bool) -> str:
    ue_root = config["ue_root_in_container"]
    plugin_root = args.plugin_root.strip("/").replace("\\", "/")
    container_project_dir = f"{ue_root}/{INSTALL_SMOKE_PROJECT_NAME}"
    scratch_root = "/tmp/packet_stoat_cesium_unreal"
    scratch_plugin = f"{scratch_root}/plugin"
    scratch_inner_log = f"{scratch_root}/inner.log"
    host_inner_log = _container_repo_path(paths["inner_log"])
    version_env_suffix = _version_slug(args.engine_version)
    compiler_dir = config.get("engine_compiler_dir")
    compiler_dir_container = None
    if isinstance(compiler_dir, Path):
        try:
            compiler_dir_container = "/opt/unreal-engine/" + compiler_dir.resolve().relative_to(Path(config["engine_path"]).resolve()).as_posix()
        except Exception:
            compiler_dir_container = None
    lines = [
        "set -euo pipefail",
        "echo '[bootstrap] container started'",
        "if ! command -v cmake >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1 || ! command -v zip >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1 || ! command -v ninja >/dev/null 2>&1 || ! command -v pkg-config >/dev/null 2>&1; then",
        "  if command -v apt-get >/dev/null 2>&1; then",
        "    echo '[bootstrap] installing cmake/build prerequisites inside container'",
        "    export DEBIAN_FRONTEND=noninteractive",
        "    apt-get update",
        "    apt-get install -y cmake build-essential python3 rsync curl zip unzip tar git ninja-build pkg-config",
        "  else",
        "    echo 'cmake is required inside the Linux Unreal container' >&2",
        "    exit 1",
        "  fi",
        "fi",
        "if ! python3 -c \"import yaml\" >/dev/null 2>&1; then",
        "  if command -v apt-get >/dev/null 2>&1; then",
        "    echo '[bootstrap] installing python3-yaml inside container'",
        "    export DEBIAN_FRONTEND=noninteractive",
        "    apt-get update",
        "    apt-get install -y python3-yaml",
        "  else",
        "    echo 'python3-yaml is required inside the Linux Unreal container' >&2",
        "    exit 1",
        "  fi",
        "fi",
    ]
    if archive_present and extract_archive:
        lines.extend(
            [
                "echo '[bootstrap] extracting Linux Unreal archive into staged engine dir'",
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
    lines.extend(_mark_executables_script(ue_root))
    lines.extend(
        [
            "echo '[bootstrap] validating required Unreal engine payload entries'",
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
            f'export FASTDIS_UNREAL_ENGINE_DIR_{version_env_suffix}="{ue_root}"',
            f'export FASTDIS_UNREAL_EDITOR="{ue_root}/Engine/Binaries/Linux/UnrealEditor"',
            f'export FASTDIS_UNREAL_EDITOR_{version_env_suffix}="{ue_root}/Engine/Binaries/Linux/UnrealEditor"',
            f'export FASTDIS_UNREAL_ROOTS="{ue_root}"',
            *( [f'export UNREAL_ENGINE_ROOT="{ue_root}"', f'export UNREAL_ENGINE_DIR="{ue_root}"'] ),
            f'export FASTDIS_UNREAL_WORK_ROOT="{scratch_root}/work"',
            f'export HOME="{scratch_root}/home"',
            f'export XDG_CONFIG_HOME="{scratch_root}/home/.config"',
            f'export XDG_CACHE_HOME="{scratch_root}/home/.cache"',
            f'export XDG_DATA_HOME="{scratch_root}/home/.local/share"',
            'export PKG_CONFIG="/usr/bin/pkg-config"',
            'export PKG_CONFIG_EXECUTABLE="/usr/bin/pkg-config"',
            'export PKGCONFIG="/usr/bin/pkg-config"',
            'export CMAKE_PROGRAM_PATH="/usr/bin${CMAKE_PROGRAM_PATH:+:$CMAKE_PROGRAM_PATH}"',
            f'mkdir -p "{scratch_root}/home/.config" "{scratch_root}/home/.cache" "{scratch_root}/home/.local/share"',
            "echo '[bootstrap] copying Cesium Unreal plugin into container scratch'",
            f'rm -rf "{scratch_plugin}"',
            f'mkdir -p "{scratch_root}"',
            f'rsync -a --delete '
            f'--exclude ".git/" '
            f'--exclude ".github/" '
            f'--exclude ".concierge/" '
            f'--exclude "Documentation/" '
            f'--exclude "travis/" '
            f'--exclude "TestsProject/" '
            f'--exclude "node_modules/" '
            f'--exclude "extern/build-fastdis/" '
            f'"/src/{plugin_root}/" "{scratch_plugin}/"',
            'cd "/src"',
        ]
    )
    lines.extend(
        _container_parent_mkdir_commands(
            paths["inner_log"],
            paths["docker_log"],
            paths["handoff_json"],
            paths["handoff_md"],
            paths["build_json"],
            paths["build_md"],
            paths["install_json"],
            paths["install_md"],
            paths["progress_json"],
            paths["progress_md"],
            paths["progress_events"],
            paths["package_dir"],
            paths["project_dir"],
        )
    )
    if compiler_dir_container:
        lines.insert(lines.index(f'export FASTDIS_UNREAL_WORK_ROOT="{scratch_root}/work"'), f'export UNREAL_ENGINE_COMPILER_DIR="{compiler_dir_container}"')
        lines.insert(lines.index(f'export FASTDIS_UNREAL_WORK_ROOT="{scratch_root}/work"'), "echo '[bootstrap] exporting Unreal Linux compiler dir'")
    prepare_cmd = [
        "python3",
        "tools/unreal_vendor_workflow.py",
        "prepare-source",
        "--vendor",
        args.vendor,
        "--engine-version",
        args.engine_version,
        "--plugin-root",
        scratch_plugin,
        "--clean-build",
    ]
    handoff_cmd = [
        "python3",
        "tools/unreal_vendor_workflow.py",
        "handoff",
        "--vendor",
        args.vendor,
        "--engine-version",
        args.engine_version,
        "--baseline-version",
        args.baseline_version,
        "--plugin-root",
        scratch_plugin,
        "--target-platforms",
        args.target_platforms,
        "--clean-package",
        "--clean-project",
        "--package-dir",
        _container_repo_path(paths["package_dir"]),
        "--project-dir",
        _container_repo_path(paths["project_dir"]),
        "--editor-project-path",
        container_project_dir,
        "--build-json-out",
        _container_repo_path(paths["build_json"]),
        "--build-md-out",
        _container_repo_path(paths["build_md"]),
        "--install-json-out",
        _container_repo_path(paths["install_json"]),
        "--install-md-out",
        _container_repo_path(paths["install_md"]),
        "--json-out",
        _container_repo_path(paths["handoff_json"]),
        "--md-out",
        _container_repo_path(paths["handoff_md"]),
    ]
    if args.inner_dry_run:
        handoff_cmd.append("--dry-run")
    lines.append("echo '[bootstrap] starting Cesium Unreal prepare-source'")
    lines.append(f'rm -f "{scratch_inner_log}"')
    lines.append(" ".join(shlex.quote(part) for part in prepare_cmd) + f' 2>&1 | tee "{scratch_inner_log}"')
    lines.append(f'cp "{scratch_inner_log}" "{host_inner_log}"')
    lines.append("echo '[bootstrap] starting Cesium Unreal handoff'")
    lines.append(" ".join(shlex.quote(part) for part in handoff_cmd) + f' 2>&1 | tee -a "{scratch_inner_log}"')
    lines.append(f'cp "{scratch_inner_log}" "{host_inner_log}"')
    return "\n".join(lines)


def build_docker_command(args: argparse.Namespace, config: dict[str, Any], paths: dict[str, Path]) -> list[str]:
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
        search_roots = ", ".join(str(path) for path in config.get("search_roots") or []) or "none"
        raise SystemExit(
            "Provide --engine-path or --engine-archive, set UE_HOST_PATH/UE_HOST_ARCHIVE in the profile, "
            f"or place Linux Unreal downloads under one of: {search_roots}"
        )
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        resolved_container_name(args),
        "--platform",
        str(config["platform"]),
        "--user",
        str(config["docker_user"]),
        "-v",
        f"{ROOT}:/src",
        "-v",
        f"{mount_engine_source}:{config['ue_root_in_container']}",
        "-v",
        f"{paths['project_dir']}:{config['ue_root_in_container']}/{INSTALL_SMOKE_PROJECT_NAME}",
        "-w",
        "/src",
    ]
    if archive_present and config["engine_archive"] is not None:
        command.extend(["-v", f"{config['engine_archive']}:/tmp/linux_unreal_engine.zip:ro"])
    command.extend(
        [
            str(config["image"]),
            "bash",
            "-lc",
            build_inner_command(args, config, paths, archive_present=archive_present, extract_archive=extract_archive),
        ]
    )
    return command


def run_docker_command(
    command: list[str],
    *,
    log_out: Path,
    log_mode: str,
    timeout_seconds: int,
    log_tail_lines: int,
    container_name: str,
) -> tuple[int | None, list[str], list[str], str]:
    log_out.parent.mkdir(parents=True, exist_ok=True)
    if log_mode == "capture":
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            log_out.write_text(stdout + stderr, encoding="utf-8")
            cleanup_container(container_name)
            raise
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        log_out.write_text(stdout + stderr, encoding="utf-8")
        return result.returncode, _tail(stdout, log_tail_lines), _tail(stderr, log_tail_lines), stdout + "\n" + stderr

    tail: deque[str] = deque(maxlen=max(1, log_tail_lines))
    line_queue: queue.Queue[str | None] = queue.Queue()
    with log_out.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None

        def enqueue_output() -> None:
            try:
                for output_line in process.stdout:
                    line_queue.put(output_line)
            finally:
                line_queue.put(None)

        reader = threading.Thread(target=enqueue_output, daemon=True)
        reader.start()
        deadline = time.monotonic() + max(1, timeout_seconds)
        reader_done = False
        while True:
            if time.monotonic() > deadline:
                process.kill()
                cleanup_container(container_name)
                raise subprocess.TimeoutExpired(command, timeout_seconds)
            try:
                line = line_queue.get(timeout=1)
            except queue.Empty:
                if reader_done and process.poll() is not None:
                    break
                continue
            if line is None:
                reader_done = True
                if process.poll() is not None:
                    break
                continue
            log_file.write(line)
            log_file.flush()
            stripped = line.rstrip()
            if stripped:
                tail.append(stripped)
            print(line, end="", flush=True)
        return process.wait(timeout=5), list(tail), [], ""


def _path_is_fresh(path: Path, min_mtime: float) -> bool:
    try:
        return path.is_file() and path.stat().st_mtime >= min_mtime
    except OSError:
        return False


def load_json(path: Path, *, min_mtime: float | None = None) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    if min_mtime is not None and not _path_is_fresh(path, min_mtime):
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def handoff_rough_edges(inner: dict[str, Any] | None) -> list[str]:
    if not inner:
        return []
    edges: list[str] = []
    build_report = inner.get("build_report") if isinstance(inner.get("build_report"), dict) else {}
    install_report = inner.get("install_smoke_report") if isinstance(inner.get("install_smoke_report"), dict) else {}
    detail = str(build_report.get("detail") or "").strip()
    if detail:
        edges.append(detail)
    raw_output = str(build_report.get("raw_output") or "").strip()
    if raw_output:
        edges.extend(_tail(raw_output, 8))
    install_status = str(install_report.get("status") or "")
    if install_status and install_status not in {"pass", "dry-run"}:
        edges.append(f"install-smoke: {install_status}")
    log_summary = install_report.get("log_summary")
    if isinstance(log_summary, dict):
        failure_kind = str(log_summary.get("failure_kind") or "").strip()
        if failure_kind:
            edges.append(f"install-smoke failure_kind: {failure_kind}")
        summary_text = str(log_summary.get("summary") or "").strip()
        if summary_text:
            edges.append(summary_text)
    deduped: list[str] = []
    seen: set[str] = set()
    for edge in edges:
        text = edge.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def classify(payload: dict[str, Any], output: str, inner: dict[str, Any] | None) -> str:
    inner_failure = str(inner.get("failure_class") or "") if inner else ""
    if inner_failure:
        return inner_failure
    lowered = output.lower()
    if "no such image" in lowered or "unable to find image" in lowered:
        return "container-image-missing"
    if "missing unreal engine payload entries" in lowered:
        return "engine-missing"
    if "cmake is required inside the linux unreal container" in lowered:
        return "toolchain-missing"
    if "error c" in lowered or "fatal error" in lowered or "undefined reference" in lowered or "not a valid platform to build" in lowered:
        return "compile-or-link"
    return "docker-lane-failed" if payload.get("returncode") else "dry-run"


def clear_reused_report_paths(paths: dict[str, Path]) -> list[str]:
    cleared: list[str] = []
    for key in (
        "handoff_json",
        "handoff_md",
        "build_json",
        "build_md",
        "install_json",
        "install_md",
        "progress_json",
        "progress_md",
        "progress_events",
        "inner_log",
        "docker_log",
    ):
        path = paths[key]
        try:
            if path.exists():
                path.unlink()
                cleared.append(str(path))
        except OSError:
            continue
    return cleared


def build_lane_manifest(args: argparse.Namespace, config: dict[str, Any], paths: dict[str, Path], command: list[str]) -> dict[str, Any]:
    plugin_root = (ROOT / args.plugin_root).resolve()
    selected_input = config.get("selected_input") if isinstance(config.get("selected_input"), dict) else {}
    engine_path = config.get("engine_path")
    build_version_path = engine_path / "Engine" / "Build" / "Build.version" if isinstance(engine_path, Path) else None
    return {
        "schema": "packet_stoat.unreal_vendor_linux_lane_manifest.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "lane": "cesium-unreal-linux-docker",
        "vendor": args.vendor,
        "engine_version": args.engine_version,
        "baseline_version": args.baseline_version,
        "target_platforms": args.target_platforms,
        "image": {
            "tag": str(config["image"]),
            "platform": str(config["platform"]),
            "repo_digest": _docker_image_digest(str(config["image"])),
        },
        "profile": _file_fact(Path(config["profile_path"]), include_sha256=True),
        "engine": {
            "source_mode": str(config.get("engine_source_mode") or ""),
            "version_label": str(config.get("version_label") or ""),
            "selected_input": _json_ready(selected_input),
            "engine_path": _file_fact(engine_path),
            "engine_archive": _file_fact(config.get("engine_archive")),
            "engine_stage_dir": _file_fact(config.get("engine_stage_dir")),
            "repo_staged_engine_dir": _file_fact(config.get("repo_staged_engine_dir")),
            "compiler_dir": _file_fact(config.get("engine_compiler_dir")),
            "build_version": _file_fact(build_version_path, include_sha256=True),
        },
        "plugin": {
            "root": str(plugin_root),
            "exists": plugin_root.exists(),
            "git_commit": _git_rev_parse(plugin_root),
        },
        "runner": {
            "script": str(Path(__file__).resolve()),
            "repo_root": str(ROOT),
            "repo_commit": _git_rev_parse(ROOT),
        },
        "artifacts": {
            "report_json": str(paths["json_out"]),
            "report_markdown": str(paths["md_out"]),
            "docker_log": str(paths["docker_log"]),
            "inner_log": str(paths["inner_log"]),
            "handoff_json": str(paths["handoff_json"]),
            "build_json": str(paths["build_json"]),
            "install_smoke_json": str(paths["install_json"]),
            "lane_manifest_json": str(paths["lane_manifest_json"]),
            "lane_manifest_markdown": str(paths["lane_manifest_md"]),
        },
        "replay": {
            "command": command,
            "command_text": " ".join(shlex.quote(part) for part in command),
        },
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    run_started_mtime = time.time()
    paths = output_paths(args)
    config = build_config(args)
    container_name = resolved_container_name(args)
    docker_ok, docker_detail = docker_available()
    command = build_docker_command(args, config, paths) if docker_ok or args.dry_run else ["docker", "run", "..."]
    lane_manifest = build_lane_manifest(args, config, paths, command)
    payload: dict[str, Any] = {
        "schema": "packet_stoat.unreal_vendor_linux_docker.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "vendor": args.vendor,
        "engine_version": args.engine_version,
        "baseline_version": args.baseline_version,
        "host": "linux-docker",
        "status": "dry-run" if args.dry_run else "pending",
        "failure_class": "dry-run" if args.dry_run else "",
        "image": str(config["image"]),
        "platform": str(config["platform"]),
        "container_name": container_name,
        "runner_pid": os.getpid(),
        "plugin_root": args.plugin_root,
        "target_platforms": args.target_platforms,
        "docker_available": docker_ok,
        "docker_detail": docker_detail,
        "image_available": image_available(str(config["image"])) if docker_ok or args.dry_run else False,
        "command": command,
        "command_text": " ".join(shlex.quote(part) for part in command),
        "claim_boundary": (
            "This Linux Docker proof covers source hydration, Unreal BuildPlugin packaging, and install-smoke "
            "execution for the Cesium Unreal plugin against a Linux Unreal editor inside Docker."
        ),
        "proof_profile": {
            "profile_path": str(config["profile_path"]),
            "version_label": str(config["version_label"]),
            "selected_input": _json_ready(config["selected_input"]),
            "engine_source_mode": str(config.get("engine_source_mode") or ""),
            "engine_stage_dir": str(config.get("engine_stage_dir") or ""),
            "repo_staged_engine_dir": str(config.get("repo_staged_engine_dir") or ""),
            "engine_compiler_dir": str(config.get("engine_compiler_dir") or ""),
        },
        "observability": {
            "docker_log_mode": args.docker_log_mode,
            "log_tail_lines": max(1, args.log_tail_lines),
            "docker_log": str(paths["docker_log"]),
            "inner_log": str(paths["inner_log"]),
        },
        "report_json": str(paths["json_out"]),
        "report_markdown": str(paths["md_out"]),
        "handoff_json": str(paths["handoff_json"]),
        "handoff_markdown": str(paths["handoff_md"]),
        "build_report_json": str(paths["build_json"]),
        "build_report_markdown": str(paths["build_md"]),
        "install_smoke_json": str(paths["install_json"]),
        "install_smoke_markdown": str(paths["install_md"]),
        "progress_json": str(paths["progress_json"]),
        "progress_markdown": str(paths["progress_md"]),
        "progress_events_jsonl": str(paths["progress_events"]),
        "inner_log": str(paths["inner_log"]),
        "docker_log": str(paths["docker_log"]),
        "lane_manifest_json": str(paths["lane_manifest_json"]),
        "lane_manifest_markdown": str(paths["lane_manifest_md"]),
        "package_dir": str(paths["package_dir"]),
        "project_dir": str(paths["project_dir"]),
        "lane_manifest": lane_manifest,
        "returncode": None,
        "stdout_tail": [],
        "stderr_tail": [],
        "rough_edges": [],
        "cleared_artifacts": [],
    }
    if args.dry_run:
        payload["rough_edges"] = ["not executed; use without --dry-run to probe the Linux Docker Unreal vendor lane"]
        return payload
    if not docker_ok:
        payload["status"] = "fail"
        payload["failure_class"] = "docker-unavailable"
        payload["rough_edges"] = [docker_detail]
        return payload

    paths["json_out"].parent.mkdir(parents=True, exist_ok=True)
    paths["md_out"].parent.mkdir(parents=True, exist_ok=True)
    paths["lane_manifest_json"].parent.mkdir(parents=True, exist_ok=True)
    paths["lane_manifest_md"].parent.mkdir(parents=True, exist_ok=True)
    paths["package_dir"].mkdir(parents=True, exist_ok=True)
    paths["project_dir"].mkdir(parents=True, exist_ok=True)
    payload["cleared_artifacts"] = clear_reused_report_paths(paths)
    write_lane_manifest(lane_manifest, paths["lane_manifest_json"], paths["lane_manifest_md"])
    write_payload(payload, paths["json_out"], paths["md_out"])
    try:
        returncode, stdout_tail, stderr_tail, combined = run_docker_command(
            command,
            log_out=paths["docker_log"],
            log_mode=args.docker_log_mode,
            timeout_seconds=args.timeout_seconds,
            log_tail_lines=args.log_tail_lines,
            container_name=container_name,
        )
    except subprocess.TimeoutExpired as exc:
        stale_handoff = paths["handoff_json"].is_file() and not _path_is_fresh(paths["handoff_json"], run_started_mtime)
        latest_progress = load_json(paths["progress_json"], min_mtime=run_started_mtime)
        payload["status"] = "fail"
        payload["failure_class"] = "timeout"
        payload["stdout_tail"] = _tail(exc.stdout or "", args.log_tail_lines) if isinstance(exc.stdout, str) else []
        payload["stderr_tail"] = _tail(exc.stderr or "", args.log_tail_lines) if isinstance(exc.stderr, str) else []
        payload["rough_edges"] = [f"docker lane exceeded {args.timeout_seconds}s timeout; attempted cleanup of {container_name}"]
        if isinstance(latest_progress, dict):
            phase = str(latest_progress.get("phase") or "").strip()
            last_log_line = str(latest_progress.get("last_log_line") or "").strip()
            updated_at = str(latest_progress.get("updated_at") or "").strip()
            if phase:
                payload["rough_edges"].append(f"last recorded progress phase: {phase}")
            if updated_at:
                payload["rough_edges"].append(f"last recorded progress update: {updated_at}")
            if last_log_line:
                payload["rough_edges"].append(f"last recorded progress line: {last_log_line}")
            payload["timeout_progress"] = latest_progress
        if stale_handoff:
            payload["handoff_json"] = None
            payload["handoff_markdown"] = None
            payload["rough_edges"].append("existing inner handoff artifacts predated this run and were ignored")
        write_payload(payload, paths["json_out"], paths["md_out"])
        return payload

    payload["returncode"] = returncode
    payload["stdout_tail"] = stdout_tail
    payload["stderr_tail"] = stderr_tail
    inner = load_json(paths["handoff_json"], min_mtime=run_started_mtime)
    if inner is None and paths["handoff_json"].is_file():
        payload["handoff_json"] = None
        payload["handoff_markdown"] = None
        payload["rough_edges"].append("existing inner handoff artifacts predated this run and were ignored")
    if inner:
        payload["inner_failure_class"] = inner.get("failure_class")
        payload["inner_status"] = inner.get("status")
        build_report = inner.get("build_report") if isinstance(inner.get("build_report"), dict) else {}
        payload["build_status"] = build_report.get("status")
        payload["selected_compiler_version"] = build_report.get("selected_compiler_version")
        payload["selected_folder_version"] = build_report.get("selected_folder_version")
        payload["toolchain_reason"] = build_report.get("toolchain_selection_reason")
        install_report = inner.get("install_smoke_report") if isinstance(inner.get("install_smoke_report"), dict) else {}
        payload["install_smoke_status"] = install_report.get("status")
    inner_failure = str(inner.get("failure_class") or "") if inner else ""
    if returncode == 0 and inner_failure == "verified-build":
        payload["status"] = "pass"
    elif inner_failure == "dry-run":
        payload["status"] = "dry-run"
    else:
        payload["status"] = "fail"
    payload["failure_class"] = classify(payload, combined, inner)
    if payload["status"] == "fail":
        payload["rough_edges"] = handoff_rough_edges(inner) or [
            "Linux Docker Unreal vendor lane is not yet green; inspect stdout/stderr tails and inner handoff artifact if produced.",
        ]
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Unreal Vendor Linux Docker Proof",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- engine_version: `{payload['engine_version']}`",
        f"- baseline_version: `{payload['baseline_version']}`",
        f"- status: `{payload['status']}`",
        f"- failure_class: `{payload['failure_class']}`",
        f"- image: `{payload['image']}`",
        f"- platform: `{payload['platform']}`",
        f"- container_name: `{payload['container_name']}`",
        f"- package_dir: `{payload['package_dir']}`",
        f"- project_dir: `{payload['project_dir']}`",
        f"- docker_available: `{payload['docker_available']}`",
        f"- image_available: `{payload['image_available']}`",
        f"- returncode: `{payload['returncode']}`",
        f"- selected_compiler_version: `{payload.get('selected_compiler_version') or ''}`",
        f"- selected_folder_version: `{payload.get('selected_folder_version') or ''}`",
        f"- install_smoke_status: `{payload.get('install_smoke_status') or ''}`",
        "",
        "## Claim Boundary",
        "",
        str(payload["claim_boundary"]),
        "",
        "## Command",
        "",
        "```bash",
        str(payload["command_text"]),
        "```",
        "",
        "## Rough Edges",
        "",
    ]
    for edge in payload.get("rough_edges", []):
        lines.append(f"- {edge}")
    lines.extend(["", "## Stdout Tail", "", "```text"])
    lines.extend(str(line) for line in payload.get("stdout_tail", []))
    lines.extend(["```", "", "## Stderr Tail", "", "```text"])
    lines.extend(str(line) for line in payload.get("stderr_tail", []))
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_lane_manifest_markdown(manifest: dict[str, Any]) -> str:
    image = manifest.get("image") if isinstance(manifest.get("image"), dict) else {}
    engine = manifest.get("engine") if isinstance(manifest.get("engine"), dict) else {}
    plugin = manifest.get("plugin") if isinstance(manifest.get("plugin"), dict) else {}
    runner = manifest.get("runner") if isinstance(manifest.get("runner"), dict) else {}
    replay = manifest.get("replay") if isinstance(manifest.get("replay"), dict) else {}
    lines = [
        "# Unreal Vendor Linux Lane Manifest",
        "",
        f"- lane: `{manifest.get('lane', '')}`",
        f"- vendor: `{manifest.get('vendor', '')}`",
        f"- engine_version: `{manifest.get('engine_version', '')}`",
        f"- baseline_version: `{manifest.get('baseline_version', '')}`",
        f"- target_platforms: `{manifest.get('target_platforms', '')}`",
        f"- image_tag: `{image.get('tag', '')}`",
        f"- image_platform: `{image.get('platform', '')}`",
        f"- image_repo_digest: `{image.get('repo_digest', '')}`",
        f"- engine_source_mode: `{engine.get('source_mode', '')}`",
        f"- engine_version_label: `{engine.get('version_label', '')}`",
        f"- plugin_root: `{plugin.get('root', '')}`",
        f"- plugin_git_commit: `{plugin.get('git_commit', '')}`",
        f"- runner_repo_commit: `{runner.get('repo_commit', '')}`",
        "",
        "## Replay Command",
        "",
        "```bash",
        str(replay.get("command_text") or ""),
        "```",
        "",
    ]
    return "\n".join(lines)


def write_payload(payload: dict[str, Any], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")


def write_lane_manifest(manifest: dict[str, Any], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_lane_manifest_markdown(manifest), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = output_paths(args)
    print(
        f"starting Unreal Linux Docker proof: engine={args.engine_version} container={resolved_container_name(args)}",
        flush=True,
    )
    payload = build_payload(args)
    if isinstance(payload.get("lane_manifest"), dict):
        write_lane_manifest(payload["lane_manifest"], paths["lane_manifest_json"], paths["lane_manifest_md"])
    write_payload(payload, paths["json_out"], paths["md_out"])
    if args.preserve:
        snapshot = preserve_artifact_snapshot.build_snapshot_from_report(
            paths["json_out"],
            out_root=args.preserve_root.expanduser().resolve(),
            lane="cesium-unreal-linux-docker",
            label=args.preserve_label,
        )
        payload["preserved_snapshot"] = snapshot["snapshot_dir"]
        write_payload(payload, paths["json_out"], paths["md_out"])
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"pass", "dry-run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
