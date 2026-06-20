from __future__ import annotations

import importlib
import os

import pytest


def _live_enabled() -> bool:
    return os.environ.get("LATTICE_LIVE_TESTS") == "1"


def _require_live_env() -> tuple[str, str, str | None]:
    endpoint = os.environ.get("LATTICE_ENDPOINT") or os.environ.get("LATTICE_BASE_URL")
    token = os.environ.get("LATTICE_TOKEN") or os.environ.get("LATTICE_BEARER_TOKEN")
    sandbox_token = os.environ.get("LATTICE_SANDBOX_TOKEN")
    missing = []
    if not endpoint:
        missing.append("LATTICE_ENDPOINT or LATTICE_BASE_URL")
    if not token:
        missing.append("LATTICE_TOKEN or LATTICE_BEARER_TOKEN")
    if missing:
        pytest.skip("live Lattice smoke tests require " + ", ".join(missing))
    return str(endpoint), str(token), sandbox_token


@pytest.mark.skipif(not _live_enabled(), reason="set LATTICE_LIVE_TESTS=1 to enable live Lattice smoke tests")
def test_live_lattice_rest_sdk_imports_and_client_constructs_from_env() -> None:
    try:
        module = importlib.import_module("anduril")
    except ModuleNotFoundError:
        pytest.skip("install anduril-lattice-sdk to run live Lattice smoke tests")

    endpoint, token, sandbox_token = _require_live_env()
    headers = {}
    if sandbox_token:
        headers["Anduril-Sandbox-Authorization"] = f"Bearer {sandbox_token}"

    client = module.Lattice(base_url=endpoint, token=lambda: token, headers=headers)

    assert client is not None
    assert hasattr(client, "entities")


@pytest.mark.skipif(not _live_enabled(), reason="set LATTICE_LIVE_TESTS=1 to enable live Lattice smoke tests")
def test_live_lattice_mutating_tests_require_separate_opt_in() -> None:
    if os.environ.get("LATTICE_LIVE_MUTATION_TESTS") != "1":
        pytest.skip("set LATTICE_LIVE_MUTATION_TESTS=1 only against a disposable sandbox")

    _require_live_env()
    pytest.skip("live mutation test scaffold is armed but no destructive endpoint calls are defined yet")
