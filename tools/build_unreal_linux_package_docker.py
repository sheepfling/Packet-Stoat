#!/usr/bin/env python3
"""Package the FastDIS Unreal plugin for Linux from macOS via Docker."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "grill-linux-proof:ubuntu24.04"
DEFAULT_PLATFORM = "linux/amd64"
DEFAULT_UE_ROOT = "/opt/unreal-engine"
DEFAULT_PREFLIGHT_TIMEOUT_SECONDS = 20
REQUIRED_ENGINE_PATHS = (
    "Engine/Build/BatchFiles/RunUAT.sh",
    "Engine/Binaries/Linux/UnrealEditor",
    "Engine/Build/Build.version",
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SystemExit(f"invalid env line in {path}: {raw_line}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def sanitize_label(value: str) -> str:
    return value.replace(" ", "_").replace("/", "__")


def engine_is_valid(root: Path) -> bool:
    return all((root / rel).exists() for rel in REQUIRED_ENGINE_PATHS)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def docker_preflight(image: str, platform_name: str | None) -> None:
    print(f"docker preflight: image={image} platform={platform_name}", flush=True)
    command = ["docker", "run", "--rm"]
    if platform_name:
        command.extend(["--platform", platform_name])
    command.extend([image, "bash", "-lc", "echo docker_preflight_ok"])
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=DEFAULT_PREFLIGHT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(
            "docker preflight timed out before the container reached a runnable state.\n"
            f"command: {' '.join(shlex.quote(part) for part in command)}"
        ) from exc
    if completed.returncode != 0:
        raise SystemExit("docker preflight failed:\n" + completed.stdout)


def resolve_path(raw: str, *, base: Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (base / path).resolve()
    return path.resolve()


def resolve_path_from_bases(raw: str, *, bases: list[Path]) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    for base in bases:
        candidate = (base / path).resolve()
        if candidate.exists():
            return candidate
    return (bases[0] / path).resolve()


def should_extract(stage_root: Path, archive: Path | None, force_reextract: bool) -> bool:
    if archive is None:
        return False
    if force_reextract:
        return True
    return not engine_is_valid(stage_root)


def build_inner_script(config: dict[str, Any], *, archive_present: bool, extract_archive: bool) -> str:
    ue_root = config["ue_root_in_container"]
    repo_name = ROOT.name
    safe_label = config["safe_label"]
    local_root = f"/tmp/fastdis_linux_proof/{safe_label}"
    local_repo = f"{local_root}/{repo_name}"
    local_package_dir = f"{local_root}/package"
    host_package_dir = "/host_package"
    lines = ["set -euo pipefail"]
    lines.extend(
        [
            "if ! command -v cmake >/dev/null 2>&1; then",
            "  if command -v apt-get >/dev/null 2>&1; then",
            "    export DEBIAN_FRONTEND=noninteractive",
            "    apt-get update",
            "    apt-get install -y cmake build-essential",
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
                "for rel in [",
                "    'Engine/Build/BatchFiles/RunUAT.sh',",
                "    'Engine/Build/BatchFiles/RunUAT.command',",
                "    'Engine/Build/BatchFiles/Linux/Build.sh',",
                "]:",
                "    path = dest / rel",
                "    if path.exists():",
                "        path.chmod(path.stat().st_mode | 0o111)",
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
            "for rel in ['Engine/Build/BatchFiles', 'Engine/Binaries', 'Engine/Extras/ThirdPartyNotUE/SDKs', 'Engine/Source/ThirdParty']:",
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
            f'export FASTDIS_UNREAL_WORK_ROOT="{local_root}/work"',
            f'rm -rf "{local_root}"',
            f'mkdir -p "{local_root}"',
            f'mkdir -p "{local_repo}/tools" "{local_repo}/packages/unreal" "{local_repo}/src" "{local_repo}/include"',
            f'cp "/src/CMakeLists.txt" "{local_repo}/CMakeLists.txt"',
            f'cp "/src/pyproject.toml" "{local_repo}/pyproject.toml"',
            f'cp "/src/tools/artifacts.py" "{local_repo}/tools/artifacts.py"',
            f'cp "/src/tools/build_unreal_plugin.py" "{local_repo}/tools/build_unreal_plugin.py"',
            f'cp "/src/tools/load_local_env.py" "{local_repo}/tools/load_local_env.py"',
            f'cp "/src/tools/release_metadata.py" "{local_repo}/tools/release_metadata.py"',
            f'cp "/src/tools/unreal_env.py" "{local_repo}/tools/unreal_env.py"',
            f'cp -R "/src/cmake" "{local_repo}/cmake"',
            f'cp -R "/src/include/." "{local_repo}/include/"',
            f'cp -R "/src/src/." "{local_repo}/src/"',
            f'cp -R "/src/packages/unreal/FastDis" "{local_repo}/packages/unreal/FastDis"',
            f'cd "{local_repo}"',
            f'python3 tools/build_unreal_plugin.py --engine-dir "{ue_root}" --target-platforms Linux --package-dir "{local_package_dir}" --native-build-dir "{local_root}/native" --clean-package --skip-platform-probe',
            f'mkdir -p "{host_package_dir}"',
            f'find "{host_package_dir}" -mindepth 1 -maxdepth 1 -exec rm -rf {{}} +',
            f'cp -R "{local_package_dir}/." "{host_package_dir}/"',
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=ROOT / "tools" / "unreal_linux_profiles" / "ubuntu_24_04_ue57.env")
    parser.add_argument("--engine-archive", help="Override the Unreal Linux zip archive path")
    parser.add_argument("--engine-path", help="Override the unpacked Unreal Linux engine directory")
    parser.add_argument("--image", help="Override the Docker image")
    parser.add_argument("--package-dir", type=Path, help="Override the output package directory")
    parser.add_argument("--engine-stage-dir", type=Path, help="Override the staged engine directory")
    parser.add_argument("--force-reextract", action="store_true")
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    profile_path = args.profile.expanduser().resolve()
    values = dict(os.environ)
    values.update(parse_env_file(profile_path))
    image = args.image or values.get("UE_LINUX_IMAGE") or DEFAULT_IMAGE
    version_label = values.get("UE_VERSION_LABEL", "ue-linux")
    proof_profile = values.get("UE_PROOF_PROFILE", "default")
    safe_label = f"{sanitize_label(version_label)}_{sanitize_label(proof_profile)}"
    package_dir = args.package_dir or resolve_path(
        values.get("HOST_PACKAGE_DIR", f"build/linux_unreal_package/{safe_label}/package"),
        base=ROOT,
    )
    engine_stage_dir = args.engine_stage_dir or resolve_path(
        values.get("HOST_ENGINE_STAGE_DIR", f".build/linux_unreal_engine/{sanitize_label(version_label)}"),
        base=ROOT,
    )
    engine_path_raw = args.engine_path or values.get("UE_HOST_PATH", "")
    engine_archive_raw = args.engine_archive or values.get("UE_HOST_ARCHIVE", "")
    cli_search_bases = [Path.cwd(), ROOT, profile_path.parent]
    profile_search_bases = [profile_path.parent, ROOT, Path.cwd()]
    engine_path = (
        resolve_path_from_bases(
            engine_path_raw,
            bases=cli_search_bases if args.engine_path else profile_search_bases,
        )
        if engine_path_raw
        else None
    )
    engine_archive = (
        resolve_path_from_bases(
            engine_archive_raw,
            bases=cli_search_bases if args.engine_archive else profile_search_bases,
        )
        if engine_archive_raw
        else None
    )
    return {
        "profile_path": profile_path,
        "image": image,
        "platform": values.get("DOCKER_PLATFORM", DEFAULT_PLATFORM),
        "ue_root_in_container": values.get("UE_ROOT_IN_CONTAINER", DEFAULT_UE_ROOT),
        "version_label": version_label,
        "proof_profile": proof_profile,
        "safe_label": safe_label,
        "package_dir": package_dir.resolve(),
        "engine_stage_dir": engine_stage_dir.resolve(),
        "engine_path": engine_path,
        "engine_archive": engine_archive,
        "force_reextract": args.force_reextract,
    }


def run_build(config: dict[str, Any]) -> int:
    docker_preflight(config["image"], config["platform"])

    archive_present = config["engine_archive"] is not None
    extract_archive = False
    mount_engine_source: Path
    if config["engine_path"] is not None:
        mount_engine_source = config["engine_path"]
    elif config["engine_archive"] is not None:
        mount_engine_source = config["engine_stage_dir"]
        mount_engine_source.mkdir(parents=True, exist_ok=True)
        extract_archive = should_extract(
            config["engine_stage_dir"], config["engine_archive"], bool(config["force_reextract"])
        )
    else:
        raise SystemExit("Provide --engine-path or --engine-archive, or set UE_HOST_PATH/UE_HOST_ARCHIVE in the profile.")

    print(
        f"engine source: {mount_engine_source} archive_present={archive_present} extract_archive={extract_archive}",
        flush=True,
    )
    print(f"package output: {display_path(config['package_dir'])}", flush=True)

    config["package_dir"].mkdir(parents=True, exist_ok=True)
    if config["package_dir"].exists():
        shutil.rmtree(config["package_dir"])
    config["package_dir"].mkdir(parents=True, exist_ok=True)

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
        f"{config['package_dir']}:/host_package",
    ]
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
    print("launching docker build for FastDIS Unreal Linux package", flush=True)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode == 0:
        print(f"linux unreal package: {display_path(config['package_dir'])}")
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_build(build_config(args))


if __name__ == "__main__":
    raise SystemExit(main())
