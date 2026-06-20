from __future__ import annotations

import grpc


RETRYABLE_STATUS_CODES = {
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.DEADLINE_EXCEEDED,
    grpc.StatusCode.RESOURCE_EXHAUSTED,
    grpc.StatusCode.CANCELLED,
}


def run_with_retry(operation, *, max_attempts: int = 3):
    attempts = 0
    while True:
        attempts += 1
        try:
            return operation(), attempts
        except grpc.RpcError as exc:
            if attempts >= max_attempts or exc.code() not in RETRYABLE_STATUS_CODES:
                raise


__all__ = ["RETRYABLE_STATUS_CODES", "run_with_retry"]
