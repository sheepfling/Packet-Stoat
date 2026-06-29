from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


OBJECT_PATH_PATTERN = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")
TASK_STATUSES = {
    "queued",
    "sent",
    "received",
    "accepted",
    "rejected",
    "running",
    "in_progress",
    "completed",
    "failed",
    "cancel_requested",
    "cancelled",
}
TERMINAL_TASK_STATUSES = {"rejected", "completed", "failed", "cancelled"}


def _filtered_payload(payload: dict[str, Any], components_to_include: set[str] | None) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    if not components_to_include:
        return clone
    allowed = {"schema", "entityId", "entity_key", "source", "exercise_id", "force_id", "marking", "timestamp", "stale"}
    component_map = {
        "aliases": {"aliases"},
        "location": {"location", "pose"},
        "ontology": {"ontology", "track"},
        "milView": {"milView", "track"},
        "provenance": {"provenance"},
        "media": {"media"},
        "packetStoat": {"packetStoat"},
        "metadata": {"metadata"},
    }
    keep = set()
    for name in components_to_include:
        keep.update(component_map.get(name, set()))
    for key in list(clone.keys()):
        if key in allowed or key in keep:
            continue
        del clone[key]
    return clone


def entity_is_exportable_to_dis(payload: dict[str, Any]) -> bool:
    return loop_suppression_reason(payload) is None


def loop_suppression_reason(payload: dict[str, Any]) -> str | None:
    packet_stoat = payload.get("packetStoat")
    if isinstance(packet_stoat, dict) and packet_stoat.get("source") == "dis-ingress":
        return "packet-stoat.dis_ingress"
    provenance = payload.get("provenance")
    if isinstance(provenance, dict):
        if provenance.get("integrationName") == "packet-stoat" and provenance.get("dataType") == "dis.entity_state":
            return "packetstoat.dis_entity_state"
    return None


@dataclass
class ShimObjectRecord:
    path: str
    content_type: str
    size_bytes: int
    sha256: str
    created_at_unix_s: float
    updated_at_unix_s: float


@dataclass
class ShimTaskRecord:
    task_id: str
    agent_id: str
    task_type: str
    payload: dict[str, Any]
    status: str = "sent"
    created_at_unix_s: float = field(default_factory=time.time)
    updated_at_unix_s: float = field(default_factory=time.time)


class MockLatticeShim:
    def __init__(self) -> None:
        self._entities: dict[str, dict[str, Any]] = {}
        self._event_log: list[dict[str, Any]] = []
        self._objects: dict[str, tuple[bytes, ShimObjectRecord]] = {}
        self._tasks: dict[str, ShimTaskRecord] = {}

    def publish_entity(self, payload: dict[str, Any]) -> dict[str, Any]:
        entity_id = str(payload.get("entityId") or payload.get("entity_key") or "")
        if not entity_id:
            raise ValueError("entity payload requires entityId or entity_key")
        event_kind = "EntityUpdated" if entity_id in self._entities else "EntityPublished"
        if payload.get("stale"):
            event_kind = "EntityStale"
        stored = copy.deepcopy(payload)
        stored["_shim"] = {
            "revision": int(self._entities.get(entity_id, {}).get("_shim", {}).get("revision", 0)) + 1,
            "last_publish_unix_s": time.time(),
        }
        self._entities[entity_id] = stored
        event = {
            "sequence": len(self._event_log) + 1,
            "kind": event_kind,
            "entityId": entity_id,
            "timestamp_unix_s": time.time(),
            "payload": stored,
        }
        self._event_log.append(event)
        return {"status": "accepted", "backend": "shim", "entity_id": entity_id, "event_kind": event_kind}

    def publish_batch(self, payloads: list[dict[str, Any]]) -> dict[str, Any]:
        results = [self.publish_entity(payload) for payload in payloads]
        return {"accepted": len(results), "results": results}

    def list_entities(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(self._entities[key]) for key in sorted(self._entities)]

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        payload = self._entities.get(entity_id)
        return None if payload is None else copy.deepcopy(payload)

    def stream_entities(
        self,
        *,
        components_to_include: list[str] | None = None,
        heartbeat_interval_ms: int = 1000,
        pre_existing_only: bool = False,
        include_heartbeat: bool = True,
    ) -> list[dict[str, Any]]:
        component_set = set(components_to_include or [])
        events: list[dict[str, Any]] = []
        source = self.list_entities() if pre_existing_only else [event["payload"] for event in self._event_log if "payload" in event]
        for index, payload in enumerate(source, start=1):
            entity_id = str(payload.get("entityId") or payload.get("entity_key"))
            events.append(
                {
                    "kind": "EntityEvent",
                    "sequence": index,
                    "entityId": entity_id,
                    "payload": _filtered_payload(payload, component_set),
                }
            )
        if include_heartbeat:
            events.append(
                {
                    "kind": "Heartbeat",
                    "heartbeat_interval_ms": heartbeat_interval_ms,
                    "sequence": len(events) + 1,
                }
            )
        return events

    def exportable_entities_for_dis(self) -> list[dict[str, Any]]:
        return [payload for payload in self.list_entities() if entity_is_exportable_to_dis(payload)]

    def export_report_for_dis(self) -> dict[str, Any]:
        exportable: list[dict[str, Any]] = []
        suppressed: list[dict[str, Any]] = []
        for payload in self.list_entities():
            reason = loop_suppression_reason(payload)
            if reason is None:
                exportable.append(payload)
                continue
            suppressed.append(
                {
                    "entity_id": payload.get("entityId") or payload.get("entity_key"),
                    "reason": reason,
                }
            )
        return {
            "exportable": exportable,
            "suppressed": suppressed,
            "exportable_count": len(exportable),
            "suppressed_count": len(suppressed),
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "entity_count": len(self._entities),
            "event_count": len(self._event_log),
            "object_count": len(self._objects),
            "task_count": len(self._tasks),
        }

    def put_object(self, path: str, content_type: str, content: bytes) -> dict[str, Any]:
        _validate_object_path(path)
        content_bytes = bytes(content)
        now = time.time()
        record = ShimObjectRecord(
            path=path,
            content_type=content_type,
            size_bytes=len(content_bytes),
            sha256=hashlib.sha256(content_bytes).hexdigest(),
            created_at_unix_s=now,
            updated_at_unix_s=now,
        )
        self._objects[path] = (content_bytes, record)
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "ObjectPut",
                "path": path,
                "timestamp_unix_s": time.time(),
            }
        )
        return {"status": "accepted", "path": path, "size_bytes": record.size_bytes, "sha256": record.sha256}

    def get_object(self, path: str) -> bytes | None:
        entry = self._objects.get(path)
        return None if entry is None else entry[0]

    def get_object_metadata(self, path: str) -> dict[str, Any] | None:
        entry = self._objects.get(path)
        if entry is None:
            return None
        _content, record = entry
        return {
            "path": record.path,
            "content_type": record.content_type,
            "size_bytes": record.size_bytes,
            "sha256": record.sha256,
            "created_at_unix_s": record.created_at_unix_s,
            "updated_at_unix_s": record.updated_at_unix_s,
        }

    def delete_object(self, path: str) -> dict[str, Any]:
        if path not in self._objects:
            raise KeyError(f"object not found: {path}")
        del self._objects[path]
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "ObjectDeleted",
                "path": path,
                "timestamp_unix_s": time.time(),
            }
        )
        return {"status": "accepted", "path": path}

    def list_objects(self, prefix: str = "") -> list[dict[str, Any]]:
        rows = []
        for path, (_content, record) in sorted(self._objects.items()):
            if not path.startswith(prefix):
                continue
            rows.append(
                {
                    "path": record.path,
                    "content_type": record.content_type,
                    "size_bytes": record.size_bytes,
                    "sha256": record.sha256,
                    "created_at_unix_s": record.created_at_unix_s,
                    "updated_at_unix_s": record.updated_at_unix_s,
                }
            )
        return rows

    def link_object_to_entity_media(self, entity_id: str, object_path: str, *, label: str = "media") -> dict[str, Any]:
        _validate_object_path(object_path)
        if object_path not in self._objects:
            raise KeyError(f"object not found: {object_path}")
        payload = self._entities.get(entity_id)
        if payload is None:
            raise KeyError(f"entity not found: {entity_id}")
        media = copy.deepcopy(payload.get("media", {}))
        items = list(media.get("items", []))
        items.append({"relativePath": object_path, "label": label})
        media["items"] = items
        payload["media"] = media
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "EntityMediaOverride",
                "entityId": entity_id,
                "object_path": object_path,
                "timestamp_unix_s": time.time(),
                "payload": copy.deepcopy(payload),
            }
        )
        return {"status": "accepted", "entity_id": entity_id, "object_path": object_path}

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        task_id = str(task.get("task_id") or f"task-{len(self._tasks) + 1}")
        agent_id = str(task.get("agent_id", "packet-stoat"))
        now = time.time()
        record = ShimTaskRecord(
            task_id=task_id,
            agent_id=agent_id,
            task_type=str(task.get("task_type", "unknown")),
            payload=copy.deepcopy(task),
            created_at_unix_s=now,
            updated_at_unix_s=now,
        )
        self._tasks[task_id] = record
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "TaskExecute",
                "task_id": task_id,
                "timestamp_unix_s": time.time(),
            }
        )
        return {"status": "accepted", "task_id": task_id}

    def stream_tasks(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        events = []
        for record in self._tasks.values():
            if agent_id is not None and record.agent_id != agent_id:
                continue
            events.append(
                {
                    "kind": "TaskExecute",
                    "task_id": record.task_id,
                    "agent_id": record.agent_id,
                    "task_type": record.task_type,
                    "status": record.status,
                    "payload": copy.deepcopy(record.payload),
                }
            )
        return events

    def list_tasks(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for record in self._tasks.values():
            if agent_id is not None and record.agent_id != agent_id:
                continue
            rows.append(
                {
                    "task_id": record.task_id,
                    "agent_id": record.agent_id,
                    "task_type": record.task_type,
                    "status": record.status,
                    "payload": copy.deepcopy(record.payload),
                    "created_at_unix_s": record.created_at_unix_s,
                }
            )
        return rows

    def update_task_status(self, task_id: str, status: str) -> dict[str, Any]:
        normalized = status.lower()
        if normalized not in TASK_STATUSES:
            raise ValueError(f"unsupported task status: {status}")
        record = self._tasks[task_id]
        if record.status in TERMINAL_TASK_STATUSES and normalized != record.status:
            raise ValueError(f"terminal task {task_id} cannot transition from {record.status} to {normalized}")
        record.status = normalized
        record.updated_at_unix_s = time.time()
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "TaskStatusUpdated",
                "task_id": task_id,
                "status": normalized,
                "timestamp_unix_s": time.time(),
            }
        )
        return {"status": "accepted", "task_id": task_id, "task_status": normalized}

    def expire_entities(self, *, now_ms: int | None = None) -> dict[str, Any]:
        current_ms = int(time.time() * 1000) if now_ms is None else now_ms
        expired: list[str] = []
        for entity_id, payload in list(self._entities.items()):
            if payload.get("noExpiry") is True:
                continue
            expiry_time = payload.get("expiryTime")
            if expiry_time is None or int(expiry_time) > current_ms:
                continue
            payload["stale"] = True
            payload["isLive"] = False
            expired.append(entity_id)
            self._event_log.append(
                {
                    "sequence": len(self._event_log) + 1,
                    "kind": "EntityExpired",
                    "entityId": entity_id,
                    "timestamp_unix_s": time.time(),
                    "payload": copy.deepcopy(payload),
                }
            )
        return {"expired_count": len(expired), "expired_entity_ids": expired}

    def simulate_restart(self, *, now_unix_s: float | None = None, no_expiry_republish_window_s: int = 300) -> dict[str, Any]:
        current = time.time() if now_unix_s is None else now_unix_s
        dropped: list[str] = []
        for entity_id, payload in list(self._entities.items()):
            if payload.get("noExpiry") is not True:
                continue
            last_publish = float(payload.get("_shim", {}).get("last_publish_unix_s", 0.0))
            if current - last_publish <= no_expiry_republish_window_s:
                continue
            del self._entities[entity_id]
            dropped.append(entity_id)
            self._event_log.append(
                {
                    "sequence": len(self._event_log) + 1,
                    "kind": "EntityDroppedAfterRestart",
                    "entityId": entity_id,
                    "timestamp_unix_s": time.time(),
                }
            )
        return {"dropped_count": len(dropped), "dropped_entity_ids": dropped}

    def write_event_log_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for event in self._event_log:
                handle.write(json.dumps(event, sort_keys=True))
                handle.write("\n")


def _validate_object_path(path: str) -> None:
    if not path or path.startswith("/") or path.endswith("/") or not OBJECT_PATH_PATTERN.match(path):
        raise ValueError("object path must use slash-separated A-Z a-z 0-9 . _ - segments")


__all__ = [
    "MockLatticeShim",
    "entity_is_exportable_to_dis",
    "loop_suppression_reason",
]
