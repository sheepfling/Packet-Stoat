from __future__ import annotations

import sys
from pathlib import Path

import grpc
import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SRC = ROOT / "packages" / "lattice" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

from packet_stoat_lattice import RetryableGrpcError, run_with_retry  # noqa: E402


def test_lattice_grpc_retry_policy_retries_transient_failures() -> None:
    attempts = {"count": 0}

    def operation():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RetryableGrpcError(grpc.StatusCode.UNAVAILABLE)
        return "ok"

    result, used_attempts = run_with_retry(operation, max_attempts=3)

    assert result == "ok"
    assert used_attempts == 3


def test_lattice_grpc_retry_policy_does_not_retry_terminal_failures() -> None:
    attempts = {"count": 0}

    def operation():
        attempts["count"] += 1
        raise RetryableGrpcError(grpc.StatusCode.INVALID_ARGUMENT)

    with pytest.raises(grpc.RpcError):
        run_with_retry(operation, max_attempts=3)

    assert attempts["count"] == 1
