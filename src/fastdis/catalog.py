"""Repo-local support catalog for the initial FASTDIS scaffold."""

from __future__ import annotations


def supported_protocol_versions() -> list[int]:
    """Return the DIS protocol versions currently targeted by the workspace."""
    return [6, 7]


def supported_pdu_families() -> list[str]:
    """Return the first PDU families expected to anchor parser development."""
    return [
        "Entity Information/State",
        "Warfare",
        "Simulation Management",
        "Logistics",
    ]
