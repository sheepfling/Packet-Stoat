from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

from .interop import (
    CanonicalEntity,
    CanonicalEntityId,
    canonical_entity_from_dict,
    canonical_entity_from_entity_state_packet,
    canonical_entity_from_snapshot,
    canonical_entity_from_transform,
    canonical_entity_to_dict,
    canonical_entity_to_entity_state_packet,
    canonical_entity_to_entity_state_spec,
    entity_type_tuple,
    load_canonical_entities,
    vec3_tuple,
)


DEFAULT_LATTICE_EXPIRY_OFFSET = 60_000


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


def canonical_entity_to_lattice_payload(entity: CanonicalEntity) -> dict[str, Any]:
    kind = _platform_kind(entity)
    disposition = _force_disposition(entity.force_id)
    environment = _environment(kind)
    entity_id = (
        f"packet-stoat:dis:v7:ex{entity.exercise_id}:"
        f"site{entity.entity_id.site}:app{entity.entity_id.application}:entity{entity.entity_id.entity}"
    )
    provenance_data_type = "dis.entity_state" if entity.source == "dis-ingress" else "mock.track"
    dead_reckoning = dict(entity.metadata.get("dead_reckoning", {}))
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
        "isLive": not entity.stale,
        "expiryTime": entity.timestamp + DEFAULT_LATTICE_EXPIRY_OFFSET,
        "aliases": {
            "name": entity.marking,
        },
        "ontology": {
            "template": "track",
            "platformType": kind,
        },
        "milView": {
            "disposition": disposition,
            "environment": environment,
        },
        "location": {
            "position": {
                "ecefMeters": list(entity.location_ecef_m),
            },
            "velocityEcefMps": list(entity.velocity_mps),
            "attitudeDisDeg": {
                "psi": entity.orientation_dis_deg[0],
                "theta": entity.orientation_dis_deg[1],
                "phi": entity.orientation_dis_deg[2],
            },
        },
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
            "dataType": provenance_data_type,
            "sourceUpdateTime": entity.timestamp,
        },
        "packetStoat": {
            "source": entity.source,
            "deadReckoning": dead_reckoning,
            "dis": {
                "exerciseId": entity.exercise_id,
                "siteId": entity.entity_id.site,
                "applicationId": entity.entity_id.application,
                "entityId": entity.entity_id.entity,
            },
        },
        "metadata": dict(entity.metadata),
    }


def canonical_entity_from_lattice_payload(payload: dict[str, Any]) -> CanonicalEntity:
    entity_key = str(payload.get("entity_key") or "")
    if not entity_key:
        raise ValueError("Lattice-style payload requires entity_key for canonical recovery")
    site_text, app_text, entity_text = entity_key.split(":", 2)
    pose = payload.get("pose", {})
    location = payload.get("location", {})
    orientation = pose.get("orientation_dis_deg") or location.get("attitudeDisDeg", {})
    location_ecef = pose.get("location_ecef_m")
    if location_ecef is None:
        location_position = location.get("position", {})
        location_ecef = location_position.get("ecefMeters", (0.0, 0.0, 0.0))
    velocity_mps = pose.get("velocity_mps")
    if velocity_mps is None:
        velocity_mps = location.get("velocityEcefMps", (0.0, 0.0, 0.0))
    return CanonicalEntity(
        entity_id=CanonicalEntityId(
            site=int(site_text),
            application=int(app_text),
            entity=int(entity_text),
        ),
        source=str(payload.get("source", "mock-lattice")),
        exercise_id=int(payload.get("exercise_id", 1)),
        force_id=int(payload.get("force_id", 0)),
        marking=str(payload.get("marking", "FASTDIS")),
        entity_type=entity_type_tuple(payload.get("entity_type", (1, 2, 840, 3, 4, 5, 6))),
        alternate_entity_type=entity_type_tuple(payload.get("entity_type", (1, 2, 840, 3, 4, 5, 6))),
        timestamp=int(payload.get("timestamp", 0x10000000)),
        stale=bool(payload.get("stale", not bool(payload.get("isLive", True)))),
        location_ecef_m=vec3_tuple(location_ecef),
        orientation_dis_deg=(
            float(orientation.get("psi", 0.0)),
            float(orientation.get("theta", 0.0)),
            float(orientation.get("phi", 0.0)),
        ),
        velocity_mps=vec3_tuple(velocity_mps),
        metadata=dict(payload.get("metadata", {})),
    )


def _platform_kind(entity: CanonicalEntity) -> str:
    kind = int(entity.entity_type[0]) if entity.entity_type else 0
    domain = int(entity.entity_type[1]) if len(entity.entity_type) > 1 else 0
    if kind == 1 and domain == 2:
        return "aircraft"
    if kind == 1 and domain in {1, 3}:
        return "ground_vehicle"
    if kind == 1 and domain == 4:
        return "surface_vessel"
    return "unknown"


def _force_disposition(force_id: int) -> str:
    return {
        0: "other",
        1: "friendly",
        2: "opposing",
        3: "neutral",
    }.get(int(force_id), "unknown")


def _environment(platform_kind: str) -> str:
    return {
        "aircraft": "air",
        "surface_vessel": "sea",
        "ground_vehicle": "land",
    }.get(platform_kind, "unknown")


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
    "canonical_entity_from_entity_state_packet",
    "canonical_entity_from_lattice_payload",
    "canonical_entity_from_snapshot",
    "canonical_entity_from_transform",
    "canonical_entity_to_dict",
    "canonical_entity_to_entity_state_packet",
    "canonical_entity_to_entity_state_spec",
    "canonical_entity_to_lattice_payload",
    "load_canonical_entities",
    "mock_publish_report_to_dict",
]
