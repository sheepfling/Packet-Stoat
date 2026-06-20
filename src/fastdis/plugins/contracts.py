from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Protocol


class PacketSource(Protocol):
    name: str

    def packets(self) -> Iterator[bytes]:
        ...


class EntityPublisher(Protocol):
    name: str

    def publish(self, entities: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
        ...


class EntityStream(Protocol):
    name: str

    def stream(self) -> Iterator[Mapping[str, Any]]:
        ...


class Consumer(Protocol):
    name: str

    def consume(self, entities: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
        ...


class Workflow(Protocol):
    name: str

    def run(self, args: list[str] | None = None) -> int:
        ...


__all__ = [
    "Consumer",
    "EntityPublisher",
    "EntityStream",
    "PacketSource",
    "Workflow",
]
