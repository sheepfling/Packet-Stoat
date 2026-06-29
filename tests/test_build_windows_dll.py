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
    )


def test_resolve_rc_tool_accepts_plain_windres(monkeypatch) -> None:
    def fake_which(name: str) -> str | None:
        if name == "windres":
            return r"C:\mingw\bin\windres.exe"
        return None

    monkeypatch.setattr(build_windows_dll.shutil, "which", fake_which)

    assert build_windows_dll.resolve_rc_tool("x86_64-w64-mingw32") == r"C:\mingw\bin\windres.exe"


def test_stage_mingw_runtime_dlls_copies_sidecars(monkeypatch, tmp_path: Path) -> None:
    source_dir = tmp_path / "mingw" / "bin"
    source_dir.mkdir(parents=True)
    for name in ("libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll"):
        (source_dir / name).write_bytes(name.encode("ascii"))
    target_dir = tmp_path / "build"
    target_dir.mkdir()
    dll = target_dir / "libfastdis.dll"
    dll.write_bytes(b"fastdis")

    monkeypatch.setattr(
        build_windows_dll.shutil,
        "which",
        lambda name: str(source_dir / "x86_64-w64-mingw32-g++.exe") if name == "x86_64-w64-mingw32-g++" else None,
    )

    staged = build_windows_dll.stage_mingw_runtime_dlls(dll, "x86_64-w64-mingw32")

    assert [path.name for path in staged] == ["libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll"]
    assert all((target_dir / path.name).is_file() for path in staged)


def test_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_windows_dll.py"])
    args = build_windows_dll.parse_args()
    assert Path(args.build_dir).parts[-3:] == ("build", "cmake", "mingw-win64")
    assert args.mingw_prefix == "x86_64-w64-mingw32"
    assert args.config == "Release"
    assert args.generator is None
    assert args.target == "fastdis_shared"
    assert not args.build_examples
    assert not args.build_benchmarks
