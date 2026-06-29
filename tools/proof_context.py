#!/usr/bin/env python3
"""Helpers for emitting the shared FastDIS proof_context envelope."""

from __future__ import annotations

import platform as py_platform
from typing import Any


def normalize_os_name(value: str | None) -> str:
    raw = (value or "").strip()
    lowered = raw.lower()
    if lowered in {"darwin", "macos", "mac", "osx"}:
        return "macos"
    if lowered in {"windows", "win32", "win64"}:
        return "windows"
    if lowered in {"linux"}:
        return "linux"
    return lowered or "unknown"


def normalize_os_family(value: str | None) -> str:
    name = normalize_os_name(value)
    if name in {"macos", "windows", "linux"}:
        return name
    return "unknown"


def normalize_arch(value: str | None) -> str:
    raw = (value or "").strip()
    lowered = raw.lower()
    if lowered in {"arm64", "aarch64"}:
        return "arm64"
    if lowered in {"x86_64", "amd64"}:
        return "x86_64"
    return lowered or "unknown"


def current_host_summary() -> dict[str, Any]:
    system = py_platform.system()
    release = py_platform.release()
    machine = py_platform.machine()
    return {
        "system": system,
        "system_family": normalize_os_family(system),
        "release": release,
        "machine": machine,
        "arch": normalize_arch(machine),
        "python": py_platform.python_version(),
    }


def build_platform_summary(
    host: dict[str, Any] | None,
    *,
    runtime_kind: str | None,
    engine_family: str | None = None,
    build_configuration: str | None = None,
    cross_compiled: bool | None = None,
) -> dict[str, Any]:
    host = host or {}
    system = host.get("system") if isinstance(host.get("system"), str) else host.get("platform")
    machine = host.get("arch") if isinstance(host.get("arch"), str) else host.get("machine")
    os_name = normalize_os_name(system if isinstance(system, str) else None)
    arch = normalize_arch(machine if isinstance(machine, str) else None)
    return {
        "os": os_name,
        "os_family": normalize_os_family(os_name),
        "arch": arch,
        "runtime_kind": runtime_kind,
        "engine_family": engine_family,
        "build_configuration": build_configuration,
        "cross_compiled": cross_compiled,
    }


def merge_host_summary(base: dict[str, Any] | None, **extras: Any) -> dict[str, Any]:
    host = dict(base or {})
    if "system" in host and "system_family" not in host:
        host["system_family"] = normalize_os_family(host.get("system"))
    if "machine" in host and "arch" not in host:
        host["arch"] = normalize_arch(host.get("machine"))
    for key, value in extras.items():
        if value is not None:
            host[key] = value
    return host


def scenario_family_for(scenario: str | None) -> str | None:
    if not scenario:
        return None
    if scenario in {"entity_state_1x10hz", "entity_state_100x30hz", "entity_state_1000x60hz"}:
        return "ingest_baseline"
    if scenario in {"filter_reject_90pct", "mixed_noise_10pct_entity_state"}:
        return "filtering"
    if scenario == "malformed_10pct":
        return "malformed_resilience"
    if scenario in {"entity_state_10000_burst", "snapshot_pressure", "late_reader_pressure"}:
        return "burst_latest_state"
    if "replay" in scenario:
        return "replay"
    if "orientation" in scenario or scenario in {
        "level_north",
        "level_east",
        "equator_prime_meridian_level_north",
        "adelaide_heading_135_pitch_20_roll_30",
    }:
        return "orientation_assurance"
    if "install" in scenario or "workflow" in scenario or "proof_verification" in scenario:
        return "workflow_install"
    return None


def build_proof_context(
    *,
    evidence_class: str,
    comparison_axis: str,
    host: dict[str, Any] | None,
    runtime_kind: str | None,
    claim_boundary: str,
    comparable: bool,
    scenario_family: str | None = None,
    engine_family: str | None = None,
    build_configuration: str | None = None,
    cross_compiled: bool | None = None,
    same_host: bool | None = None,
    same_host_class: bool | None = None,
    same_scenario: bool | None = None,
    same_metric_meaning: bool | None = None,
    truth_backed: bool | None = None,
    blocked_reason: str | None = None,
    qualification_notes: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    host_summary = merge_host_summary(host)
    return {
        "schema": "fastdis.proof_context.v1",
        "evidence_class": evidence_class,
        "comparison_axis": comparison_axis,
        "scenario_family": scenario_family,
        "host": host_summary,
        "platform": build_platform_summary(
            host_summary,
            runtime_kind=runtime_kind,
            engine_family=engine_family,
            build_configuration=build_configuration,
            cross_compiled=cross_compiled,
        ),
        "qualification": {
            "claim_boundary": claim_boundary,
            "comparable": comparable,
            "same_host": same_host,
            "same_host_class": same_host_class,
            "same_scenario": same_scenario,
            "same_metric_meaning": same_metric_meaning,
            "truth_backed": truth_backed,
            "blocked_reason": blocked_reason,
            "qualification_notes": qualification_notes or [],
        },
        "notes": notes or [],
    }
