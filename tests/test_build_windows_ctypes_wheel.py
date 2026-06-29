from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_windows_ctypes_wheel


def test_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_windows_ctypes_wheel.py"])
    args = build_windows_ctypes_wheel.parse_args()
    assert Path(args.build_dir).as_posix().endswith("build/cmake/mingw-win64")
    assert Path(args.outdir).as_posix().endswith("build/dist")
    assert args.plat_name == "win_amd64"
    assert args.python_tag == "py3"
    assert args.abi_tag == "none"
    assert args.target == "fastdis_shared"
    assert not args.build_examples
    assert not args.build_benchmarks
