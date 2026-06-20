from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _filtered_payload(payload: dict[str, Any], components_to_include: set[str] | None) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    if not components_to_include:
        return clone
    allowed = {"schema", "entityId", "entity_key", "source", "exercise_id", "force_id", "marking", "timestamp", "stale"}
    component_map = {
        "aliases": "aliases",
        "location": "pose",
        "ontology": "track",
        "milView": "track",
        "provenance": "provenance",
        "packetStoat": "packetStoat",
        "metadata": "metadata",
    }
    keep = {component_map[name] for name in components_to_include if name in component_map}
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
    created_at_unix_s: float


@dataclass
class ShimTaskRecord:
    task_id: str
    agent_id: str
    task_type: str
    payload: dict[str, Any]
    status: str = "pending"
    created_at_unix_s: float = field(default_factory=time.time)


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
        source = self.list_entities() if pre_existing_only else [event["payload"] for event in self._event_log]
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
        record = ShimObjectRecord(
            path=path,
            content_type=content_type,
            size_bytes=len(content),
            created_at_unix_s=time.time(),
        )
        self._objects[path] = (bytes(content), record)
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "ObjectPut",
                "path": path,
                "timestamp_unix_s": time.time(),
            }
        )
        return {"status": "accepted", "path": path, "size_bytes": record.size_bytes}

    def get_object(self, path: str) -> bytes | None:
        entry = self._objects.get(path)
        return None if entry is None else entry[0]

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
                    "created_at_unix_s": record.created_at_unix_s,
                }
            )
        return rows

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        task_id = str(task.get("task_id") or f"task-{len(self._tasks) + 1}")
        agent_id = str(task.get("agent_id", "packet-stoat"))
        record = ShimTaskRecord(
            task_id=task_id,
            agent_id=agent_id,
            task_type=str(task.get("task_type", "unknown")),
            payload=copy.deepcopy(task),
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
        record = self._tasks[task_id]
        record.status = status
        self._event_log.append(
            {
                "sequence": len(self._event_log) + 1,
                "kind": "TaskStatusUpdated",
                "task_id": task_id,
                "status": status,
                "timestamp_unix_s": time.time(),
            }
        )
        return {"status": "accepted", "task_id": task_id, "task_status": status}

    def write_event_log_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for event in self._event_log:
                handle.write(json.dumps(event, sort_keys=True))
                handle.write("\n")


__all__ = ["MockLatticeShim", "entity_is_exportable_to_dis", "loop_suppression_reason"]
