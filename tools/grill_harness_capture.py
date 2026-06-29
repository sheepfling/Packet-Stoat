#!/usr/bin/env python3
"""Shared validation and canonicalization for GRILL competitor harness captures."""

from __future__ import annotations

from typing import Any

from proof_context import merge_host_summary


NEW_SCHEMA = "fastdis.grill_harness_capture.v1"
LEGACY_UNITY_SCHEMA = "fastdis.unity_grill_benchmark_baseline.v1"
LEGACY_UNREAL_SCHEMA = "fastdis.unreal_grill_benchmark_baseline.v1"


def _placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("REPLACE_ME")


def detect_lane(payload: dict[str, Any]) -> str | None:
    schema = payload.get("schema")
    if schema == NEW_SCHEMA:
        lane = payload.get("lane")
        return lane if isinstance(lane, str) else None
    if schema == LEGACY_UNITY_SCHEMA:
        return "unity_vs_grill"
    if schema == LEGACY_UNREAL_SCHEMA:
        return "unreal_vs_grill"
    return None


def _validate_new_payload(payload: dict[str, Any], *, expected_lane: str | None) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != NEW_SCHEMA:
        return [f"`schema` must equal `{NEW_SCHEMA}`"]
    lane = detect_lane(payload)
    if expected_lane is not None and lane != expected_lane:
        errors.append(f"`lane` must equal `{expected_lane}`")
    if payload.get("product") not in {"GRILL DIS for Unity", "GRILL DIS for Unreal"}:
        errors.append("`product` must name a supported GRILL engine plugin")
    for field in ("captured_at_utc", "repository", "host", "runtime", "scenario", "results"):
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    repository = payload.get("repository")
    if isinstance(repository, dict):
        for field in ("url", "commit"):
            value = repository.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`repository.{field}` must be a populated non-template string")
    else:
        errors.append("`repository` must be an object")
    host = payload.get("host")
    if isinstance(host, dict):
        for field in ("system", "release", "machine"):
            value = host.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`host.{field}` must be a populated non-template string")
    else:
        errors.append("`host` must be an object")
    runtime = payload.get("runtime")
    if isinstance(runtime, dict):
        family = runtime.get("engine_family")
        version = runtime.get("version")
        if not isinstance(family, str) or family not in {"unity", "unreal"}:
            errors.append("`runtime.engine_family` must equal `unity` or `unreal`")
        if not isinstance(version, str) or not version or _placeholder(version):
            errors.append("`runtime.version` must be a populated non-template string")
        if lane == "unity_vs_grill" and family != "unity":
            errors.append("`runtime.engine_family` must equal `unity` for `unity_vs_grill`")
        if lane == "unreal_vs_grill" and family != "unreal":
            errors.append("`runtime.engine_family` must equal `unreal` for `unreal_vs_grill`")
    else:
        errors.append("`runtime` must be an object")
    scenario = payload.get("scenario")
    if isinstance(scenario, dict):
        for field in ("environment_name", "traffic_mix"):
            value = scenario.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`scenario.{field}` must be a populated non-template string")
    else:
        errors.append("`scenario` must be an object")
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        errors.append("`results` must be a non-empty array")
    else:
        for index, row in enumerate(results):
            if not isinstance(row, dict):
                errors.append(f"`results[{index}]` must be an object")
                continue
            scenario_name = row.get("scenario")
            if not isinstance(scenario_name, str) or not scenario_name or _placeholder(scenario_name):
                errors.append(f"`results[{index}].scenario` must be a populated non-template string")
    return errors


def _validate_legacy_unity_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != LEGACY_UNITY_SCHEMA:
        errors.append(f"`schema` must equal `{LEGACY_UNITY_SCHEMA}`")
    if payload.get("product") != "GRILL DIS for Unity":
        errors.append("`product` must equal `GRILL DIS for Unity`")
    for field in ("captured_at_utc", "repository", "unity", "host", "scenario", "results"):
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    repository = payload.get("repository")
    if isinstance(repository, dict):
        for field in ("url", "commit"):
            value = repository.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`repository.{field}` must be a populated non-template string")
    else:
        errors.append("`repository` must be an object")
    unity = payload.get("unity")
    if isinstance(unity, dict):
        version = unity.get("version")
        if not isinstance(version, str) or not version or _placeholder(version):
            errors.append("`unity.version` must be a populated non-template string")
    else:
        errors.append("`unity` must be an object")
    host = payload.get("host")
    if isinstance(host, dict):
        for field in ("system", "machine"):
            value = host.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`host.{field}` must be a populated non-template string")
    else:
        errors.append("`host` must be an object")
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        errors.append("`results` must be a non-empty array")
    return errors


def _validate_legacy_unreal_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != LEGACY_UNREAL_SCHEMA:
        errors.append(f"`schema` must equal `{LEGACY_UNREAL_SCHEMA}`")
    if payload.get("product") != "GRILL DIS for Unreal":
        errors.append("`product` must equal `GRILL DIS for Unreal`")
    for field in ("captured_at_utc", "repository", "engine", "host", "scenario", "results"):
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    engine = payload.get("engine")
    if isinstance(engine, dict):
        version = engine.get("version")
        if not isinstance(version, str) or not version or _placeholder(version):
            errors.append("`engine.version` must be a populated non-template string")
    else:
        errors.append("`engine` must be an object")
    host = payload.get("host")
    if isinstance(host, dict):
        for field in ("system", "machine"):
            value = host.get(field)
            if not isinstance(value, str) or not value or _placeholder(value):
                errors.append(f"`host.{field}` must be a populated non-template string")
    else:
        errors.append("`host` must be an object")
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        errors.append("`results` must be a non-empty array")
    return errors


def validate_payload(payload: dict[str, Any], *, expected_lane: str | None = None) -> list[str]:
    schema = payload.get("schema")
    if schema == NEW_SCHEMA:
        return _validate_new_payload(payload, expected_lane=expected_lane)
    if schema == LEGACY_UNITY_SCHEMA:
        if expected_lane not in {None, "unity_vs_grill"}:
            return [f"legacy Unity capture does not match expected lane `{expected_lane}`"]
        return _validate_legacy_unity_payload(payload)
    if schema == LEGACY_UNREAL_SCHEMA:
        if expected_lane not in {None, "unreal_vs_grill"}:
            return [f"legacy Unreal capture does not match expected lane `{expected_lane}`"]
        return _validate_legacy_unreal_payload(payload)
    return [f"unsupported GRILL capture schema `{schema}`"]


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def canonicalize_payload(payload: dict[str, Any], *, expected_lane: str | None = None) -> dict[str, Any]:
    errors = validate_payload(payload, expected_lane=expected_lane)
    if errors:
        raise ValueError("; ".join(errors))
    schema = payload.get("schema")
    lane = detect_lane(payload)
    if schema == NEW_SCHEMA:
        runtime = payload.get("runtime") if isinstance(payload.get("runtime"), dict) else {}
        scenario = payload.get("scenario") if isinstance(payload.get("scenario"), dict) else {}
        host = merge_host_summary(
            payload.get("host") if isinstance(payload.get("host"), dict) else {},
            system=(payload.get("host") or {}).get("system") if isinstance(payload.get("host"), dict) else None,
            release=(payload.get("host") or {}).get("release") if isinstance(payload.get("host"), dict) else None,
            machine=(payload.get("host") or {}).get("machine") if isinstance(payload.get("host"), dict) else None,
            plugin_commit=runtime.get("plugin_commit"),
            plugin_version=runtime.get("plugin_version") or (payload.get("repository") or {}).get("plugin_version"),
            unity_version=runtime.get("version") if runtime.get("engine_family") == "unity" else None,
            engine_version=runtime.get("version") if runtime.get("engine_family") == "unreal" else None,
        )
        rows = []
        for result in payload.get("results", []):
            if not isinstance(result, dict):
                continue
            rows.append(
                {
                    "scenario": str(result.get("scenario")),
                    "entity_count": _to_int(result.get("entity_count")),
                    "update_hz": _to_int(result.get("update_hz")),
                    "packets_received": _to_int(result.get("packets_received")),
                    "packets_parsed": _to_int(result.get("packets_parsed")),
                    "packets_accepted": _to_int(result.get("packets_accepted")),
                    "packets_rejected": _to_int(result.get("packets_rejected")),
                    "malformed": _to_int(result.get("malformed")),
                    "socket_drops": _to_int(result.get("socket_drops")),
                    "queue_drops": _to_int(result.get("queue_drops")),
                    "p50_ingest_ms": _to_float(result.get("p50_ingest_ms")),
                    "p95_ingest_ms": _to_float(result.get("p95_ingest_ms")),
                    "p99_ingest_ms": _to_float(result.get("p99_ingest_ms")),
                    "steady_state_gc_bytes": _to_int(result.get("steady_state_gc_bytes")),
                    "main_thread_apply_ms": _to_float(result.get("main_thread_apply_ms")),
                    "packets_per_sec": _to_float(result.get("packets_per_sec")),
                    "notes": result.get("notes") if isinstance(result.get("notes"), str) else None,
                }
            )
        return {
            "schema": NEW_SCHEMA,
            "lane": lane,
            "product": payload.get("product"),
            "captured_at_utc": payload.get("captured_at_utc"),
            "repository": payload.get("repository"),
            "host": host,
            "runtime": runtime,
            "scenario": scenario,
            "results": rows,
        }
    if schema == LEGACY_UNITY_SCHEMA:
        unity = payload.get("unity") if isinstance(payload.get("unity"), dict) else {}
        scenario = payload.get("scenario") if isinstance(payload.get("scenario"), dict) else {}
        host = merge_host_summary(
            payload.get("host") if isinstance(payload.get("host"), dict) else {},
            system=(payload.get("host") or {}).get("system") if isinstance(payload.get("host"), dict) else None,
            release=(payload.get("host") or {}).get("release") if isinstance(payload.get("host"), dict) else None,
            machine=(payload.get("host") or {}).get("machine") if isinstance(payload.get("host"), dict) else None,
            unity_version=unity.get("version"),
            plugin_commit=(payload.get("repository") or {}).get("commit") if isinstance(payload.get("repository"), dict) else None,
        )
        rows = []
        for result in payload.get("results", []):
            if not isinstance(result, dict):
                continue
            scenario_name = result.get("case")
            rows.append(
                {
                    "scenario": str(scenario_name or "unknown"),
                    "entity_count": _to_int(result.get("entity_count")),
                    "update_hz": _to_int(result.get("update_hz")),
                    "packets_received": None,
                    "packets_parsed": None,
                    "packets_accepted": None,
                    "packets_rejected": None,
                    "malformed": None,
                    "socket_drops": None,
                    "queue_drops": None,
                    "p50_ingest_ms": None,
                    "p95_ingest_ms": None,
                    "p99_ingest_ms": None,
                    "steady_state_gc_bytes": _to_int(result.get("gc_alloc_bytes_per_frame")),
                    "main_thread_apply_ms": _to_float(result.get("main_thread_ms_avg")),
                    "packets_per_sec": _to_float(result.get("packets_per_sec")),
                    "notes": result.get("notes") if isinstance(result.get("notes"), str) else None,
                }
            )
        return {
            "schema": NEW_SCHEMA,
            "lane": "unity_vs_grill",
            "product": payload.get("product"),
            "captured_at_utc": payload.get("captured_at_utc"),
            "repository": payload.get("repository"),
            "host": host,
            "runtime": {
                "engine_family": "unity",
                "version": unity.get("version"),
                "render_pipeline": unity.get("render_pipeline"),
                "scripting_backend": unity.get("scripting_backend"),
                "plugin_commit": (payload.get("repository") or {}).get("commit") if isinstance(payload.get("repository"), dict) else None,
                "plugin_version": None,
            },
            "scenario": {
                "environment_name": scenario.get("scene"),
                "traffic_mix": scenario.get("traffic_mix"),
                "entity_counts": scenario.get("entity_counts") if isinstance(scenario.get("entity_counts"), list) else [],
                "update_hz": scenario.get("update_hz") if isinstance(scenario.get("update_hz"), list) else [],
                "notes": scenario.get("notes"),
            },
            "results": rows,
        }
    engine = payload.get("engine") if isinstance(payload.get("engine"), dict) else {}
    scenario = payload.get("scenario") if isinstance(payload.get("scenario"), dict) else {}
    host = merge_host_summary(
        payload.get("host") if isinstance(payload.get("host"), dict) else {},
        system=(payload.get("host") or {}).get("system") if isinstance(payload.get("host"), dict) else None,
        release=(payload.get("host") or {}).get("release") if isinstance(payload.get("host"), dict) else None,
        machine=(payload.get("host") or {}).get("machine") if isinstance(payload.get("host"), dict) else None,
        engine_version=engine.get("version"),
        plugin_commit=(payload.get("repository") or {}).get("commit") if isinstance(payload.get("repository"), dict) else None,
    )
    rows = []
    for result in payload.get("results", []):
        if not isinstance(result, dict):
            continue
        rows.append(
            {
                "scenario": str(result.get("scenario") or "unknown"),
                "entity_count": None,
                "update_hz": None,
                "packets_received": _to_int(result.get("packets_received")),
                "packets_parsed": _to_int(result.get("packets_parsed")),
                "packets_accepted": _to_int(result.get("packets_accepted")),
                "packets_rejected": _to_int(result.get("packets_rejected")),
                "malformed": _to_int(result.get("malformed")),
                "socket_drops": _to_int(result.get("socket_drops")),
                "queue_drops": _to_int(result.get("queue_drops")),
                "p50_ingest_ms": _to_float(result.get("p50_ingest_ms")),
                "p95_ingest_ms": _to_float(result.get("p95_ingest_ms")),
                "p99_ingest_ms": _to_float(result.get("p99_ingest_ms")),
                "steady_state_gc_bytes": _to_int(result.get("steady_state_gc_bytes")),
                "main_thread_apply_ms": _to_float(result.get("main_thread_apply_ms")),
                "packets_per_sec": _to_float(result.get("packets_per_sec")),
                "notes": result.get("notes") if isinstance(result.get("notes"), str) else None,
            }
        )
    return {
        "schema": NEW_SCHEMA,
        "lane": "unreal_vs_grill",
        "product": payload.get("product"),
        "captured_at_utc": payload.get("captured_at_utc"),
        "repository": payload.get("repository"),
        "host": host,
        "runtime": {
            "engine_family": "unreal",
            "version": engine.get("version"),
            "render_pipeline": None,
            "scripting_backend": None,
            "plugin_commit": (payload.get("repository") or {}).get("commit") if isinstance(payload.get("repository"), dict) else None,
            "plugin_version": None,
        },
        "scenario": {
            "environment_name": scenario.get("map"),
            "traffic_mix": scenario.get("traffic_mix"),
            "entity_counts": [],
            "update_hz": [],
            "notes": scenario.get("notes"),
        },
        "results": rows,
    }
