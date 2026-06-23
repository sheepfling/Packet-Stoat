#!/usr/bin/env python3
"""Credential-gated live Lattice route surface for FastDIS workflows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping
from urllib.parse import quote

import httpx


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ADAPTER_SRC = ROOT / "integrations" / "lattice" / "src"
for path in (SRC, ADAPTER_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fastdis.interop import CanonicalEntity, canonical_entity_to_dict, canonical_entity_to_entity_state_packet
from fastdis.lattice import canonical_entity_from_lattice_payload, canonical_entity_to_lattice_payload
from fastdis.replay import write_v1_packets
from packet_stoat_lattice.sdk_rest_compat import offline_client_config_from_env


DEFAULT_DIS_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "dis_entity_fixture.json"
DEFAULT_TRACK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "lattice_track_fixture.json"
DEFAULT_OBJECT_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "object_fixture.json"
DEFAULT_TASK_FIXTURE = ROOT / "integrations" / "lattice" / "examples" / "task_fixture.json"


@dataclass(frozen=True)
class LiveRouteConfig:
    base_url: str
    skip_tls_verify: bool
    sandboxes_token: str | None
    environment_token: str | None
    client_id: str | None
    client_secret: str | None

    @property
    def auth_mode(self) -> str:
        if self.environment_token:
            return "environment-token"
        if self.client_id and self.client_secret:
            return "client-credentials"
        return "missing"

    @property
    def is_ready(self) -> bool:
        return bool(self.base_url) and self.auth_mode != "missing"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Inspect live credential/env readiness")
    doctor.add_argument("--probe-auth", action="store_true", help="Attempt a live auth probe when credentials are present")

    dis = subparsers.add_parser("dis-to-shim", help="Publish canonical DIS fixture entities to a live Lattice endpoint")
    dis.add_argument("--fixture", type=Path, default=DEFAULT_DIS_FIXTURE)
    dis.add_argument("--out-dir", type=Path, required=True)

    shim = subparsers.add_parser("shim-to-dis", help="Round-trip a Lattice-shaped fixture through the live route and emit DIS replay")
    shim.add_argument("--fixture", type=Path, default=DEFAULT_TRACK_FIXTURE)
    shim.add_argument("--out-dir", type=Path, required=True)

    lab = subparsers.add_parser("lab-state", help="Exercise live object/task REST seams")
    lab.add_argument("--object-fixture", type=Path, default=DEFAULT_OBJECT_FIXTURE)
    lab.add_argument("--task-fixture", type=Path, default=DEFAULT_TASK_FIXTURE)
    lab.add_argument("--out-dir", type=Path, required=True)

    return parser.parse_args(argv)


def load_live_route_config(env: Mapping[str, str] | None = None) -> LiveRouteConfig:
    values = dict(env or {})
    offline = offline_client_config_from_env(values if values else None)
    source = values if values else None
    env_values = source or __import__("os").environ
    return LiveRouteConfig(
        base_url=offline.base_url.rstrip("/"),
        skip_tls_verify=offline.skip_tls_verify,
        sandboxes_token=offline.sandbox_token,
        environment_token=(env_values.get("ENVIRONMENT_TOKEN") or "").strip() or None,
        client_id=(env_values.get("LATTICE_CLIENT_ID") or "").strip() or None,
        client_secret=(env_values.get("LATTICE_CLIENT_SECRET") or "").strip() or None,
    )


def _load_fixture_payload(path: Path) -> list[CanonicalEntity]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "entities" in payload:
        from fastdis.interop import canonical_entity_from_dict

        rows = payload["entities"]
        return [canonical_entity_from_dict(dict(row)) for row in rows]
    if isinstance(payload, dict) and "entity_id" in payload:
        from fastdis.interop import canonical_entity_from_dict

        return [canonical_entity_from_dict(payload)]
    if isinstance(payload, dict) and "entity_key" in payload and "pose" in payload:
        return [canonical_entity_from_lattice_payload(payload)]
    if isinstance(payload, list):
        from fastdis.interop import canonical_entity_from_dict

        return [canonical_entity_from_dict(dict(row)) for row in payload]
    raise ValueError(f"unsupported fixture shape: {path}")


def _client(config: LiveRouteConfig) -> httpx.Client:
    return httpx.Client(verify=not config.skip_tls_verify, timeout=15.0)


def _headers(config: LiveRouteConfig, token: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if config.sandboxes_token:
        headers["Anduril-Sandbox-Authorization"] = f"Bearer {config.sandboxes_token}"
    return headers


def _fetch_access_token(config: LiveRouteConfig) -> str:
    if config.environment_token:
        return config.environment_token
    if not config.client_id or not config.client_secret:
        raise RuntimeError("missing live Lattice credentials")
    with _client(config) as client:
        response = client.post(
            f"{config.base_url}/api/v1/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": config.client_id,
                "client_secret": config.client_secret,
            },
            headers=_headers(config, None),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or "access_token" not in payload:
            raise RuntimeError("token response did not include access_token")
        return str(payload["access_token"])


def _doctor_payload(config: LiveRouteConfig, *, probe_auth: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "ready" if config.is_ready else "missing-prereqs",
        "base_url": config.base_url,
        "skip_tls_verify": config.skip_tls_verify,
        "auth_mode": config.auth_mode,
        "has_sandboxes_token": bool(config.sandboxes_token),
        "has_environment_token": bool(config.environment_token),
        "has_client_credentials": bool(config.client_id and config.client_secret),
    }
    if probe_auth and config.is_ready:
        try:
            token = _fetch_access_token(config)
            payload["auth_probe"] = "ok"
            payload["token_prefix"] = token[:16]
        except Exception as exc:  # noqa: BLE001
            payload["status"] = "probe-failed"
            payload["auth_probe"] = f"failed: {exc}"
    return payload


def command_doctor(args: argparse.Namespace) -> int:
    payload = _doctor_payload(load_live_route_config(), probe_auth=bool(args.probe_auth))
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "ready" else 2


def _entity_id_from_payload(payload: dict[str, Any]) -> str:
    value = payload.get("entityId")
    if not isinstance(value, str) or not value:
        raise RuntimeError("live entity payload missing entityId")
    return value


def command_dis_to_shim(args: argparse.Namespace) -> int:
    config = load_live_route_config()
    if not config.is_ready:
        print(json.dumps(_doctor_payload(config, probe_auth=False), indent=2))
        return 2
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fixture = args.fixture.resolve()
    entities = _load_fixture_payload(fixture)
    token = _fetch_access_token(config)
    published: list[dict[str, Any]] = []
    with _client(config) as client:
        for entity in entities:
            payload = canonical_entity_to_lattice_payload(entity)
            response = client.put(f"{config.base_url}/api/v1/entities", json=payload, headers=_headers(config, token))
            response.raise_for_status()
            body = response.json()
            published.append(body if isinstance(body, dict) else payload)
    summary = {
        "status": "ready",
        "fixture": str(fixture),
        "published_count": len(published),
        "base_url": config.base_url,
        "auth_mode": config.auth_mode,
    }
    path = out_dir / "dis_to_shim_report.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def command_shim_to_dis(args: argparse.Namespace) -> int:
    config = load_live_route_config()
    if not config.is_ready:
        print(json.dumps(_doctor_payload(config, probe_auth=False), indent=2))
        return 2
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fixture = args.fixture.resolve()
    entities = _load_fixture_payload(fixture)
    token = _fetch_access_token(config)
    observed: list[CanonicalEntity] = []
    with _client(config) as client:
        for entity in entities:
            payload = canonical_entity_to_lattice_payload(entity)
            publish = client.put(f"{config.base_url}/api/v1/entities", json=payload, headers=_headers(config, token))
            publish.raise_for_status()
            entity_id = _entity_id_from_payload(payload)
            response = client.get(
                f"{config.base_url}/api/v1/entities/{quote(entity_id, safe='')}",
                headers=_headers(config, token),
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise RuntimeError("live entity fetch response was not an object")
            observed.append(canonical_entity_from_lattice_payload(body))
    canonical_path = out_dir / "canonical_entities.json"
    replay_path = out_dir / "shim_to_dis.fastdispkt"
    canonical_path.write_text(
        json.dumps({"entities": [canonical_entity_to_dict(entity) for entity in observed]}, indent=2) + "\n",
        encoding="utf-8",
    )
    packets = [canonical_entity_to_entity_state_packet(entity) for entity in observed]
    write_v1_packets(replay_path, packets)
    summary = {
        "status": "ready",
        "fixture": str(fixture),
        "canonical_entities_path": str(canonical_path),
        "replay_path": str(replay_path),
        "entities_emitted": len(observed),
        "base_url": config.base_url,
        "auth_mode": config.auth_mode,
    }
    path = out_dir / "shim_to_dis_report.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def command_lab_state(args: argparse.Namespace) -> int:
    config = load_live_route_config()
    if not config.is_ready:
        print(json.dumps(_doctor_payload(config, probe_auth=False), indent=2))
        return 2
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    object_fixture = json.loads(args.object_fixture.resolve().read_text(encoding="utf-8"))
    task_fixture = json.loads(args.task_fixture.resolve().read_text(encoding="utf-8"))
    token = _fetch_access_token(config)
    operations = 0
    with _client(config) as client:
        for obj in object_fixture.get("objects", []):
            path = str(obj["path"])
            response = client.post(
                f"{config.base_url}/api/v1/objects/{quote(path, safe='')}",
                content=str(obj["content"]).encode("utf-8"),
                headers=_headers(config, token) | {"Content-Type": str(obj.get("content_type", "application/octet-stream"))},
            )
            response.raise_for_status()
            operations += 1
        for task in task_fixture.get("tasks", []):
            create = client.post(
                f"{config.base_url}/api/v1/tasks",
                json={
                    "taskId": task["task_id"],
                    "displayName": task["task_type"],
                    "description": task.get("task_type"),
                    "relations": {"assignee": {"entityId": task["agent_id"]}},
                    "specification": task.get("parameters", {}),
                },
                headers=_headers(config, token),
            )
            create.raise_for_status()
            operations += 1
    summary = {
        "status": "ready",
        "operations": operations,
        "base_url": config.base_url,
        "auth_mode": config.auth_mode,
    }
    path = out_dir / "lab_state_report.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "dis-to-shim":
        return command_dis_to_shim(args)
    if args.command == "shim-to-dis":
        return command_shim_to_dis(args)
    if args.command == "lab-state":
        return command_lab_state(args)
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
