"""Repo-local support catalog for FASTDIS protocol coverage."""

from __future__ import annotations

from .pdu_catalog import PDU_CATALOG, PduCatalogEntry, body_decoder_available, find_pdu, known_pdu_types


def supported_protocol_versions() -> list[int]:
    """Return the DIS protocol versions currently targeted by the workspace."""
    return [6, 7]


def supported_pdu_families() -> list[str]:
    """Return known PDU family names from the generated DIS 6/7 catalog."""
    return sorted({entry.family_name for entry in PDU_CATALOG})


def implemented_body_decoders() -> list[PduCatalogEntry]:
    """Return known PDU entries with body decoders implemented in fastdis."""
    return [entry for entry in PDU_CATALOG if entry.has_body_decoder]
