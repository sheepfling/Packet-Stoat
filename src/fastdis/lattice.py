from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .tools._shared import EntityStateSpec, make_entity_state_packet


@dataclass(frozen=True)
class CanonicalEntityId:
    site: int
    application: int
    entity: int


@dataclass(frozen=True)
class CanonicalEntity:
    entity_id: CanonicalEntityId
    source: str = "mock-lattice"
    exercise_id: int = 1
    force_id: int = 0
    marking: str = "FASTDIS"
    entity_type: tuple[int, int, int, int, int, int, int] = (1, 2, 840, 3, 4, 5, 6)
    alternate_entity_type: tuple[int, int, int, int, int, int, int] = (1, 2, 840, 3, 4, 5, 6)
    timestamp: int = 0x10000000
    location_ecef_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation_dis_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity_mps: tuple[float, float, float] = (0.0, 0.0, 0.0)
    appearance: int = 0
    stale: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.entity_id.site}:{self.entity_id.application}:{self.entity_id.entity}"


@dataclass(frozen=True)
class MockPublishConfig:
    reject_entity_keys: frozenset[str] = frozenset()
    reject_stale: bool = False
    fail_after: int | None = None
    timeout_after: int | None = None
    timeout_message: str = "mock timeout"


@dataclass(frozen=True)
class MockPublishResult:
    entity_key: str
    status: str
    reason: str | None = None
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class MockPublishReport:
    publisher: str
    started_at_unix_s: float
    finished_at_unix_s: float
    attempted: int
    accepted: int
    rejected: int
    failed: int
    timed_out: bool
    results: tuple[MockPublishResult, ...]


def canonical_entity_from_dict(payload: dict[str, Any]) -> CanonicalEntity:
    entity_id_payload = payload["entity_id"]
    entity_type = tuple(int(value) for value in payload.get("entity_type", (1, 2, 840, 3, 4, 5, 6)))
    return CanonicalEntity(
        entity_id=CanonicalEntityId(
            site=int(entity_id_payload["site"]),
            application=int(entity_id_payload["application"]),
            entity=int(entity_id_payload["entity"]),
        ),
        source=str(payload.get("source", "mock-lattice")),
        exercise_id=int(payload.get("exercise_id", 1)),
        force_id=int(payload.get("force_id", 0)),
        marking=str(payload.get("marking", "FASTDIS")),
        entity_type=entity_type,
        alternate_entity_type=tuple(int(value) for value in payload.get("alternate_entity_type", entity_type)),
        timestamp=int(payload.get("timestamp", 0x10000000)),
        location_ecef_m=tuple(float(value) for value in payload.get("location_ecef_m", (0.0, 0.0, 0.0))),
        orientation_dis_deg=tuple(float(value) for value in payload.get("orientation_dis_deg", (0.0, 0.0, 0.0))),
        velocity_mps=tuple(float(value) for value in payload.get("velocity_mps", (0.0, 0.0, 0.0))),
        appearance=int(payload.get("appearance", 0)),
        stale=bool(payload.get("stale", False)),
        metadata=dict(payload.get("metadata", {})),
    )


def canonical_entity_to_dict(entity: CanonicalEntity) -> dict[str, Any]:
    payload = asdict(entity)
    payload["entity_id"] = asdict(entity.entity_id)
    return payload


def canonical_entity_to_lattice_payload(entity: CanonicalEntity) -> dict[str, Any]:
    entity_id = (
        f"packet-stoat:dis:v7:ex{entity.exercise_id}:"
        f"site{entity.entity_id.site}:app{entity.entity_id.application}:entity{entity.entity_id.entity}"
    )
    return {
        "schema": "fastdis.mock-lattice.track.v1",
        "entityId": entity_id,
        "entity_key": entity.key,
        "source": entity.source,
        "exercise_id": entity.exercise_id,
        "force_id": entity.force_id,
        "marking": entity.marking,
        "entity_type": list(entity.entity_type),
        "timestamp": entity.timestamp,
        "stale": entity.stale,
        "pose": {
            "location_ecef_m": list(entity.location_ecef_m),
            "orientation_dis_deg": {
                "psi": entity.orientation_dis_deg[0],
                "theta": entity.orientation_dis_deg[1],
                "phi": entity.orientation_dis_deg[2],
            },
            "velocity_mps": list(entity.velocity_mps),
        },
        "provenance": {
            "integrationName": "packet-stoat",
            "dataType": "dis.entity_state",
            "sourceUpdateTime": entity.timestamp,
        },
        "packetStoat": {
            "source": entity.source,
            "dis": {
                "exerciseId": entity.exercise_id,
                "siteId": entity.entity_id.site,
                "applicationId": entity.entity_id.application,
                "entityId": entity.entity_id.entity,
            },
        },
        "metadata": dict(entity.metadata),
    }


def canonical_entity_to_entity_state_spec(entity: CanonicalEntity) -> EntityStateSpec:
    return EntityStateSpec(
        site=entity.entity_id.site,
        application=entity.entity_id.application,
        entity=entity.entity_id.entity,
        force_id=entity.force_id,
        exercise_id=entity.exercise_id,
        marking=entity.marking,
        entity_type=entity.entity_type,
        alternate_entity_type=entity.alternate_entity_type,
        velocity_mps=entity.velocity_mps,
        location_ecef_m=entity.location_ecef_m,
        orientation_dis_deg=entity.orientation_dis_deg,
        appearance=entity.appearance,
        timestamp=entity.timestamp,
    )


def canonical_entity_to_entity_state_packet(entity: CanonicalEntity) -> bytes:
    return make_entity_state_packet(canonical_entity_to_entity_state_spec(entity))


def canonical_entity_from_transform(transform, *, source: str = "dis-ingress", metadata: dict[str, Any] | None = None) -> CanonicalEntity:
    entity_id = CanonicalEntityId(
        site=int(transform.entity_id[0]),
        application=int(transform.entity_id[1]),
        entity=int(transform.entity_id[2]),
    )
    return CanonicalEntity(
        entity_id=entity_id,
        source=source,
        exercise_id=int(transform.exercise_id),
        force_id=int(transform.force_id),
        marking=f"DIS-{entity_id.site}-{entity_id.application}-{entity_id.entity}",
        timestamp=int(transform.timestamp),
        location_ecef_m=tuple(float(value) for value in transform.location),
        orientation_dis_deg=tuple(math.degrees(float(value)) for value in transform.orientation),
        velocity_mps=tuple(float(value) for value in transform.linear_velocity),
        appearance=int(transform.appearance),
        metadata=dict(metadata or {}),
    )


def canonical_entity_from_snapshot(snapshot, *, source: str = "dis-ingress", metadata: dict[str, Any] | None = None) -> CanonicalEntity:
    combined_metadata = {
        "first_seen_tick": int(snapshot.first_seen_tick),
        "last_seen_tick": int(snapshot.last_seen_tick),
        "update_count": int(snapshot.update_count),
        "change_flags": int(snapshot.change_flags),
    }
    if metadata:
        combined_metadata.update(metadata)
    return canonical_entity_from_transform(snapshot.transform, source=source, metadata=combined_metadata)


def load_canonical_entities(path: Path) -> list[CanonicalEntity]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("entities", [])
    else:
        rows = payload
    return [canonical_entity_from_dict(dict(row)) for row in rows]


def mock_publish_report_to_dict(report: MockPublishReport) -> dict[str, Any]:
    return {
        "publisher": report.publisher,
        "started_at_unix_s": report.started_at_unix_s,
        "finished_at_unix_s": report.finished_at_unix_s,
        "attempted": report.attempted,
        "accepted": report.accepted,
        "rejected": report.rejected,
        "failed": report.failed,
        "timed_out": report.timed_out,
        "results": [asdict(result) for result in report.results],
    }


class MockLatticePublisher:
    def __init__(self, config: MockPublishConfig | None = None, *, publisher_name: str = "mock-lattice-publisher") -> None:
        self._config = config or MockPublishConfig()
        self.publisher_name = publisher_name
        self.published_payloads: list[dict[str, Any]] = []

    def publish(self, entities: list[CanonicalEntity]) -> MockPublishReport:
        started = time.time()
        results: list[MockPublishResult] = []
        accepted = 0
        rejected = 0
        failed = 0
        timed_out = False
        for index, entity in enumerate(entities):
            ordinal = index + 1
            if self._config.timeout_after is not None and ordinal > self._config.timeout_after:
                timed_out = True
                failed += 1
                results.append(
                    MockPublishResult(
                        entity_key=entity.key,
                        status="timeout",
                        reason=self._config.timeout_message,
                    )
                )
                break
            if self._config.fail_after is not None and ordinal > self._config.fail_after:
                failed += 1
                results.append(
                    MockPublishResult(
                        entity_key=entity.key,
                        status="failed",
                        reason="mock failure",
                    )
                )
                continue
            if entity.key in self._config.reject_entity_keys:
                rejected += 1
                results.append(
                    MockPublishResult(
                        entity_key=entity.key,
                        status="rejected",
                        reason="entity key rejected by config",
                    )
                )
                continue
            if self._config.reject_stale and entity.stale:
                rejected += 1
                results.append(
                    MockPublishResult(
                        entity_key=entity.key,
                        status="rejected",
                        reason="stale entity rejected by config",
                    )
                )
                continue
            payload = canonical_entity_to_lattice_payload(entity)
            self.published_payloads.append(payload)
            accepted += 1
            results.append(
                MockPublishResult(
                    entity_key=entity.key,
                    status="accepted",
                    payload=payload,
                )
            )
        finished = time.time()
        return MockPublishReport(
            publisher=self.publisher_name,
            started_at_unix_s=started,
            finished_at_unix_s=finished,
            attempted=len(entities),
            accepted=accepted,
            rejected=rejected,
            failed=failed,
            timed_out=timed_out,
            results=tuple(results),
        )


__all__ = [
    "CanonicalEntity",
    "CanonicalEntityId",
    "MockLatticePublisher",
    "MockPublishConfig",
    "MockPublishReport",
    "MockPublishResult",
    "canonical_entity_from_dict",
    "canonical_entity_from_snapshot",
    "canonical_entity_from_transform",
    "canonical_entity_to_dict",
    "canonical_entity_to_entity_state_packet",
    "canonical_entity_to_entity_state_spec",
    "canonical_entity_to_lattice_payload",
    "load_canonical_entities",
    "mock_publish_report_to_dict",
]
