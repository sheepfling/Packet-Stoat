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


def test_evidence_pack_step_skips_when_existing_manifest_verifies(monkeypatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    def fake_check(path):
        assert path == manifest_path
        return True, []

    monkeypatch.setattr(test_shards, "DEFAULT_EVIDENCE_MANIFEST", manifest_path)
    monkeypatch.setattr(test_shards.check_evidence_pack, "check", fake_check)

    evidence_step = next(step for shard_name, step in test_shards.resolve_steps("evidence-green") if shard_name == "evidence-green" and step.label == "evidence pack")
    reusable, reason = evidence_step.reuse_probe()

    assert reusable is True
    assert "verified existing manifest" in reason


def test_command_run_reuses_existing_evidence_pack(monkeypatch, tmp_path: Path) -> None:
    executed: list[tuple[str, str, bool]] = []

    def fake_run_step(shard_name, step, *, allow_reuse):
        executed.append((shard_name, step.label, allow_reuse))
        if step.label == "evidence pack":
            return {
                "shard": shard_name,
                "label": step.label,
                "command": list(step.command),
                "required": step.required,
                "returncode": 0,
                "status": "skip",
                "elapsed_seconds": 0.0,
                "skip_reason": "verified existing manifest",
            }
        return {
            "shard": shard_name,
            "label": step.label,
            "command": list(step.command),
            "required": step.required,
            "returncode": 0,
            "status": "pass",
            "elapsed_seconds": 0.0,
        }

    monkeypatch.setattr(test_shards, "run_step", fake_run_step)
    monkeypatch.setattr(test_shards, "write_report", lambda *_args, **_kwargs: None)

    rc = test_shards.command_run(["evidence-green"], str(tmp_path / "report.json"), fresh=False)

    assert rc == 0
    assert ("evidence-green", "evidence pack", True) in executed


def test_command_run_fresh_disables_reuse(monkeypatch, tmp_path: Path) -> None:
    executed: list[tuple[str, str, bool]] = []

    def fake_run_step(shard_name, step, *, allow_reuse):
        executed.append((shard_name, step.label, allow_reuse))
        return {
            "shard": shard_name,
            "label": step.label,
            "command": list(step.command),
            "required": step.required,
            "returncode": 0,
            "status": "pass",
            "elapsed_seconds": 0.0,
        }

    monkeypatch.setattr(test_shards, "run_step", fake_run_step)
    monkeypatch.setattr(test_shards, "write_report", lambda *_args, **_kwargs: None)

    rc = test_shards.command_run(["evidence-green"], str(tmp_path / "report.json"), fresh=True)

    assert rc == 0
    assert ("evidence-green", "evidence pack", False) in executed
