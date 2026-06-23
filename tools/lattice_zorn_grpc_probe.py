#!/usr/bin/env python3
"""Probe the pinned Zorn gRPC surface from FastDIS."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts import VERIFICATION_REPORTS_DIR
from fastdis.lattice_backend import load_lattice_backend_config


DEFAULT_OUT_DIR = VERIFICATION_REPORTS_DIR / "alpha5" / "lattice_zorn_grpc"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser.parse_args()


def _find_zorn_python(checkout: Path) -> Path | None:
    env_override = os.environ.get("FASTDIS_LATTICE_BACKEND_PYTHON")
    if env_override:
        candidate = Path(env_override).resolve()
        if candidate.is_file():
            return candidate
    for candidate in (
        checkout / ".venv" / "bin" / "python",
        checkout / ".venv" / "Scripts" / "python.exe",
    ):
        if candidate.is_file():
            return candidate
    return None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def _wait_for_tcp(host: str, port: int, *, timeout_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    last_error: OSError | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError as exc:
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"Zorn gRPC server did not open {host}:{port}: {last_error}")


def _zorn_env(checkout: Path, state_dir: Path, port: int) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    zorn_src = str((checkout / "src").resolve())
    env["PYTHONPATH"] = zorn_src if not pythonpath else f"{zorn_src}{os.pathsep}{pythonpath}"
    env["C2_COMPAT_AUTH_MODE"] = "none"
    env["C2_COMPAT_DATABASE_URL"] = f"sqlite:///{(state_dir / 'zorn-grpc.db').resolve()}"
    env["C2_COMPAT_OBJECT_ROOT"] = str((state_dir / "objects").resolve())
    env["C2_COMPAT_GRPC_HOST"] = "127.0.0.1"
    env["C2_COMPAT_GRPC_PORT"] = str(port)
    return env


@contextmanager
def _running_zorn_grpc(out_dir: Path, *, timeout_seconds: float) -> Iterator[tuple[str, Path, Path]]:
    config = load_lattice_backend_config()
    checkout = config.checkout_path
    zorn_python = _find_zorn_python(checkout)
    if not checkout.is_dir():
        raise RuntimeError(f"Zorn checkout is not present: {checkout}")
    if zorn_python is None:
        raise RuntimeError(f"Zorn virtualenv python was not found under {checkout}")
    port = _free_port()
    target = f"127.0.0.1:{port}"
    out_dir.mkdir(parents=True, exist_ok=True)
    state_dir = out_dir / f"zorn_grpc_runtime_{time.time_ns()}"
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "zorn_grpc_server.log"
    env = _zorn_env(checkout, state_dir, port)
    command = [str(zorn_python), "-m", "zorn.grpc_main"]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=checkout, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            _wait_for_tcp("127.0.0.1", port, timeout_seconds=timeout_seconds)
            yield target, checkout, zorn_python
        finally:
            process.terminate()
            try:
                process.wait(timeout=10.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)


def _write_probe_script(out_dir: Path) -> Path:
    script_path = (out_dir / "zorn_grpc_surface_probe.py").resolve()
    script_path.write_text(_PROBE_SCRIPT, encoding="utf-8")
    return script_path


def _run_probe(zorn_python: Path, checkout: Path, target: str, out_dir: Path) -> dict[str, Any]:
    script_path = _write_probe_script(out_dir)
    report_path = (out_dir / "zorn_grpc_surface_probe.json").resolve()
    command = [str(zorn_python), str(script_path), "--target", target, "--out", str(report_path)]
    completed = subprocess.run(command, cwd=checkout, check=False, text=True, capture_output=True)
    if report_path.is_file():
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload["probe_returncode"] = completed.returncode
            payload["probe_stdout"] = completed.stdout
            payload["probe_stderr"] = completed.stderr
            return payload
    return {
        "overall_status": "failed",
        "probe_returncode": completed.returncode,
        "probe_stdout": completed.stdout,
        "probe_stderr": completed.stderr,
        "checks": [
            {
                "name": "probe_script",
                "status": "failed",
                "detail": "probe did not write a JSON report",
            }
        ],
    }


def build_report(out_dir: Path, *, timeout_seconds: float) -> dict[str, Any]:
    config = load_lattice_backend_config()
    report: dict[str, Any] = {
        "schema": "fastdis.zorn.grpc.probe.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": config.backend,
        "transport": config.transport,
        "zorn_tag": config.tag,
        "zorn_checkout": str(config.checkout_path),
        "proof_source": "zorn-grpc-official-buf-surface",
    }
    try:
        with _running_zorn_grpc(out_dir, timeout_seconds=timeout_seconds) as (target, checkout, zorn_python):
            report["target"] = target
            report["zorn_python"] = str(zorn_python)
            report.update(_run_probe(zorn_python, checkout, target, out_dir))
    except Exception as exc:  # noqa: BLE001
        report.update(
            {
                "overall_status": "failed",
                "checks": [
                    {
                        "name": "zorn_grpc_startup",
                        "status": "failed",
                        "detail": str(exc),
                    }
                ],
            }
        )
    return report


def write_report(report: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "zorn_grpc_probe_report.json"
    md_path = out_dir / "zorn_grpc_probe_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Zorn gRPC Probe Report",
        "",
        f"- overall_status: `{report.get('overall_status', 'unknown')}`",
        f"- proof_source: `{report.get('proof_source', 'unknown')}`",
        f"- target: `{report.get('target', 'not-started')}`",
        f"- zorn_tag: `{report.get('zorn_tag', 'unknown')}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks", []):
        if isinstance(check, dict):
            lines.append(f"- `{check.get('name')}`: `{check.get('status')}` - {check.get('detail', '')}")
    gaps = report.get("gaps", [])
    if gaps:
        lines.extend(["", "## Gaps", ""])
        for gap in gaps:
            lines.append(f"- {gap}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args.out_dir, timeout_seconds=args.timeout_seconds)
    json_path, md_path = write_report(report, args.out_dir)
    print(json.dumps({"overall_status": report["overall_status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))
    return 0 if report["overall_status"] in {"ready", "ready-with-gaps"} else 1


_PROBE_SCRIPT = r'''
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import grpc
from google.protobuf.json_format import MessageToDict

from zorn.grpc_api.contract import assert_lattice_grpc_contract
from zorn.grpc_api.proto_modules import load_lattice_proto_modules


def _status(name: str, status: str, detail: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


async def _entity_smoke(channel: grpc.aio.Channel, proto_modules: Any) -> dict[str, str]:
    stub = proto_modules.entity_api_grpc.EntityManagerAPIStub(channel)
    entity_id = "fastdis-zorn-grpc-probe-entity"
    entity = proto_modules.entity.Entity(
        entity_id=entity_id,
        description="FastDIS Zorn gRPC probe entity",
        is_live=True,
        no_expiry=True,
    )
    await stub.PublishEntity(proto_modules.entity_api.PublishEntityRequest(entity=entity))
    response = await stub.GetEntity(proto_modules.entity_api.GetEntityRequest(entity_id=entity_id))
    response_dict = MessageToDict(response, preserving_proto_field_name=True)
    if entity_id not in json.dumps(response_dict):
        return _status("entity_publish_get", "failed", json.dumps(response_dict, sort_keys=True))
    return _status("entity_publish_get", "passed", "PublishEntity/GetEntity succeeded")


async def _task_smoke(channel: grpc.aio.Channel, proto_modules: Any) -> list[dict[str, str]]:
    if proto_modules.task is None:
        return [_status("task_create", "skipped", "task protobuf module was not available")]
    stub = proto_modules.task_api_grpc.TaskManagerAPIStub(channel)
    task_module = proto_modules.task
    task_id = "fastdis-zorn-grpc-probe-task"
    assignee_id = "fastdis-zorn-grpc-probe-agent"
    checks: list[dict[str, str]] = []
    request = proto_modules.task_api.CreateTaskRequest(
        task_id=task_id,
        display_name="FastDIS Zorn gRPC probe task",
        description="FastDIS Zorn gRPC probe task",
        relations=task_module.Relations(
            assignee=task_module.Principal(
                system=task_module.System(entity_id=assignee_id)
            )
        ),
    )
    try:
        response = await stub.CreateTask(request)
    except Exception as exc:  # noqa: BLE001
        return [_status("task_create", "failed", str(exc))]
    response_dict = MessageToDict(response, preserving_proto_field_name=True)
    if response.task.version.task_id != task_id:
        return [_status("task_create", "failed", json.dumps(response_dict, sort_keys=True))]
    checks.append(_status("task_create", "passed", json.dumps(response_dict, sort_keys=True)))

    try:
        updated = await stub.UpdateStatus(
            proto_modules.task_api.UpdateStatusRequest(
                status_update=task_module.StatusUpdate(
                    version=task_module.TaskVersion(
                        task_id=task_id,
                        status_version=1,
                    ),
                    status=task_module.TaskStatus(
                        status=task_module.STATUS_EXECUTING,
                    ),
                )
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(_status("task_update_status", "failed", str(exc)))
        return checks
    if updated.task.version.task_id != task_id or updated.task.status.status != task_module.STATUS_EXECUTING:
        checks.append(
            _status(
                "task_update_status",
                "failed",
                json.dumps(MessageToDict(updated, preserving_proto_field_name=True), sort_keys=True),
            )
        )
        return checks
    updated_dict = MessageToDict(updated, preserving_proto_field_name=True)
    checks.append(_status("task_update_status", "passed", json.dumps(updated_dict, sort_keys=True)))

    listen_call = None
    try:
        listen_call = stub.ListenAsAgent(
            proto_modules.task_api.ListenAsAgentRequest(
                entity_ids=proto_modules.task_api.EntityIds(entity_ids=[assignee_id]),
                heartbeat_interval_ms=0,
            )
        )
        listen_response = await asyncio.wait_for(listen_call.read(), timeout=2)
    except Exception as exc:  # noqa: BLE001
        checks.append(_status("task_listen_as_agent", "failed", str(exc)))
        return checks
    finally:
        if listen_call is not None:
            try:
                listen_call.cancel()
            except Exception:  # noqa: BLE001
                pass
    listen_dict = MessageToDict(listen_response, preserving_proto_field_name=True)
    execute_task_id = (
        listen_dict.get("execute_request", {})
        .get("task", {})
        .get("version", {})
        .get("task_id")
    )
    if execute_task_id != task_id:
        checks.append(_status("task_listen_as_agent", "failed", json.dumps(listen_dict, sort_keys=True)))
        return checks
    checks.append(_status("task_listen_as_agent", "passed", json.dumps(listen_dict, sort_keys=True)))

    stream_call = None
    try:
        stream_call = stub.StreamTasks(
            proto_modules.task_api.StreamTasksRequest(
                heartbeat_interval_ms=0,
            )
        )
        first_stream = await asyncio.wait_for(stream_call.read(), timeout=2)
        await stub.CancelTask(
            proto_modules.task_api.CancelTaskRequest(task_id=task_id)
        )
        second_stream = await asyncio.wait_for(stream_call.read(), timeout=2)
    except Exception as exc:  # noqa: BLE001
        checks.append(_status("task_stream_tasks", "failed", str(exc)))
        return checks
    finally:
        if stream_call is not None:
            try:
                stream_call.cancel()
            except Exception:  # noqa: BLE001
                pass
    first_stream_dict = MessageToDict(first_stream, preserving_proto_field_name=True)
    second_stream_dict = MessageToDict(second_stream, preserving_proto_field_name=True)
    first_task_id = first_stream_dict.get("task_event", {}).get("task", {}).get("version", {}).get("task_id")
    second_task_id = second_stream_dict.get("task_event", {}).get("task", {}).get("version", {}).get("task_id")
    if first_task_id != task_id or second_task_id != task_id:
        checks.append(
            _status(
                "task_stream_tasks",
                "failed",
                json.dumps({"first": first_stream_dict, "second": second_stream_dict}, sort_keys=True),
            )
        )
        return checks
    checks.append(
        _status(
            "task_stream_tasks",
            "passed",
            json.dumps({"first": first_stream_dict, "second": second_stream_dict}, sort_keys=True),
        )
    )

    try:
        canceled = await stub.GetTask(
            proto_modules.task_api.GetTaskRequest(task_id=task_id)
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(_status("task_cancel", "failed", str(exc)))
        return checks
    canceled_dict = MessageToDict(canceled, preserving_proto_field_name=True)
    if canceled.task.version.task_id != task_id or canceled.task.status.status != task_module.STATUS_DONE_NOT_OK:
        checks.append(_status("task_cancel", "failed", json.dumps(canceled_dict, sort_keys=True)))
        return checks
    checks.append(_status("task_cancel", "passed", json.dumps(canceled_dict, sort_keys=True)))
    return checks


async def run_probe(target: str) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    gaps: list[str] = []
    try:
        proto_modules = load_lattice_proto_modules()
        checks.append(_status("official_buf_modules", "passed", json.dumps(proto_modules.module_names(), sort_keys=True)))
    except Exception as exc:  # noqa: BLE001
        checks.append(_status("official_buf_modules", "failed", str(exc)))
        return {"overall_status": "failed", "checks": checks, "gaps": ["official Buf-generated Python packages are unavailable or mismatched"]}
    try:
        assert_lattice_grpc_contract(proto_modules)
        checks.append(_status("official_proto_contract", "passed", "EntityManagerAPI and TaskManagerAPI descriptors loaded"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_status("official_proto_contract", "failed", str(exc)))
        return {"overall_status": "failed", "checks": checks, "gaps": ["Zorn official proto contract audit failed"]}
    async with grpc.aio.insecure_channel(target) as channel:
        try:
            checks.append(await _entity_smoke(channel, proto_modules))
        except Exception as exc:  # noqa: BLE001
            checks.append(_status("entity_publish_get", "failed", str(exc)))
        checks.extend(await _task_smoke(channel, proto_modules))
    failed = [check for check in checks if check["status"] == "failed"]
    skipped = [check for check in checks if check["status"] == "skipped"]
    if failed:
        status = "failed"
    elif skipped:
        status = "ready-with-gaps"
        gaps.extend(check["detail"] for check in skipped)
    else:
        status = "ready"
    return {"overall_status": status, "checks": checks, "gaps": gaps}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = asyncio.run(run_probe(args.target))
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["overall_status"] in {"ready", "ready-with-gaps"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


if __name__ == "__main__":
    raise SystemExit(main())
