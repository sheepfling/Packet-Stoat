from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_windows_dll


def test_expected_tool_names() -> None:
    assert build_windows_dll.expected_tool_names("x86_64-w64-mingw32") == (
        "x86_64-w64-mingw32-gcc",
        "x86_64-w64-mingw32-g++",
        "x86_64-w64-mingw32-windres",
    )


def test_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_windows_dll.py"])
    args = build_windows_dll.parse_args()
    assert args.build_dir.endswith("build/cmake/mingw-win64")
    assert args.mingw_prefix == "x86_64-w64-mingw32"
    assert args.config == "Release"
    assert args.target == "fastdis_shared"
    assert not args.build_examples
    assert not args.build_benchmarks
