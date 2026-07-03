from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import host_profile
import test_shards


def test_resolve_host_profile_uses_explicit_overrides() -> None:
    profile = host_profile.resolve_host_profile(
        host_label_override="Win Lab A",
        host_platform_override="windows",
        hostname_override="win-lab-a",
        system_override="Windows",
        release_override="11",
        machine_override="x86_64",
        python_version_override="3.12.9",
        fingerprint_seed_override="seed-a",
        env={},
    )

    assert profile.host_slug == "win-lab-a"
    assert profile.host_label == "win-lab-a"
    assert profile.host_platform == "windows"
    assert profile.hostname == "win-lab-a"
    assert profile.system == "Windows"
    assert profile.release == "11"
    assert profile.machine == "x86_64"
    assert profile.python_version == "3.12.9"
    assert profile.identity_source == "overridden"
    assert len(profile.host_fingerprint) == 64


def test_resolve_host_profile_reads_env_overrides() -> None:
    profile = host_profile.resolve_host_profile(
        env={
            host_profile.ENV_HOST_LABEL: "Linux Box",
            host_profile.ENV_HOST_PLATFORM: "linux",
            host_profile.ENV_HOSTNAME: "linux-box",
            host_profile.ENV_HOST_SYSTEM: "Linux",
            host_profile.ENV_HOST_MACHINE: "x86_64",
            host_profile.ENV_HOST_FINGERPRINT_SEED: "seed-b",
        }
    )

    assert profile.host_slug == "linux-box"
    assert profile.host_label == "linux-box"
    assert profile.host_platform == "linux"
    assert profile.hostname == "linux-box"
    assert profile.system == "Linux"
    assert profile.machine == "x86_64"
    assert profile.identity_source == "overridden"


def test_host_facts_accepts_override_env() -> None:
    facts = test_shards.host_facts(
        env={
            host_profile.ENV_HOST_PLATFORM: "windows",
            host_profile.ENV_HOST_SYSTEM: "Windows",
        }
    )

    assert facts.host_class == "windows"
    assert "windows" in facts.cross_build_targets


def test_normalize_manifest_identity_backfills_slug_and_platform() -> None:
    manifest = host_profile.normalize_manifest_identity(
        {
            "host_label": "Win Lab A",
            "platform": "Windows-11-x86_64",
        },
        default_host_label="fallback-host",
    )

    assert manifest["host_label"] == "win-lab-a"
    assert manifest["host_slug"] == "win-lab-a"
    assert manifest["host_platform"] == "windows"
