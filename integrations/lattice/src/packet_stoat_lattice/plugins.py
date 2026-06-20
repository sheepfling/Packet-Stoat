from __future__ import annotations

from pathlib import Path
from typing import Any

from .mock_shim import MockLatticeShim
from .publishers import HttpMockPublisher, JsonlPublisher, RealLatticePublisher


def jsonl_publisher(path: str | Path = "lattice_payloads.jsonl") -> JsonlPublisher:
    return JsonlPublisher(Path(path))


def mock_publisher() -> HttpMockPublisher:
    return HttpMockPublisher()


def real_publisher(**kwargs: Any) -> RealLatticePublisher:
    return RealLatticePublisher(**kwargs)


def shim_stream() -> MockLatticeShim:
    return MockLatticeShim()


def full_workflow():
    from fastdis.tools import lattice_shim

    return lattice_shim


__all__ = [
    "full_workflow",
    "jsonl_publisher",
    "mock_publisher",
    "real_publisher",
    "shim_stream",
]
