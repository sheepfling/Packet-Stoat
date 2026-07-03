from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import linux_native_build


def test_resolve_backend_prefers_direct_when_available(monkeypatch, tmp_path: Path) -> None:
    toolchain = tmp_path / "linux-zig.cmake"
    toolchain.write_text("set(CMAKE_SYSTEM_NAME Linux)\n", encoding="utf-8")
    monkeypatch.setattr(
        linux_native_build,
        "direct_backend_probe",
        lambda path: {"available": True, "detail": "ready"} if path == toolchain else {"available": False, "detail": "missing"},
    )

    assert linux_native_build.resolve_backend("auto", toolchain) == "direct"


def test_latest_linux_shared_library_prefers_versioned_real_file(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "linux-build"
    build_dir.mkdir()
    versioned = build_dir / "libfastdis.so.0.13.0"
    alias = build_dir / "libfastdis.so"
    versioned.write_bytes(b"linux-real")
    alias.write_bytes(b"linux-alias")

    original = linux_native_build.path_is_file

    def fake_path_is_file(path: Path) -> bool:
        if path == alias:
            return False
        return original(path)

    monkeypatch.setattr(linux_native_build, "path_is_file", fake_path_is_file)

    resolved = linux_native_build.latest_linux_shared_library(build_dir)

    assert resolved == versioned


def test_materialize_linux_alias_replaces_stale_alias(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "linux-build"
    build_dir.mkdir()
    versioned = build_dir / "libfastdis.so.0.13.0"
    alias_path = build_dir / "libfastdis.so"
    versioned.write_bytes(b"linux-real")
    alias_path.write_bytes(b"linux-alias")

    monkeypatch.setattr(linux_native_build, "latest_linux_shared_library", lambda path: versioned if path == build_dir else None)
    monkeypatch.setattr(linux_native_build, "path_is_file", lambda path: path == versioned)

    alias = linux_native_build.materialize_linux_alias(build_dir)

    assert alias == alias_path
    assert alias.read_bytes() == b"linux-real"
