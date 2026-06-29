from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
THIRDPARTY_ROOT = ROOT / "packages" / "unreal" / "FastDis" / "ThirdParty" / "fastdis"


def test_unreal_thirdparty_headers_are_staged_from_current_public_set() -> None:
    include_dir = THIRDPARTY_ROOT / "include" / "fastdis"
    public_headers = sorted(path.name for path in (ROOT / "include" / "fastdis").iterdir() if path.is_file())
    staged_headers = sorted(path.name for path in include_dir.iterdir() if path.is_file())
    assert staged_headers == public_headers


def test_unreal_thirdparty_macos_payload_has_no_duplicate_or_stale_dylibs() -> None:
    if sys.platform.startswith("win"):
        pytest.skip("macOS dylib payload assertions are not meaningful on Windows")
    mac_lib_dir = THIRDPARTY_ROOT / "lib" / "Mac"
    names = sorted(path.name for path in mac_lib_dir.iterdir() if path.is_file())
    assert names == [
        "libfastdis.0.13.0.dylib",
        "libfastdis.0.dylib",
        "libfastdis.dylib",
    ]
