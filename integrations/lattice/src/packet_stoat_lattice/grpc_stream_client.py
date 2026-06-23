from __future__ import annotations

import json

import grpc

from .grpc_runtime import load_lattice_shim_modules


pb2, pb2_grpc = load_lattice_shim_modules()


def stream_entity_components(
    target: str,
    *,
    components_to_include: list[str] | None = None,
    include_all_components: bool = False,
    heartbeat_period_millis: int = 1000,
    preexisting_only: bool = False,
    update_per_entity_limit_ms: int = 0,
    metadata: list[tuple[str, str]] | None = None,
) -> list[dict[str, object]]:
    with grpc.insecure_channel(target) as channel:
        stub = pb2_grpc.LatticeShimStub(channel)
        request = pb2.StreamEntityComponentsRequest(
            components_to_include=components_to_include or [],
            include_all_components=include_all_components,
            heartbeat_period_millis=heartbeat_period_millis,
            preexisting_only=preexisting_only,
            update_per_entity_limit_ms=update_per_entity_limit_ms,
        )
        responses = stub.StreamEntityComponents(request, metadata=metadata)
        rows = []
        for response in responses:
            rows.append(
                {
                    "event_type": response.event_type,
                    "entity_id": response.entity_id,
                    "entity_json": response.entity_json,
                    "payload": {} if not response.entity_json else json.loads(response.entity_json),
                    "server_sequence": int(response.server_sequence),
                    "server_emit_unix_ns": int(response.server_emit_unix_ns),
                }
            )
        return rows


__all__ = ["stream_entity_components"]
