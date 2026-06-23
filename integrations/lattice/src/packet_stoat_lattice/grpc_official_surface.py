from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any


SERVICE_MODULE_CANDIDATES = (
    "anduril.entitymanager.v1.entity_manager_api_pb2_grpc",
    "anduril.entitymanager.v1.entitymanager_api_pb2_grpc",
    "anduril.entitymanager.v1.entity_manager_pb2_grpc",
    "anduril.entitymanager.v1.entitymanager_pb2_grpc",
)
MESSAGE_MODULE_CANDIDATES = (
    "anduril.entitymanager.v1.entity_manager_api_pb2",
    "anduril.entitymanager.v1.entitymanager_api_pb2",
    "anduril.entitymanager.v1.entity_pb2",
    "anduril.entitymanager.v1.entitymanager_pb2",
)


def _try_import(name: str) -> ModuleType | None:
    try:
        return import_module(name)
    except ModuleNotFoundError:
        return None


def _available_attrs(module: ModuleType | None, attrs: tuple[str, ...]) -> list[str]:
    if module is None:
        return []
    return [attr for attr in attrs if hasattr(module, attr)]


def inspect_official_grpc_surface() -> dict[str, Any]:
    """Inspect optional Buf-generated Lattice gRPC Python modules.

    This never imports Packet-Stoat's shim modules. It only checks whether public
    Buf-generated modules are installed in the current environment and whether
    the names our future real backend needs are visible.
    """

    service_modules = {name: _try_import(name) for name in SERVICE_MODULE_CANDIDATES}
    message_modules = {name: _try_import(name) for name in MESSAGE_MODULE_CANDIDATES}
    imported_service = [name for name, module in service_modules.items() if module is not None]
    imported_messages = [name for name, module in message_modules.items() if module is not None]
    service_attrs = {
        name: _available_attrs(
            module,
            (
                "EntityManagerAPIStub",
                "EntityManagerAPIServicer",
                "add_EntityManagerAPIServicer_to_server",
            ),
        )
        for name, module in service_modules.items()
        if module is not None
    }
    message_attrs = {
        name: _available_attrs(
            module,
            (
                "Entity",
                "PublishEntitiesRequest",
                "PublishEntitiesResponse",
                "StreamEntityComponentsRequest",
                "StreamEntityComponentsResponse",
                "GetEntityRequest",
            ),
        )
        for name, module in message_modules.items()
        if module is not None
    }
    required_service_symbols = {"EntityManagerAPIStub"}
    required_message_symbols = {"PublishEntitiesRequest", "StreamEntityComponentsRequest"}
    found_service_symbols = {attr for attrs in service_attrs.values() for attr in attrs}
    found_message_symbols = {attr for attrs in message_attrs.values() for attr in attrs}
    status = "passed" if required_service_symbols <= found_service_symbols and required_message_symbols <= found_message_symbols else "skipped"
    return {
        "status": status,
        "source": "buf.build/anduril/lattice-sdk/sdks/main:grpc/python",
        "imported_service_modules": imported_service,
        "imported_message_modules": imported_messages,
        "service_attrs": service_attrs,
        "message_attrs": message_attrs,
        "required_service_symbols": sorted(required_service_symbols),
        "required_message_symbols": sorted(required_message_symbols),
        "remaining_if_skipped": [
            "install Buf-generated Lattice gRPC Python artifacts",
            "verify exact generated Python module names",
            "run official request object serialization against local fixtures",
        ],
    }


__all__ = ["MESSAGE_MODULE_CANDIDATES", "SERVICE_MODULE_CANDIDATES", "inspect_official_grpc_surface"]
