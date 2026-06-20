from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_ctypes_wheel


def test_parse_args_requires_native_lib_and_plat_name(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_ctypes_wheel.py",
            "--native-lib",
            "fastdis.dll",
            "--plat-name",
            "win_amd64",
        ],
    )
    args = build_ctypes_wheel.parse_args()
    assert args.native_lib == "fastdis.dll"
    assert args.plat_name == "win_amd64"
    assert args.python_tag == "py3"
    assert args.abi_tag == "none"
