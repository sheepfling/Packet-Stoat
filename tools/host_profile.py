#!/usr/bin/env python3
"""Shared host-profile helpers for staging and route-discovery workflows."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import platform as py_platform
import re
from typing import Mapping


ENV_HOST_LABEL = "FASTDIS_HOST_LABEL"
ENV_HOST_PLATFORM = "FASTDIS_HOST_PLATFORM"
ENV_HOSTNAME = "FASTDIS_HOSTNAME"
ENV_HOST_SYSTEM = "FASTDIS_HOST_SYSTEM"
ENV_HOST_RELEASE = "FASTDIS_HOST_RELEASE"
ENV_HOST_MACHINE = "FASTDIS_HOST_MACHINE"
ENV_HOST_PYTHON_VERSION = "FASTDIS_HOST_PYTHON_VERSION"
ENV_HOST_FINGERPRINT_SEED = "FASTDIS_HOST_FINGERPRINT_SEED"

_PLATFORM_ALIASES = {
    "darwin": "macos",
    "mac": "macos",
    "macos": "macos",
    "osx": "macos",
    "win": "windows",
    "windows": "windows",
    "linux": "linux",
}


@dataclass(frozen=True)
class HostProfile:
    host_label: str
    host_platform: str
    hostname: str
    platform_string: str
    system: str
    release: str
    machine: str
    python_version: str
    host_fingerprint: str
    identity_source: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-_.").lower()
    return slug or "host"


def normalize_host_platform(value: str) -> str:
    normalized = _PLATFORM_ALIASES.get(value.strip().lower(), "")
    return normalized or slugify(value)


def default_host_label(hostname: str, system: str, machine: str) -> str:
    return slugify(f"{hostname}-{system}-{machine}")


def build_platform_string(
    *,
    system: str,
    release: str,
    machine: str,
    system_overridden: bool,
    release_overridden: bool,
    machine_overridden: bool,
    platform_module=py_platform,
) -> str:
    if not any((system_overridden, release_overridden, machine_overridden)):
        detected = platform_module.platform()
        if detected:
            return detected
    parts = [part for part in (system, release, machine) if part]
    return "-".join(parts) or "unknown"


def compute_host_fingerprint(*, hostname: str, system: str, release: str, machine: str, host_platform: str, fingerprint_seed: str = "") -> str:
    digest = hashlib.sha256()
    if fingerprint_seed:
        digest.update(fingerprint_seed.encode("utf-8"))
        digest.update(b"\0")
    for value in (hostname, system, release, machine, host_platform):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _resolved_value(
    explicit: str | None,
    env: Mapping[str, str],
    env_key: str,
    fallback: str,
) -> tuple[str, bool]:
    if explicit is not None and explicit != "":
        return explicit, True
    env_value = env.get(env_key, "")
    if env_value:
        return env_value, True
    return fallback, False


def resolve_host_profile(
    *,
    host_label_override: str | None = None,
    host_platform_override: str | None = None,
    hostname_override: str | None = None,
    system_override: str | None = None,
    release_override: str | None = None,
    machine_override: str | None = None,
    python_version_override: str | None = None,
    fingerprint_seed_override: str | None = None,
    env: Mapping[str, str] | None = None,
    platform_module=py_platform,
) -> HostProfile:
    resolved_env = env if env is not None else os.environ
    hostname, hostname_overridden = _resolved_value(hostname_override, resolved_env, ENV_HOSTNAME, platform_module.node() or "host")
    system, system_overridden = _resolved_value(system_override, resolved_env, ENV_HOST_SYSTEM, platform_module.system() or "system")
    release, release_overridden = _resolved_value(release_override, resolved_env, ENV_HOST_RELEASE, platform_module.release() or "")
    machine, machine_overridden = _resolved_value(machine_override, resolved_env, ENV_HOST_MACHINE, platform_module.machine() or "machine")
    python_version, python_overridden = _resolved_value(
        python_version_override,
        resolved_env,
        ENV_HOST_PYTHON_VERSION,
        platform_module.python_version(),
    )
    derived_platform = normalize_host_platform(system)
    raw_host_platform, host_platform_overridden = _resolved_value(
        host_platform_override,
        resolved_env,
        ENV_HOST_PLATFORM,
        derived_platform,
    )
    host_platform = normalize_host_platform(raw_host_platform)
    fallback_label = default_host_label(hostname, system, machine)
    raw_host_label, host_label_overridden = _resolved_value(
        host_label_override,
        resolved_env,
        ENV_HOST_LABEL,
        fallback_label,
    )
    host_label = slugify(raw_host_label)
    fingerprint_seed, fingerprint_overridden = _resolved_value(
        fingerprint_seed_override,
        resolved_env,
        ENV_HOST_FINGERPRINT_SEED,
        "",
    )
    identity_source = "detected"
    if any(
        (
            hostname_overridden,
            system_overridden,
            release_overridden,
            machine_overridden,
            python_overridden,
            host_platform_overridden,
            host_label_overridden,
            fingerprint_overridden,
        )
    ):
        identity_source = "overridden"
    platform_string = build_platform_string(
        system=system,
        release=release,
        machine=machine,
        system_overridden=system_overridden,
        release_overridden=release_overridden,
        machine_overridden=machine_overridden,
        platform_module=platform_module,
    )
    return HostProfile(
        host_label=host_label,
        host_platform=host_platform,
        hostname=hostname,
        platform_string=platform_string,
        system=system,
        release=release,
        machine=machine,
        python_version=python_version,
        host_fingerprint=compute_host_fingerprint(
            hostname=hostname,
            system=system,
            release=release,
            machine=machine,
            host_platform=host_platform,
            fingerprint_seed=fingerprint_seed,
        ),
        identity_source=identity_source,
    )
