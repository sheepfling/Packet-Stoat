from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import lattice_live_bridge


def test_load_live_route_config_prefers_env_token() -> None:
    config = lattice_live_bridge.load_live_route_config(
        {
            "LATTICE_ENDPOINT": "example.env.sandboxes.developer.anduril.com",
            "ENVIRONMENT_TOKEN": "env-token",
            "SANDBOXES_TOKEN": "sandbox-token",
            "SKIP_TLS_VERIFY": "true",
        }
    )

    assert config.base_url == "https://example.env.sandboxes.developer.anduril.com"
    assert config.skip_tls_verify is True
    assert config.auth_mode == "environment-token"
    assert config.is_ready is True


def test_doctor_reports_missing_prereqs_without_auth(capsys) -> None:
    rc = lattice_live_bridge.main(["doctor"])

    out = capsys.readouterr().out
    assert rc == 2
    assert '"status": "missing-prereqs"' in out


def test_doctor_reports_ready_with_environment_token(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LATTICE_ENDPOINT", "example.env.sandboxes.developer.anduril.com")
    monkeypatch.setenv("ENVIRONMENT_TOKEN", "env-token")
    monkeypatch.setenv("SANDBOXES_TOKEN", "sandbox-token")

    rc = lattice_live_bridge.main(["doctor"])

    out = capsys.readouterr().out
    assert rc == 0
    assert '"status": "ready"' in out
    assert '"auth_mode": "environment-token"' in out
