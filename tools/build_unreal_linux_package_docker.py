#!/usr/bin/env python3
"""Package the FastDIS Unreal plugin for Linux from macOS via Docker."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "grill-linux-proof:ubuntu24.04"
DEFAULT_PLATFORM = "linux/amd64"
DEFAULT_DOCKER_USER = "1000:1000"
DEFAULT_UE_ROOT = "/opt/unreal-engine"
DEFAULT_PREFLIGHT_TIMEOUT_SECONDS = 20
DEFAULT_LINUX_ENGINE_INPUT_ROOT = ROOT / "artifacts" / "inputs" / "unreal" / "linux"
REQUIRED_ENGINE_PATHS = (
    "Engine/Build/BatchFiles/RunUAT.sh",
    "Engine/Binaries/Linux/UnrealEditor",
    "Engine/Build/Build.version",
)
ARCHIVE_VERSION_PATTERN = re.compile(r"Linux_Unreal_Engine_(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)
GENERIC_VERSION_PATTERN = re.compile(r"(\d+\.\d+(?:\.\d+)?)")


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


def version_family(version: str | None) -> str:
    if not version:
        return ""
    parts = [part for part in str(version).split(".") if part]
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return str(version)


def version_sort_key(version: str | None) -> tuple[int, ...]:
    if not version:
        return (0,)
    numbers: list[int] = []
    for token in re.findall(r"\d+", str(version)):
        try:
            numbers.append(int(token))
        except ValueError:
            numbers.append(0)
    return tuple(numbers or [0])


def parse_linux_engine_version(name: str, *, allow_generic: bool = True) -> str | None:
    archive_match = ARCHIVE_VERSION_PATTERN.search(name)
    if archive_match:
        return archive_match.group(1)
    if not allow_generic:
        return None
    generic_match = GENERIC_VERSION_PATTERN.search(name)
    if generic_match:
        return generic_match.group(1)
    return None


def default_linux_engine_search_roots() -> list[Path]:
    roots: list[Path] = [DEFAULT_LINUX_ENGINE_INPUT_ROOT]
    env_value = os.environ.get("FASTDIS_UNREAL_LINUX_ENGINE_ROOTS", "").strip()
    if env_value:
        for raw in env_value.split(os.pathsep):
            if raw.strip():
                roots.append(Path(raw.strip()).expanduser())
    system_name = platform.system().lower()
    if system_name == "windows":
        roots.append(Path(r"D:\Unreal\linux"))
        roots.append(Path(r"C:\Users\Public\Unreal\engines\linux"))
    elif system_name == "darwin":
        roots.append(Path("/Users/Public/Unreal/engines/linux"))
        roots.append(Path("/Users/Shared/Unreal/engines/linux"))
    else:
        roots.append(Path("/opt/unreal/engines/linux"))
        roots.append(Path("/srv/unreal/engines/linux"))
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        normalized = str(root)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(root)
    return unique


def discover_linux_engine_inputs(search_roots: list[Path] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in search_roots or default_linux_engine_search_roots():
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_file() and child.suffix.lower() == ".zip":
                version = parse_linux_engine_version(child.name, allow_generic=False)
                if not version:
                    continue
                row = {
                    "version": version,
                    "version_family": version_family(version),
                    "version_label": f"ue{version}-linux",
                    "root": root.resolve(),
                }
                row["archive_path"] = child.resolve()
            elif child.is_dir() and engine_is_valid(child):
                version = parse_linux_engine_version(child.name, allow_generic=True)
                if not version:
                    build_version = child / "Engine" / "Build" / "Build.version"
                    if build_version.is_file():
                        try:
                            payload = build_version.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            payload = ""
                        version = parse_linux_engine_version(payload, allow_generic=True)
                if not version:
                    continue
                row = {
                    "version": version,
                    "version_family": version_family(version),
                    "version_label": f"ue{version}-linux",
                    "root": root.resolve(),
                }
                row["engine_path"] = child.resolve()
            else:
                continue
            rows.append(row)
    rows.sort(
        key=lambda row: (
            version_sort_key(str(row.get("version") or "")),
            1 if row.get("engine_path") else 0,
            str(row.get("archive_path") or row.get("engine_path") or ""),
        )
    )
    return rows


def select_linux_engine_input(
    version: str | None,
    discovered: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not discovered:
        return None
    if version:
        requested_family = version_family(version)
        candidates = [
            row
            for row in discovered
            if str(row.get("version") or "") == version
            or str(row.get("version_family") or "") == requested_family
        ]
        if candidates:
            return max(
                candidates,
                key=lambda row: (
                    version_sort_key(str(row.get("version") or "")),
                    1 if row.get("engine_path") else 0,
                ),
            )
        return None
    return max(
        discovered,
        key=lambda row: (
            version_sort_key(str(row.get("version") or "")),
            1 if row.get("engine_path") else 0,
        ),
    )


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
    parser.add_argument("--engine-version", help="Prefer a discovered Linux Unreal payload matching this engine version, for example 5.8")
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
    discovered_inputs = discover_linux_engine_inputs()
    selected_input = select_linux_engine_input(args.engine_version, discovered_inputs)
    requested_family = version_family(args.engine_version)
    profile_version_family = version_family(values.get("UE_VERSION_LABEL", ""))
    profile_version_mismatch = bool(requested_family and profile_version_family and profile_version_family != requested_family)
    image = args.image or values.get("UE_LINUX_IMAGE") or DEFAULT_IMAGE
    docker_user = values.get("DOCKER_USER") or DEFAULT_DOCKER_USER
    resolved_engine_version = (
        str(selected_input.get("version_family") or "")
        if selected_input
        else (args.engine_version or version_family(values.get("UE_VERSION_LABEL", "")) or "")
    )
    version_label = (
        values.get("UE_VERSION_LABEL")
        if values.get("UE_VERSION_LABEL") and not profile_version_mismatch
        else None
    ) or (
        str(selected_input.get("version_label") or "")
        if selected_input
        else (f"ue{args.engine_version}-linux" if args.engine_version else "ue-linux")
    )
    proof_profile = values.get("UE_PROOF_PROFILE", "default")
    safe_label = f"{sanitize_label(version_label)}_{sanitize_label(proof_profile)}"
    host_package_dir_value = values.get("HOST_PACKAGE_DIR", "")
    host_engine_stage_dir_value = values.get("HOST_ENGINE_STAGE_DIR", "")
    if profile_version_mismatch:
        host_package_dir_value = ""
        host_engine_stage_dir_value = ""
    package_dir = args.package_dir or resolve_path(
        host_package_dir_value or f"artifacts/packages/unreal/linux/{safe_label}/package",
        base=ROOT,
    )
    engine_stage_dir = args.engine_stage_dir or resolve_path(
        host_engine_stage_dir_value or f"artifacts/staging/unreal/linux/{sanitize_label(version_label)}",
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
        else Path(selected_input["engine_path"]).resolve() if selected_input and selected_input.get("engine_path") else None
    )
    engine_archive = (
        resolve_path_from_bases(
            engine_archive_raw,
            bases=cli_search_bases if args.engine_archive else profile_search_bases,
        )
        if engine_archive_raw
        else Path(selected_input["archive_path"]).resolve() if selected_input and selected_input.get("archive_path") else None
    )
    return {
        "profile_path": profile_path,
        "image": image,
        "platform": values.get("DOCKER_PLATFORM", DEFAULT_PLATFORM),
        "docker_user": docker_user,
        "ue_root_in_container": values.get("UE_ROOT_IN_CONTAINER", DEFAULT_UE_ROOT),
        "version_label": version_label,
        "engine_version": resolved_engine_version,
        "proof_profile": proof_profile,
        "safe_label": safe_label,
        "package_dir": package_dir.resolve(),
        "engine_stage_dir": engine_stage_dir.resolve(),
        "engine_path": engine_path,
        "engine_archive": engine_archive,
        "discovered_inputs": discovered_inputs,
        "selected_input": selected_input,
        "search_roots": [path.resolve() for path in default_linux_engine_search_roots()],
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
        search_roots = ", ".join(str(path) for path in config.get("search_roots") or []) or "none"
        raise SystemExit(
            "Provide --engine-path or --engine-archive, set UE_HOST_PATH/UE_HOST_ARCHIVE in the profile, "
            f"or place Linux Unreal downloads under one of: {search_roots}"
        )

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
        "--user",
        str(config["docker_user"]),
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
