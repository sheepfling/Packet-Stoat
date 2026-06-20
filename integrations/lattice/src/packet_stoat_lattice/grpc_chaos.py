from __future__ import annotations

from dataclasses import dataclass, field

import grpc


@dataclass
class GrpcShimChaos:
    publish_statuses: list[grpc.StatusCode] = field(default_factory=list)
    stream_statuses: list[grpc.StatusCode] = field(default_factory=list)

    def pop_publish_status(self) -> grpc.StatusCode | None:
        if not self.publish_statuses:
            return None
        return self.publish_statuses.pop(0)

    def pop_stream_status(self) -> grpc.StatusCode | None:
        if not self.stream_statuses:
            return None
        return self.stream_statuses.pop(0)


class RetryableGrpcError(grpc.RpcError):
    def __init__(self, status_code: grpc.StatusCode) -> None:
        super().__init__()
        self._status_code = status_code

    def code(self):
        return self._status_code


__all__ = ["GrpcShimChaos", "RetryableGrpcError"]
