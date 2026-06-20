from __future__ import annotations

import json
import os
from pathlib import Path


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


class RealLatticePublisher:
    REQUIRED_ENV = ("LATTICE_BASE_URL", "LATTICE_CLIENT_ID", "LATTICE_CLIENT_SECRET")

    def __init__(self) -> None:
        missing = [name for name in self.REQUIRED_ENV if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                "real Lattice publisher is not configured; missing environment: " + ", ".join(missing)
            )

    def publish_entity(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "status": "unimplemented",
            "backend": "real-lattice",
            "entity_key": payload.get("entity_key"),
            "reason": "real SDK transport is intentionally deferred until sandbox credentials exist",
        }
