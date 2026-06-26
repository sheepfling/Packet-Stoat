from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import capture_unity_host_report


def test_build_steps_defaults_cover_full_capture(tmp_path: Path) -> None:
    args = capture_unity_host_report.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label="windows-demo",
        host_platform="windows",
        dest_root=str(tmp_path / "hosts"),
        archive_out_dir=str(tmp_path / "archives"),
        unity_version="6000.5",
        skip_native_build=False,
        skip_startup_probe=False,
        skip_full=False,
        skip_stage=False,
        skip_export=False,
        skip_install_matrix=False,
    )

    steps = capture_unity_host_report.build_steps(args)

    assert steps[0] == [sys.executable, "tools/unity_workflow.py", "full", "--unity-version", "6000.5"]
    assert [
        sys.executable,
        "tools/unity_workflow.py",
        "stage-host-report",
        "--source-dir",
        str((tmp_path / "reports").resolve()),
        "--overwrite",
        "--host-label",
        "windows-demo",
        "--host-platform",
        "windows",
        "--dest-root",
        str((tmp_path / "hosts").resolve()),
    ] in steps
    assert [sys.executable, "tools/unity_workflow.py", "install-matrix", "--report-dir", str((tmp_path / "reports").resolve()), "--out-dir", str((tmp_path / "reports").resolve())] in steps
    assert [sys.executable, "tools/unity_workflow.py", "host-matrix", "--host-root", str((tmp_path / "hosts").resolve()), "--out-dir", str((tmp_path / "reports").resolve())] in steps
    assert [sys.executable, "tools/unity_workflow.py", "signoff", "--report-dir", str((tmp_path / "reports").resolve()), "--host-root", str((tmp_path / "hosts").resolve()), "--out-dir", str((tmp_path / "reports").resolve())] in steps
    assert steps[-1] == [
        sys.executable,
        "tools/unity_workflow.py",
        "export-host-report",
        "windows-demo",
        "--host-root",
        str((tmp_path / "hosts").resolve()),
        "--out-dir",
        str((tmp_path / "archives").resolve()),
    ]


def test_build_steps_respects_skip_flags(tmp_path: Path) -> None:
    args = capture_unity_host_report.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label="linux-demo",
        host_platform="linux",
        dest_root=None,
        archive_out_dir=None,
        unity_version=None,
        skip_native_build=False,
        skip_startup_probe=False,
        skip_full=True,
        skip_stage=False,
        skip_export=True,
        skip_install_matrix=True,
    )

    steps = capture_unity_host_report.build_steps(args)

    assert steps == [
        [
            sys.executable,
            "tools/unity_workflow.py",
            "stage-host-report",
            "--source-dir",
            str((tmp_path / "reports").resolve()),
            "--overwrite",
            "--host-label",
            "linux-demo",
            "--host-platform",
            "linux",
        ]
    ]


def test_build_steps_auto_detects_host_label_for_export(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(capture_unity_host_report.stage_unity_host_report, "detect_host_label", lambda: "auto-host")
    args = capture_unity_host_report.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label=None,
        host_platform=None,
        dest_root=None,
        archive_out_dir=None,
        unity_version=None,
        skip_native_build=False,
        skip_startup_probe=False,
        skip_full=True,
        skip_stage=False,
        skip_export=False,
        skip_install_matrix=True,
    )

    steps = capture_unity_host_report.build_steps(args)

    assert steps == [
        [
            sys.executable,
            "tools/unity_workflow.py",
            "stage-host-report",
            "--source-dir",
            str((tmp_path / "reports").resolve()),
            "--overwrite",
            "--host-label",
            "auto-host",
        ],
        [sys.executable, "tools/unity_workflow.py", "export-host-report", "auto-host"],
    ]


def test_main_returns_first_nonzero_exit(monkeypatch, tmp_path: Path) -> None:
    args = capture_unity_host_report.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label="host",
        host_platform="windows",
        dest_root=None,
        archive_out_dir=None,
        unity_version=None,
        skip_native_build=False,
        skip_startup_probe=False,
        skip_full=True,
        skip_stage=False,
        skip_export=True,
        skip_install_matrix=True,
    )
    monkeypatch.setattr(capture_unity_host_report, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(capture_unity_host_report.load_local_env, "load", lambda: None)
    recorded: list[list[str]] = []
    codes = iter([2])

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return next(codes)

    monkeypatch.setattr(capture_unity_host_report, "run_step", fake_run_step)

    rc = capture_unity_host_report.main()

    assert rc == 2
    assert recorded[0][1] == "tools/unity_workflow.py"
    assert recorded[0][2] == "stage-host-report"


def test_build_steps_can_forward_skip_native_build_to_full(tmp_path: Path) -> None:
    args = capture_unity_host_report.argparse.Namespace(
        source_dir=str(tmp_path / "reports"),
        host_label="linux-demo",
        host_platform="linux",
        dest_root=None,
        archive_out_dir=None,
        unity_version="6000.5",
        skip_native_build=True,
        skip_startup_probe=True,
        skip_full=False,
        skip_stage=True,
        skip_export=True,
        skip_install_matrix=True,
    )

    steps = capture_unity_host_report.build_steps(args)

    assert steps == [[sys.executable, "tools/unity_workflow.py", "full", "--unity-version", "6000.5", "--skip-native-build", "--skip-startup-probe"]]
