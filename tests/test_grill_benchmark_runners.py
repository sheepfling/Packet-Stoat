from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_grill_benchmark
import run_unity_grill_benchmark


def test_unreal_runner_prefers_current_report_and_builds_command(tmp_path: Path) -> None:
    current = tmp_path / "grill_unreal_engine_benchmark_report.json"
    sample = tmp_path / "grill_unreal.sample.json"
    current.write_text("{}\n", encoding="utf-8")
    sample.write_text("{}\n", encoding="utf-8")
    args = run_unreal_grill_benchmark.argparse.Namespace(
        fastdis=tmp_path / "fastdis_unreal.json",
        grill_reports=[sample, current],
        allow_sample_grill=False,
        json_out=tmp_path / "unreal_vs_grill.json",
        md_out=tmp_path / "unreal_vs_grill.md",
    )

    grill = run_unreal_grill_benchmark.select_grill_report(args.grill_reports, allow_sample=False)
    cmd = run_unreal_grill_benchmark.build_command(args, grill_report=grill)

    assert grill == current
    assert cmd == [
        sys.executable,
        "tools/run_engine_head_to_head_matrix.py",
        "--left",
        str(args.fastdis),
        "--right",
        str(current),
        "--left-label",
        "FastDIS Unreal",
        "--right-label",
        "GRILL Unreal",
        "--json-out",
        str(args.json_out),
        "--md-out",
        str(args.md_out),
    ]


def test_unreal_runner_can_fall_back_to_sample_when_allowed(tmp_path: Path) -> None:
    sample = tmp_path / "grill_unreal.sample.json"
    sample.write_text("{}\n", encoding="utf-8")

    grill = run_unreal_grill_benchmark.select_grill_report([sample], allow_sample=True)

    assert grill == sample


def test_unreal_runner_main_returns_one_when_no_report(monkeypatch, tmp_path: Path) -> None:
    fastdis = tmp_path / "fastdis_unreal.json"
    fastdis.write_text('{"surface":"unreal","host":{"system":"Darwin"}}\n', encoding="utf-8")
    args = run_unreal_grill_benchmark.argparse.Namespace(
        fastdis=fastdis,
        grill_reports=[tmp_path / "missing.json"],
        allow_sample_grill=False,
        if_available=False,
        json_out=tmp_path / "out.json",
        md_out=tmp_path / "out.md",
    )
    monkeypatch.setattr(run_unreal_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unreal_grill_benchmark.load_local_env, "load", lambda: None)

    rc = run_unreal_grill_benchmark.main()

    assert rc == 1
    payload = json.loads(args.json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked_on_competitor"
    assert payload["inputs"]["right"] == str(tmp_path / "missing.json")


def test_unreal_runner_main_if_available_returns_zero_when_no_report(monkeypatch, tmp_path: Path) -> None:
    fastdis = tmp_path / "fastdis_unreal.json"
    fastdis.write_text('{"surface":"unreal","host":{"system":"Darwin"}}\n', encoding="utf-8")
    args = run_unreal_grill_benchmark.argparse.Namespace(
        fastdis=fastdis,
        grill_reports=[tmp_path / "missing.json"],
        allow_sample_grill=False,
        if_available=True,
        json_out=tmp_path / "out.json",
        md_out=tmp_path / "out.md",
    )
    monkeypatch.setattr(run_unreal_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unreal_grill_benchmark.load_local_env, "load", lambda: None)

    rc = run_unreal_grill_benchmark.main()

    assert rc == 0
    payload = json.loads(args.json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked_on_competitor"


def test_unreal_runner_main_normalizes_raw_baseline_when_shared_report_missing(monkeypatch, tmp_path: Path) -> None:
    raw = tmp_path / "grill_unreal_benchmark_baseline.json"
    shared = tmp_path / "grill_unreal_engine_benchmark_report.json"
    raw.write_text("{}\n", encoding="utf-8")
    args = run_unreal_grill_benchmark.argparse.Namespace(
        fastdis=tmp_path / "fastdis_unreal.json",
        grill_reports=[shared],
        allow_sample_grill=False,
        if_available=False,
        json_out=tmp_path / "out.json",
        md_out=tmp_path / "out.md",
    )
    monkeypatch.setattr(run_unreal_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unreal_grill_benchmark.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unreal_grill_benchmark, "DEFAULT_RAW_BASELINE", raw)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        if cmd[1] == "tools/normalize_unreal_grill_baseline.py":
            shared.write_text("{}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(run_unreal_grill_benchmark, "run_step", fake_run_step)

    rc = run_unreal_grill_benchmark.main()

    assert rc == 0
    assert recorded[0][1] == "tools/normalize_unreal_grill_baseline.py"
    assert recorded[1][1] == "tools/run_engine_head_to_head_matrix.py"


def test_unity_runner_builds_command_from_first_existing_candidate(tmp_path: Path) -> None:
    current = tmp_path / "grill_unity_engine_benchmark_report.json"
    current.write_text("{}\n", encoding="utf-8")
    args = run_unity_grill_benchmark.argparse.Namespace(
        fastdis=tmp_path / "fastdis_unity.json",
        grill_reports=[tmp_path / "missing.json", current],
        if_available=False,
        json_out=tmp_path / "unity_vs_grill.json",
        md_out=tmp_path / "unity_vs_grill.md",
    )

    grill = run_unity_grill_benchmark.select_grill_report(args.grill_reports)
    cmd = run_unity_grill_benchmark.build_command(args, grill_report=grill)

    assert grill == current
    assert cmd == [
        sys.executable,
        "tools/run_engine_head_to_head_matrix.py",
        "--left",
        str(args.fastdis),
        "--right",
        str(current),
        "--left-label",
        "FastDIS Unity",
        "--right-label",
        "GRILL Unity",
        "--json-out",
        str(args.json_out),
        "--md-out",
        str(args.md_out),
    ]


def test_unity_runner_main_returns_first_nonzero_exit(monkeypatch, tmp_path: Path) -> None:
    current = tmp_path / "grill_unity_engine_benchmark_report.json"
    current.write_text("{}\n", encoding="utf-8")
    args = run_unity_grill_benchmark.argparse.Namespace(
        fastdis=tmp_path / "fastdis_unity.json",
        grill_reports=[current],
        if_available=False,
        json_out=tmp_path / "unity_vs_grill.json",
        md_out=tmp_path / "unity_vs_grill.md",
    )
    monkeypatch.setattr(run_unity_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unity_grill_benchmark.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unity_grill_benchmark, "run_step", lambda cmd: 2)

    rc = run_unity_grill_benchmark.main()

    assert rc == 2


def test_unity_runner_main_if_available_returns_zero_when_no_report(monkeypatch, tmp_path: Path) -> None:
    fastdis = tmp_path / "fastdis_unity.json"
    fastdis.write_text('{"surface":"unity","host":{"system":"Darwin"}}\n', encoding="utf-8")
    args = run_unity_grill_benchmark.argparse.Namespace(
        fastdis=fastdis,
        grill_reports=[tmp_path / "missing.json"],
        if_available=True,
        json_out=tmp_path / "unity_vs_grill.json",
        md_out=tmp_path / "unity_vs_grill.md",
    )
    monkeypatch.setattr(run_unity_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unity_grill_benchmark.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unity_grill_benchmark, "DEFAULT_IMPORT_SMOKE", tmp_path / "missing_import_smoke.json")

    rc = run_unity_grill_benchmark.main()

    assert rc == 0
    payload = json.loads(args.json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked_on_competitor"


def test_unity_runner_main_normalizes_raw_baseline_when_shared_report_missing(monkeypatch, tmp_path: Path) -> None:
    raw = tmp_path / "grill_unity_benchmark_baseline.json"
    shared = tmp_path / "grill_unity_engine_benchmark_report.json"
    raw.write_text("{}\n", encoding="utf-8")
    args = run_unity_grill_benchmark.argparse.Namespace(
        fastdis=tmp_path / "fastdis_unity.json",
        grill_reports=[shared],
        if_available=False,
        json_out=tmp_path / "unity_vs_grill.json",
        md_out=tmp_path / "unity_vs_grill.md",
    )
    monkeypatch.setattr(run_unity_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unity_grill_benchmark.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unity_grill_benchmark, "DEFAULT_RAW_BASELINE", raw)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        if cmd[1] == "tools/normalize_unity_grill_baseline.py":
            shared.write_text("{}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(run_unity_grill_benchmark, "run_step", fake_run_step)

    rc = run_unity_grill_benchmark.main()

    assert rc == 0
    assert recorded[0][1] == "tools/normalize_unity_grill_baseline.py"
    assert recorded[1][1] == "tools/run_engine_head_to_head_matrix.py"


def test_unity_runner_main_captures_baseline_when_import_smoke_passes(monkeypatch, tmp_path: Path) -> None:
    raw = tmp_path / "grill_unity_benchmark_baseline.json"
    shared = tmp_path / "grill_unity_engine_benchmark_report.json"
    import_smoke = tmp_path / "grill_unity_import_smoke.json"
    import_smoke.write_text('{"status":"pass"}\n', encoding="utf-8")
    args = run_unity_grill_benchmark.argparse.Namespace(
        fastdis=tmp_path / "fastdis_unity.json",
        grill_reports=[shared],
        if_available=False,
        json_out=tmp_path / "unity_vs_grill.json",
        md_out=tmp_path / "unity_vs_grill.md",
    )
    monkeypatch.setattr(run_unity_grill_benchmark, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(run_unity_grill_benchmark.load_local_env, "load", lambda: None)
    monkeypatch.setattr(run_unity_grill_benchmark, "DEFAULT_RAW_BASELINE", raw)
    monkeypatch.setattr(run_unity_grill_benchmark, "DEFAULT_IMPORT_SMOKE", import_smoke)
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        if cmd[1] == "tools/capture_grill_unity_benchmark.py":
            raw.write_text("{}\n", encoding="utf-8")
        if cmd[1] == "tools/normalize_unity_grill_baseline.py":
            shared.write_text("{}\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(run_unity_grill_benchmark, "run_step", fake_run_step)

    rc = run_unity_grill_benchmark.main()

    assert rc == 0
    assert recorded[0][1] == "tools/capture_grill_unity_benchmark.py"
    assert recorded[1][1] == "tools/normalize_unity_grill_baseline.py"
    assert recorded[2][1] == "tools/run_engine_head_to_head_matrix.py"
