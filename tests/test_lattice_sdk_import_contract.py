from __future__ import annotations

import importlib

import pytest


def test_public_lattice_sdk_import_contract_if_installed() -> None:
    try:
        module = importlib.import_module("anduril")
    except ModuleNotFoundError:
        pytest.skip("public anduril-lattice-sdk package is not installed")

    assert hasattr(module, "Lattice")
