"""fastdis: callback-first DIS packet scanning.

The package is designed for high-rate packet pipelines where you usually do not
want to instantiate a deep Python object tree for every DIS PDU. The fast path
parses the fixed 12-byte header, filters/downsamples early, and calls Python
only for packets you keep.
"""

from __future__ import annotations

from typing import NamedTuple

FASTDIS_PROTOCOL_VERSION_DIS6 = 6
FASTDIS_PROTOCOL_VERSION_DIS7 = 7
FASTDIS_HEADER_STATUS_UNAVAILABLE = -1


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
    from . import _cfast as _impl

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
    "HAS_C_ACCELERATOR",
    "Header",
    "count_by_type",
    "parse_header",
    "parse_header_tuple",
    "scan_many",
    "load_shared_library",
]
