from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class JsonlPublisher:
    def __init__(self, path: Path) -> None:
        self.path = path

    def publish_entity(self, payload: dict[str, object]) -> dict[str, object]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
        return {"status": "accepted", "backend": "jsonl", "entity_key": payload.get("entity_key")}


class HttpMockPublisher:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def publish_entity(self, payload: dict[str, object]) -> dict[str, object]:
        self.payloads.append(payload)
        return {"status": "accepted", "backend": "http-mock", "entity_key": payload.get("entity_key")}


class NotConfiguredError(RuntimeError):
    pass


@dataclass(frozen=True)
class RealLatticeConfig:
    endpoint: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    token: str | None = None
    dry_run: bool = True

    @classmethod
    def from_env(cls) -> "RealLatticeConfig":
        return cls(
            endpoint=os.environ.get("LATTICE_ENDPOINT") or os.environ.get("LATTICE_BASE_URL"),
            client_id=os.environ.get("LATTICE_CLIENT_ID"),
            client_secret=os.environ.get("LATTICE_CLIENT_SECRET"),
            token=os.environ.get("LATTICE_TOKEN"),
            dry_run=(os.environ.get("LATTICE_DRY_RUN", "1") != "0"),
        )

    def is_configured(self) -> bool:
        if self.endpoint and self.token:
            return True
        return bool(self.endpoint and self.client_id and self.client_secret)

    def auth_mode(self) -> str:
        if self.token:
            return "token"
        if self.client_id and self.client_secret:
            return "client-credentials"
        return "unconfigured"

    def redacted(self) -> dict[str, object]:
        return {
            "endpoint": self.endpoint,
            "client_id": self.client_id,
            "client_secret_present": bool(self.client_secret),
            "token_present": bool(self.token),
            "dry_run": self.dry_run,
            "auth_mode": self.auth_mode(),
            "configured": self.is_configured(),
        }


class RealLatticePublisher:
    def __init__(self, config: RealLatticeConfig | None = None) -> None:
        self.config = config or RealLatticeConfig.from_env()
        if not self.config.dry_run and not self.config.is_configured():
            raise NotConfiguredError(
                "real Lattice publisher is not configured; provide endpoint plus token or client credentials"
            )

    def config_snapshot(self) -> dict[str, object]:
        return self.config.redacted()

    def _require_live_config(self) -> None:
        if self.config.dry_run:
            return
        if not self.config.is_configured():
            raise NotConfiguredError(
                "live Lattice transport requires endpoint plus token or client credentials"
            )

    def publish_entity(self, payload: dict[str, object]) -> dict[str, object]:
        self._require_live_config()
        return {
            "status": "dry-run" if self.config.dry_run else "unimplemented",
            "backend": "real-lattice",
            "entity_key": payload.get("entity_key"),
            "config": self.config_snapshot(),
            "reason": "real SDK transport is intentionally deferred until sandbox credentials exist",
        }

    def publish_entities(self, payloads: list[dict[str, Any]]) -> dict[str, object]:
        self._require_live_config()
        return {
            "status": "dry-run" if self.config.dry_run else "unimplemented",
            "backend": "real-lattice",
            "count": len(payloads),
            "config": self.config_snapshot(),
            "reason": "batch publish is stubbed until sandbox credentials and SDK transport exist",
        }

    def stream_entities(self, **kwargs: Any) -> dict[str, object]:
        self._require_live_config()
        return {
            "status": "dry-run" if self.config.dry_run else "unimplemented",
            "backend": "real-lattice",
            "operation": "stream_entities",
            "kwargs": dict(kwargs),
            "config": self.config_snapshot(),
            "reason": "streaming remains a dry-run stub until sandbox access exists",
        }

    def put_object(self, path: str, content_type: str, content: bytes) -> dict[str, object]:
        self._require_live_config()
        return {
            "status": "dry-run" if self.config.dry_run else "unimplemented",
            "backend": "real-lattice",
            "operation": "put_object",
            "path": path,
            "content_type": content_type,
            "size_bytes": len(content),
            "config": self.config_snapshot(),
            "reason": "object upload remains a dry-run stub until sandbox access exists",
        }

    def stream_tasks(self, **kwargs: Any) -> dict[str, object]:
        self._require_live_config()
        return {
            "status": "dry-run" if self.config.dry_run else "unimplemented",
            "backend": "real-lattice",
            "operation": "stream_tasks",
            "kwargs": dict(kwargs),
            "config": self.config_snapshot(),
            "reason": "task streaming remains a dry-run stub until sandbox access exists",
        }
