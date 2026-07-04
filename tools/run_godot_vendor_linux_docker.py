#!/usr/bin/env python3
"""Run the Godot vendor-plugin lane inside a Linux Docker proof container."""

from __future__ import annotations

import argparse
from collections import deque
from datetime import UTC, datetime
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
import preserve_artifact_snapshot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "fastdis-godot-linux-proof:godot4.7-ubuntu24.04"
DEFAULT_PLATFORM = "linux/amd64"
DEFAULT_VENDOR = "cesium-godot"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "reports" / "godot_vendor_plugin"
DEFAULT_JSON_OUT = DEFAULT_REPORT_DIR / "cesium-godot_linux_docker.json"
DEFAULT_MD_OUT = DEFAULT_REPORT_DIR / "cesium-godot_linux_docker.md"
DEFAULT_INNER_JSON = DEFAULT_REPORT_DIR / "cesium-godot_linux_docker_handoff.json"
DEFAULT_INNER_MD = DEFAULT_REPORT_DIR / "cesium-godot_linux_docker_handoff.md"
DEFAULT_INNER_LOG = DEFAULT_REPORT_DIR / "cesium-godot_linux_docker_build.log"
DEFAULT_DOCKER_LOG = DEFAULT_REPORT_DIR / "cesium-godot_linux_docker_stdout.log"
DEFAULT_CACHE_VOLUME = "fastdis-godot-linux-proof-cache"
DEFAULT_CONTAINER_NAME_PREFIX = "packet-stoat-godot-linux-proof"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", default=DEFAULT_VENDOR)
    parser.add_argument("--plugin-root", default="external/cesium/3D-Tiles-For-Godot")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--platform", default=DEFAULT_PLATFORM)
    parser.add_argument("--cache-volume", default=DEFAULT_CACHE_VOLUME, help="Docker volume mounted at /tmp/fastdis_godot for vcpkg/native dependency cache")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--docker-log-out", type=Path, default=DEFAULT_DOCKER_LOG)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--scons-jobs", type=int, default=4)
    parser.add_argument("--vcpkg-max-concurrency", type=int, default=4)
    parser.add_argument("--cmake-build-parallel-level", type=int, default=4)
    parser.add_argument("--docker-log-mode", choices=("capture", "tee"), default="capture", help="Capture Docker output quietly or tee it live while persisting a log")
    parser.add_argument("--inner-log-mode", choices=("capture", "tee"), default="capture", help="Forwarded to the inner Godot vendor workflow")
    parser.add_argument("--log-tail-lines", type=int, default=40, help="Number of non-empty output lines retained in JSON/Markdown tails")
    parser.add_argument("--container-name", help="Docker container name; defaults to a per-process proof name for timeout cleanup")
    parser.add_argument("--preserve", action="store_true", help="Copy final reports, logs, and discovered built artifacts to artifacts/preserved/")
    parser.add_argument("--preserve-label", default="godot-linux-docker", help="Label used in the preserved snapshot directory")
    parser.add_argument("--preserve-root", type=Path, default=PRESERVED_ARTIFACTS_DIR)
    parser.add_argument("--no-clean-native-cache", action="store_true", help="Do not remove generated native CMake cache files before the Linux container run")
    parser.add_argument("--inner-dry-run", action="store_true", help="Delegate a dry-run handoff inside Docker")
    parser.add_argument("--dry-run", action="store_true", help="Emit the Docker command without executing it")
    return parser.parse_args(argv)


def _container_path(path: Path) -> str:
    relative = path.resolve().relative_to(ROOT)
    return "/src/" + relative.as_posix()


def build_inner_command(args: argparse.Namespace) -> str:
    inner_json = _container_path(DEFAULT_INNER_JSON)
    inner_md = _container_path(DEFAULT_INNER_MD)
    inner_log = _container_path(DEFAULT_INNER_LOG)
    lines = [
        "set -euo pipefail",
        "export FASTDIS_GODOT_WORK_ROOT=/tmp/fastdis_godot",
        "export HOME=/tmp/fastdis_godot/home",
        "export XDG_CACHE_HOME=/tmp/fastdis_godot/home/.cache",
        "export XDG_CONFIG_HOME=/tmp/fastdis_godot/home/.config",
        "export XDG_DATA_HOME=/tmp/fastdis_godot/home/.local/share",
        "mkdir -p /tmp/fastdis_godot/home/.cache /tmp/fastdis_godot/home/.config /tmp/fastdis_godot/home/.local/share",
        "printf 'http1.1\\n' > /tmp/fastdis_godot/home/.curlrc",
        f"export VCPKG_MAX_CONCURRENCY={max(1, args.vcpkg_max_concurrency)}",
        f"export CMAKE_BUILD_PARALLEL_LEVEL={max(1, args.cmake_build_parallel_level)}",
        "cd /src",
    ]
    if not args.no_clean_native_cache:
        native_dir = shlex.quote(f"/src/{args.plugin_root.strip('/')}/cesium_godot/native")
        lines.extend(
            [
                f"rm -f {native_dir}/CMakeCache.txt",
                f"rm -rf {native_dir}/CMakeFiles",
            ]
        )
    lines.extend(
        [
            "python3 tools/godot_vendor_workflow.py handoff "
        f"--vendor {shlex.quote(args.vendor)} "
        f"--plugin-root {shlex.quote(args.plugin_root)} "
        f"--scons-jobs {max(1, args.scons_jobs)} "
        f"--log-mode {shlex.quote(args.inner_log_mode)} "
        f"--log-tail-lines {max(1, args.log_tail_lines)} "
        f"--build-json-out {shlex.quote(inner_json)} "
        f"--build-md-out {shlex.quote(inner_md)} "
        f"--log-out {shlex.quote(inner_log)} "
        f"--json-out {shlex.quote(inner_json)} "
        f"--md-out {shlex.quote(inner_md)}"
        + (" --dry-run" if args.inner_dry_run else ""),
        ]
    )
    return "\n".join(lines)


def build_docker_command(args: argparse.Namespace) -> list[str]:
    container_name = resolved_container_name(args)
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--platform",
        args.platform,
        "-v",
        f"{ROOT}:/src",
        "-v",
        f"{args.cache_volume}:/tmp/fastdis_godot",
        "-w",
        "/src",
        args.image,
        "bash",
        "-lc",
        build_inner_command(args),
    ]


def resolved_container_name(args: argparse.Namespace) -> str:
    return args.container_name or f"{DEFAULT_CONTAINER_NAME_PREFIX}-{os.getpid()}"


def _tail(text: str, lines: int) -> list[str]:
    rows = [row for row in text.splitlines() if row.strip()]
    return rows[-max(1, lines):]


def cleanup_container(container_name: str) -> None:
    try:
        subprocess.run(["docker", "rm", "-f", container_name], text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        pass


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


def docker_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(["docker", "info"], text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    detail = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, detail.splitlines()[0] if detail else f"returncode={result.returncode}"


def image_available(image: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image],
            text=True,
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def classify(payload: dict[str, Any], output: str) -> str:
    if payload.get("status") == "pass":
        return "verified-build"
    lowered = output.lower()
    if "no such image" in lowered or "unable to find image" in lowered:
        return "container-image-missing"
    if "scons" in lowered and ("missing" in lowered or "not found" in lowered):
        return "toolchain-missing"
    if "godot" in lowered and ("missing" in lowered or "not found" in lowered):
        return "engine-missing"
    if "error:" in lowered or "fatal error" in lowered or "undefined reference" in lowered:
        return "compile-or-link"
    return "docker-lane-failed" if payload.get("returncode") else "dry-run"


def _path_is_fresh(path: Path, min_mtime: float) -> bool:
    try:
        return path.is_file() and path.stat().st_mtime >= min_mtime
    except OSError:
        return False


def load_inner_handoff(*, min_mtime: float | None = None) -> dict[str, Any] | None:
    if not DEFAULT_INNER_JSON.is_file():
        return None
    if min_mtime is not None and not _path_is_fresh(DEFAULT_INNER_JSON, min_mtime):
        return None
    try:
        loaded = json.loads(DEFAULT_INNER_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def inner_rough_edges(inner: dict[str, Any] | None) -> list[str]:
    if not inner:
        return []
    build_report = inner.get("build_report") if isinstance(inner.get("build_report"), dict) else {}
    edges: list[str] = []
    for check in build_report.get("doctor_checks", []):
        if not isinstance(check, dict) or check.get("status") != "fail":
            continue
        name = str(check.get("name") or "check")
        detail = str(check.get("detail") or "failed")
        edges.append(f"{name}: {detail}")
    for step in build_report.get("next_steps", []):
        text = str(step).strip()
        if text:
            edges.append(f"next: {text}")
    for line in build_report.get("failure_tail", [])[-8:]:
        text = str(line).strip()
        if text:
            edges.append(f"failure: {text}")
    return edges


def inner_build_status(inner: dict[str, Any] | None) -> str:
    if not inner:
        return ""
    build_report = inner.get("build_report") if isinstance(inner.get("build_report"), dict) else {}
    return str(build_report.get("status") or inner.get("status") or "")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    run_started_mtime = time.time()
    json_out = args.json_out.expanduser().resolve()
    md_out = args.md_out.expanduser().resolve()
    docker_log_out = args.docker_log_out.expanduser().resolve()
    container_name = resolved_container_name(args)
    command = build_docker_command(args)
    docker_ok, docker_detail = docker_available()
    payload: dict[str, Any] = {
        "schema": "packet_stoat.godot_vendor_linux_docker.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "vendor": args.vendor,
        "host": "linux-docker",
        "status": "dry-run" if args.dry_run else "pending",
        "failure_class": "dry-run" if args.dry_run else "",
        "image": args.image,
        "platform": args.platform,
        "container_name": container_name,
        "plugin_root": args.plugin_root,
        "cache_volume": args.cache_volume,
        "docker_available": docker_ok,
        "docker_detail": docker_detail,
        "image_available": image_available(args.image),
        "command": command,
        "command_text": " ".join(shlex.quote(part) for part in command),
        "inner_environment": {
            "FASTDIS_GODOT_WORK_ROOT": "/tmp/fastdis_godot",
            "VCPKG_MAX_CONCURRENCY": str(max(1, args.vcpkg_max_concurrency)),
            "CMAKE_BUILD_PARALLEL_LEVEL": str(max(1, args.cmake_build_parallel_level)),
            "scons_jobs": str(max(1, args.scons_jobs)),
            "clean_native_cache": str(not args.no_clean_native_cache).lower(),
            "curl_http_version": "1.1",
            "inner_log_mode": args.inner_log_mode,
            "docker_log_mode": args.docker_log_mode,
            "log_tail_lines": str(max(1, args.log_tail_lines)),
        },
        "observability": {
            "docker_log_mode": args.docker_log_mode,
            "inner_log_mode": args.inner_log_mode,
            "log_tail_lines": max(1, args.log_tail_lines),
            "docker_log": str(docker_log_out),
            "capture": "Docker output captured until exit" if args.docker_log_mode == "capture" else "Docker output streamed live and persisted",
        },
        "report_json": str(json_out),
        "report_markdown": str(md_out),
        "inner_handoff_json": str(DEFAULT_INNER_JSON.resolve()),
        "inner_handoff_markdown": str(DEFAULT_INNER_MD.resolve()),
        "inner_build_log": str(DEFAULT_INNER_LOG.resolve()),
        "docker_log": str(docker_log_out),
        "returncode": None,
        "stdout_tail": [],
        "stderr_tail": [],
        "rough_edges": [],
    }
    if args.dry_run:
        payload["rough_edges"] = ["not executed; use without --dry-run to probe the Linux container lane"]
        return payload
    if not docker_ok:
        payload["status"] = "fail"
        payload["failure_class"] = "docker-unavailable"
        payload["rough_edges"] = [docker_detail]
        return payload

    try:
        returncode, stdout_tail, stderr_tail, combined = run_docker_command(
            command,
            log_out=docker_log_out,
            log_mode=args.docker_log_mode,
            timeout_seconds=args.timeout_seconds,
            log_tail_lines=args.log_tail_lines,
            container_name=container_name,
        )
    except subprocess.TimeoutExpired as exc:
        stale_inner_handoff = DEFAULT_INNER_JSON.is_file() and not _path_is_fresh(DEFAULT_INNER_JSON, run_started_mtime)
        payload["status"] = "fail"
        payload["failure_class"] = "timeout"
        payload["returncode"] = None
        payload["stdout_tail"] = _tail(exc.stdout or "", args.log_tail_lines) if isinstance(exc.stdout, str) else []
        payload["stderr_tail"] = _tail(exc.stderr or "", args.log_tail_lines) if isinstance(exc.stderr, str) else []
        payload["rough_edges"] = [f"docker lane exceeded {args.timeout_seconds}s timeout; attempted cleanup of {container_name}"]
        if stale_inner_handoff:
            payload["inner_handoff_json"] = None
            payload["inner_handoff_markdown"] = None
            payload["rough_edges"].append("existing inner handoff artifacts predated this run and were ignored")
        return payload

    payload["returncode"] = returncode
    payload["stdout_tail"] = stdout_tail
    payload["stderr_tail"] = stderr_tail
    inner = load_inner_handoff(min_mtime=run_started_mtime)
    if inner is None and DEFAULT_INNER_JSON.is_file():
        payload["inner_handoff_json"] = None
        payload["inner_handoff_markdown"] = None
        payload["rough_edges"].append("existing inner handoff artifacts predated this run and were ignored")
    if inner:
        payload["inner_failure_class"] = inner.get("failure_class")
    inner_failure_class = str(inner.get("failure_class")) if inner and inner.get("failure_class") else ""
    inner_status = inner_build_status(inner)
    payload["inner_status"] = inner_status
    if returncode == 0 and inner_status in {"pass", "ok"}:
        payload["status"] = "pass"
    elif inner_failure_class == "dry-run":
        payload["status"] = "dry-run"
    else:
        payload["status"] = "fail"
    payload["failure_class"] = inner_failure_class or classify(payload, combined)
    if payload["status"] == "fail":
        payload["rough_edges"] = inner_rough_edges(inner) or [
            "Linux Docker Godot vendor lane is not yet green; inspect stdout/stderr tails and inner handoff artifact if produced.",
        ]
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Godot Vendor Linux Docker Proof",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- status: `{payload['status']}`",
        f"- failure_class: `{payload['failure_class']}`",
        f"- image: `{payload['image']}`",
        f"- platform: `{payload['platform']}`",
        f"- container_name: `{payload['container_name']}`",
        f"- cache_volume: `{payload['cache_volume']}`",
        f"- docker_log: `{payload['docker_log']}`",
        f"- docker_log_mode: `{payload.get('observability', {}).get('docker_log_mode', '')}`",
        f"- inner_log_mode: `{payload.get('observability', {}).get('inner_log_mode', '')}`",
        f"- log_tail_lines: `{payload.get('observability', {}).get('log_tail_lines', '')}`",
        f"- docker_available: `{payload['docker_available']}`",
        f"- image_available: `{payload['image_available']}`",
        f"- returncode: `{payload['returncode']}`",
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


def write_payload(payload: dict[str, Any], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    write_payload(payload, args.json_out.expanduser().resolve(), args.md_out.expanduser().resolve())
    if args.preserve:
        snapshot = preserve_artifact_snapshot.build_snapshot_from_report(
            args.json_out.expanduser().resolve(),
            out_root=args.preserve_root.expanduser().resolve(),
            lane="cesium-godot-linux-docker",
            label=args.preserve_label,
        )
        payload["preserved_snapshot"] = snapshot["snapshot_dir"]
        write_payload(payload, args.json_out.expanduser().resolve(), args.md_out.expanduser().resolve())
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"pass", "dry-run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
