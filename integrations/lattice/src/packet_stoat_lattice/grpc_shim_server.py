from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import time

import grpc

from .grpc_chaos import GrpcShimChaos
from .grpc_runtime import load_lattice_shim_modules
from .mock_shim import MockLatticeShim


pb2, pb2_grpc = load_lattice_shim_modules()


def _event_type(event: dict[str, object], *, preexisting_only: bool) -> str:
    kind = str(event.get("kind", ""))
    if kind == "Heartbeat":
        return "HEARTBEAT"
    if preexisting_only:
        return "PREEXISTING"
    payload = event.get("payload")
    if isinstance(payload, dict) and payload.get("stale"):
        return "DELETED"
    return "UPDATE"


def _public_stream_payload(payload: dict[str, object], request) -> dict[str, object]:
    if request.include_all_components:
        return payload
    clone = dict(payload)
    requested = set(request.components_to_include)
    if "location" in requested and "location" in clone:
        clone.pop("pose", None)
    if ("ontology" in requested or "milView" in requested) and "ontology" in clone and "milView" in clone:
        clone.pop("track", None)
    return clone


class LatticeShimServicer(pb2_grpc.LatticeShimServicer):
    def __init__(self, shim: MockLatticeShim | None = None, *, chaos: GrpcShimChaos | None = None) -> None:
        self.shim = shim or MockLatticeShim()
        self.chaos = chaos or GrpcShimChaos()

    def PublishEntities(self, request_iterator, context):
        status = self.chaos.pop_publish_status()
        if status is not None:
            context.abort(status, f"chaos injected publish status: {status.name}")
        received = 0
        accepted = 0
        rejected = 0
        coalesced = 0
        dropped = 0
        seen: set[str] = set()
        for request in request_iterator:
            received += 1
            try:
                payload = json.loads(request.entity_json)
            except json.JSONDecodeError:
                rejected += 1
                continue
            entity_id = str(payload.get("entityId") or payload.get("entity_key") or "")
            if not entity_id:
                rejected += 1
                continue
            if entity_id in seen or self.shim.get_entity(entity_id) is not None:
                coalesced += 1
            seen.add(entity_id)
            result = self.shim.publish_entity(payload)
            if result.get("status") == "accepted":
                accepted += 1
            else:
                dropped += 1
        return pb2.PublishEntitiesSummary(
            received=received,
            accepted=accepted,
            rejected=rejected,
            coalesced=coalesced,
            dropped=dropped,
        )

    def StreamEntityComponents(self, request, context):
        status = self.chaos.pop_stream_status()
        if status is not None:
            context.abort(status, f"chaos injected stream status: {status.name}")
        components = None if request.include_all_components else list(request.components_to_include)
        events = self.shim.stream_entities(
            components_to_include=components,
            heartbeat_interval_ms=int(request.heartbeat_period_millis or 1000),
            pre_existing_only=bool(request.preexisting_only),
            include_heartbeat=True,
        )
        last_timestamp_by_entity: dict[str, int] = {}
        for sequence, event in enumerate(events, start=1):
            entity_id = str(event.get("entityId", ""))
            payload = event.get("payload")
            if isinstance(payload, dict):
                payload = _public_stream_payload(payload, request)
            if request.update_per_entity_limit_ms and isinstance(payload, dict) and entity_id:
                logical_timestamp = int(payload.get("timestamp", 0))
                last_timestamp = last_timestamp_by_entity.get(entity_id)
                if last_timestamp is not None and (logical_timestamp - last_timestamp) < int(request.update_per_entity_limit_ms):
                    continue
                last_timestamp_by_entity[entity_id] = logical_timestamp
            yield pb2.StreamEntityComponentsResponse(
                event_type=_event_type(event, preexisting_only=bool(request.preexisting_only)),
                entity_id=entity_id,
                entity_json="" if payload is None else json.dumps(payload, sort_keys=True),
                server_sequence=sequence,
                server_emit_unix_ns=time.time_ns(),
            )


def start_grpc_shim_server(
    *, shim: MockLatticeShim | None = None, chaos: GrpcShimChaos | None = None
) -> tuple[grpc.Server, str, MockLatticeShim]:
    active_shim = shim or MockLatticeShim()
    server = grpc.server(ThreadPoolExecutor(max_workers=8))
    pb2_grpc.add_LatticeShimServicer_to_server(LatticeShimServicer(active_shim, chaos=chaos), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    return server, f"127.0.0.1:{port}", active_shim


__all__ = ["LatticeShimServicer", "start_grpc_shim_server", "pb2", "pb2_grpc"]
