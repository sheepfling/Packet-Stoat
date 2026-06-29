from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import test_shards  # noqa: E402


def test_host_facts_for_macos(monkeypatch) -> None:
    monkeypatch.setattr(test_shards.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(test_shards.shutil, "which", lambda name: "/usr/local/bin/docker" if name == "docker" else None)

    facts = test_shards.host_facts()

    assert facts.host_class == "macos"
    assert facts.docker_available is True
    assert facts.can_run_linux_docker_evidence is True
    assert facts.preferred_runtime_hosts == ("macos", "linux-docker")
    assert facts.cross_build_targets == ("macos", "linux", "windows")


def test_overall_green_expands_to_expected_shards() -> None:
    resolved = test_shards.resolve_steps("overall-green")
    shard_names = {shard_name for shard_name, _step in resolved}

    assert "python-green" in shard_names
    assert "quality-green" in shard_names
    assert "native-green" in shard_names
    assert "lattice-green" in shard_names
    assert "unreal-green" in shard_names
    assert "unity-green" in shard_names
    assert "godot-green" in shard_names
    assert "evidence-green" in shard_names


def test_lattice_green_uses_canonical_package_route() -> None:
    resolved = test_shards.resolve_steps("lattice-green")
    commands = [" ".join(step.command) for _shard_name, step in resolved]

    assert any("packages/lattice/tests/test_lattice_plugin_entrypoints.py" in cmd for cmd in commands)
    assert any("python" in cmd or "pytest" in cmd for cmd in commands)
    assert any("build packages/lattice" in cmd for cmd in commands)
    assert all("integrations/lattice" not in cmd for cmd in commands)
