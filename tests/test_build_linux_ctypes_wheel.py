from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_linux_ctypes_wheel


def test_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_linux_ctypes_wheel.py"])
    args = build_linux_ctypes_wheel.parse_args()
    assert Path(args.build_dir).as_posix().endswith("build/cmake/linux-x86_64")
    assert args.backend == "auto"
    assert Path(args.toolchain_file).as_posix().endswith("cmake/toolchains/linux-x86_64-zig.cmake")
    assert args.image == "ubuntu:24.04"
    assert Path(args.outdir).as_posix().endswith("artifacts/dist")
    assert args.plat_name == "linux_x86_64"
    assert args.python_tag == "py3"
    assert args.abi_tag == "none"
    assert args.target == "fastdis_shared"
