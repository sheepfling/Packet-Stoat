from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import capture_alpha2_host_signoff


def test_build_steps_defaults_cover_full_capture(tmp_path: Path) -> None:
    args = capture_alpha2_host_signoff.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label=None,
        skip_unreal_matrix=False,
        skip_godot_report=False,
        skip_orientation_runtime=False,
        skip_orientation_visual=False,
        skip_stage=False,
        skip_package=False,
        engine_versions=None,
        matrix_versions=None,
    )

    steps = capture_alpha2_host_signoff.build_steps(args)

    assert steps[0] == [
        sys.executable,
        "tools/run_unreal_matrix.py",
        "--out-dir",
        str((tmp_path / "reports").resolve()),
        "--versions",
        "5.7",
        "5.8",
    ]
    assert [sys.executable, "tools/run_godot_report.py", "--out-dir", str((tmp_path / "reports").resolve())] in steps
    assert steps[-1] == [sys.executable, "tools/package_alpha2.py", "--write-root-checksums"]


def test_build_steps_respects_skip_flags_and_host_label(tmp_path: Path) -> None:
    args = capture_alpha2_host_signoff.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label="other-host",
        skip_unreal_matrix=True,
        skip_godot_report=True,
        skip_orientation_runtime=True,
        skip_orientation_visual=True,
        skip_stage=False,
        skip_package=True,
        engine_versions=["5.8"],
        matrix_versions=["5.8"],
    )

    steps = capture_alpha2_host_signoff.build_steps(args)

    assert steps == [
        [sys.executable, "tools/run_alpha2_signoff_matrix.py", "--out-dir", str((tmp_path / "reports").resolve())],
        [sys.executable, "tools/run_alpha2_release_audit.py", "--out-dir", str((tmp_path / "reports").resolve())],
        [
            sys.executable,
            "tools/stage_alpha2_host_report.py",
            "--source-dir",
            str((tmp_path / "reports").resolve()),
            "--overwrite",
            "--host-label",
            "other-host",
        ],
        [sys.executable, "tools/run_alpha2_signoff_matrix.py", "--out-dir", str((tmp_path / "reports").resolve())],
        [sys.executable, "tools/run_alpha2_release_audit.py", "--out-dir", str((tmp_path / "reports").resolve())],
    ]


def test_main_returns_first_nonzero_exit(monkeypatch, tmp_path: Path) -> None:
    args = capture_alpha2_host_signoff.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label=None,
        skip_unreal_matrix=True,
        skip_godot_report=True,
        skip_orientation_runtime=True,
        skip_orientation_visual=True,
        skip_stage=True,
        skip_package=True,
        engine_versions=None,
        matrix_versions=None,
    )
    monkeypatch.setattr(capture_alpha2_host_signoff, "parse_args", lambda: args)
    monkeypatch.setattr(capture_alpha2_host_signoff.load_local_env, "load", lambda: None)
    recorded: list[list[str]] = []
    codes = iter([2, 0])

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return next(codes)

    monkeypatch.setattr(capture_alpha2_host_signoff, "run_step", fake_run_step)

    rc = capture_alpha2_host_signoff.main()

    assert rc == 2
    assert recorded[0][1] == "tools/run_alpha2_signoff_matrix.py"
