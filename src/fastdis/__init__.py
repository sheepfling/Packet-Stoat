"""fastdis: callback-first DIS packet scanning.

The package is designed for high-rate packet pipelines where you usually do not
want to instantiate a deep Python object tree for every DIS PDU. The fast path
parses the fixed 12-byte header, filters/downsamples early, and calls Python
only for packets you keep.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import NamedTuple

from .message_set import MESSAGE_COVERAGE, MessageCoverage, find_message_coverage, unsupported_body_decoders
from .message_views import (
    MESSAGE_DESCRIPTORS,
    FieldVisit,
    GenericPduView,
    MessageDescriptor,
    find_message_descriptor,
    parse_many,
    parse_pdu,
    roundtrip_packet,
    serialize_pdu,
    visit_pdu_fields,
    walk_pdu_fields,
)
from .typed_pdus import (
    TYPED_PDU_DESCRIPTORS,
    TYPED_PDU_PARSERS,
    TYPED_PDU_SERIALIZERS,
    TypedPdu,
    TypedPduDescriptor,
    find_typed_pdu_descriptor,
    parse_many_typed,
    parse_typed_pdu,
    serialize_typed_pdu,
)
from .semantic_pdus import (
    SEMANTIC_PDU_DESCRIPTORS,
    SEMANTIC_PDU_PARSERS,
    SEMANTIC_PDU_SERIALIZERS,
    SemanticPdu,
    SemanticPduDescriptor,
    find_semantic_pdu_descriptor,
    parse_many_semantic,
    parse_semantic_pdu,
    serialize_semantic_pdu,
)
from .pdu_logging import (
    DIAGNOSTIC_CODES,
    PDU_LOG_DESCRIPTORS,
    FastDisLogEvent,
    FastDisPduLogDescriptor,
    PduLogAggregator,
    find_pdu_log_descriptor,
    format_log_summary,
    log_event_to_dict,
    log_event_to_json,
    make_pdu_log_event,
)
from .pdu_catalog import PDU_CATALOG, PduCatalogEntry, body_decoder_available, find_pdu, known_pdu_types
from .interop import (
    CanonicalEntity,
    CanonicalEntityId,
    canonical_entity_from_snapshot,
    canonical_entity_from_transform,
    canonical_entity_from_entity_state_packet,
    canonical_entity_to_entity_state_packet,
    load_canonical_entities,
)
from .lattice import (
    MockLatticePublisher,
    MockPublishConfig,
    canonical_entity_from_lattice_payload,
    canonical_entity_to_lattice_payload,
    mock_publish_report_to_dict,
)

FASTDIS_PROTOCOL_VERSION_DIS6 = 6
FASTDIS_PROTOCOL_VERSION_DIS7 = 7
FASTDIS_HEADER_STATUS_UNAVAILABLE = -1

try:
    __version__ = version("fastdis")
except PackageNotFoundError:
    __version__ = "0.15.0a5"


class Header(NamedTuple):
    version: int
    exercise_id: int
    pdu_type: int
    protocol_family: int
    timestamp: int
    length: int
    status: int
    padding: int

    @property
    def has_pdu_status(self) -> bool:
        return self.version >= FASTDIS_PROTOCOL_VERSION_DIS7

    @property
    def pdu_status(self) -> int | None:
        return self.status if self.has_pdu_status else None

    @property
    def padding_octet(self) -> int | None:
        return self.padding if self.has_pdu_status else None

    @property
    def legacy_padding(self) -> int | None:
        return None if self.has_pdu_status else self.padding


try:  # pragma: no cover - exercised when the optional extension builds
    from . import _cfast as _impl  # pyright: ignore[reportAttributeAccessIssue]

    HAS_C_ACCELERATOR = True
except Exception:  # pragma: no cover - pure-Python fallback path
    from . import _fallback as _impl

    HAS_C_ACCELERATOR = False

parse_header_tuple = _impl.parse_header
scan_many = _impl.scan_many
count_by_type = _impl.count_by_type


def parse_header(data: bytes | bytearray | memoryview, strict: bool = True) -> Header | None:
    """Return a named header object for ergonomic use.

    Use :func:`parse_header_tuple` or :func:`scan_many` in hot loops to avoid
    creating named Python objects.
    """

    parsed = parse_header_tuple(data, strict=strict)
    if parsed is None:
        return None
    return Header(*parsed)


def load_shared_library(path: str | None = None):
    """Load the optional DLL/shared-object C ABI wrapper.

    This is separate from the default CPython accelerator. Use it when you want
    to exercise the same shared library that an engine integration would call.
    """

    from .native import load_shared_library as _load_shared_library

    return _load_shared_library(path)


__all__ = [
    "FASTDIS_HEADER_STATUS_UNAVAILABLE",
    "FASTDIS_PROTOCOL_VERSION_DIS6",
    "FASTDIS_PROTOCOL_VERSION_DIS7",
    "DIAGNOSTIC_CODES",
    "HAS_C_ACCELERATOR",
    "__version__",
    "CanonicalEntity",
    "CanonicalEntityId",
    "Header",
    "MESSAGE_COVERAGE",
    "SEMANTIC_PDU_DESCRIPTORS",
    "SEMANTIC_PDU_PARSERS",
    "SEMANTIC_PDU_SERIALIZERS",
    "TYPED_PDU_DESCRIPTORS",
    "TYPED_PDU_PARSERS",
    "TYPED_PDU_SERIALIZERS",
    "MockLatticePublisher",
    "MockPublishConfig",
    "canonical_entity_from_snapshot",
    "canonical_entity_from_transform",
    "canonical_entity_from_lattice_payload",
    "canonical_entity_from_entity_state_packet",
    "PDU_CATALOG",
    "PDU_LOG_DESCRIPTORS",
    "FastDisLogEvent",
    "FastDisPduLogDescriptor",
    "MessageCoverage",
    "MESSAGE_DESCRIPTORS",
    "FieldVisit",
    "GenericPduView",
    "MessageDescriptor",
    "PduCatalogEntry",
    "PduLogAggregator",
    "SemanticPdu",
    "SemanticPduDescriptor",
    "TypedPdu",
    "TypedPduDescriptor",
    "body_decoder_available",
    "canonical_entity_to_entity_state_packet",
    "canonical_entity_to_lattice_payload",
    "count_by_type",
    "find_message_coverage",
    "find_message_descriptor",
    "find_pdu",
    "find_pdu_log_descriptor",
    "find_semantic_pdu_descriptor",
    "find_typed_pdu_descriptor",
    "known_pdu_types",
    "load_canonical_entities",
    "log_event_to_dict",
    "log_event_to_json",
    "make_pdu_log_event",
    "mock_publish_report_to_dict",
    "parse_header",
    "parse_header_tuple",
    "parse_many",
    "parse_many_semantic",
    "parse_many_typed",
    "parse_pdu",
    "parse_semantic_pdu",
    "parse_typed_pdu",
    "roundtrip_packet",
    "scan_many",
    "serialize_pdu",
    "serialize_semantic_pdu",
    "serialize_typed_pdu",
    "format_log_summary",
    "unsupported_body_decoders",
    "visit_pdu_fields",
    "walk_pdu_fields",
    "load_shared_library",
]
