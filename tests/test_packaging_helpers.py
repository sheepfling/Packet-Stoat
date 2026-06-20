from __future__ import annotations

from pathlib import Path

import pytest

import packaging_helpers


def test_validate_wheel_env_requires_plat_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dll = tmp_path / "fastdis.dll"
    dll.write_bytes(b"dll")
    monkeypatch.setenv("FASTDIS_WHEEL_NATIVE_LIB", str(dll))
    monkeypatch.delenv("FASTDIS_WHEEL_PLAT_NAME", raising=False)
    with pytest.raises(ValueError):
        packaging_helpers.validate_wheel_env()


def test_validate_wheel_env_requires_existing_native_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_WHEEL_NATIVE_LIB", str(tmp_path / "missing.dll"))
    monkeypatch.setenv("FASTDIS_WHEEL_PLAT_NAME", "win_amd64")
    with pytest.raises(FileNotFoundError):
        packaging_helpers.validate_wheel_env()


def test_validate_wheel_env_accepts_bundled_dll(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dll = tmp_path / "fastdis.dll"
    dll.write_bytes(b"dll")
    monkeypatch.setenv("FASTDIS_WHEEL_NATIVE_LIB", str(dll))
    monkeypatch.setenv("FASTDIS_WHEEL_PLAT_NAME", "win_amd64")
    packaging_helpers.validate_wheel_env()
    assert packaging_helpers.has_bundled_native_wheel()
    assert packaging_helpers.wheel_native_lib_from_env() == dll.resolve()
    assert packaging_helpers.wheel_plat_name_from_env() == "win_amd64"
