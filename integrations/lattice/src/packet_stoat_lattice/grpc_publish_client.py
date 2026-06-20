from __future__ import annotations

import json
import time

import grpc

from .grpc_runtime import load_lattice_shim_modules


pb2, pb2_grpc = load_lattice_shim_modules()


def publish_entities(target: str, payloads: list[dict[str, object]], *, run_id: str = "packet-stoat-grpc"):
    with grpc.insecure_channel(target) as channel:
        stub = pb2_grpc.LatticeShimStub(channel)

        def iterator():
            for sequence, payload in enumerate(payloads, start=1):
                yield pb2.PublishEntityRequest(
                    run_id=run_id,
                    entity_json=json.dumps(payload, sort_keys=True),
                    client_sequence=sequence,
                    client_send_unix_ns=time.time_ns(),
                )

        summary = stub.PublishEntities(iterator())
    return {
        "received": int(summary.received),
        "accepted": int(summary.accepted),
        "rejected": int(summary.rejected),
        "coalesced": int(summary.coalesced),
        "dropped": int(summary.dropped),
    }


__all__ = ["publish_entities"]
