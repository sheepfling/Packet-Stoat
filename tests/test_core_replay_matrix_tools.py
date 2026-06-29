from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_run_core_replay_matrix_main_writes_outputs_if_routes_pending(tmp_path: Path) -> None:
    module = _load_module("run_core_replay_matrix", ROOT / "tools" / "run_core_replay_matrix.py")
    module.C_REPLAY = tmp_path / "missing_c"
    module.CPP_REPLAY = tmp_path / "missing_cpp"
    out_dir = tmp_path / "out"
    rc = module.main(["--out-dir", str(out_dir), "--if-available"])
    assert rc == 0
    payload = json.loads((out_dir / "core_replay_matrix.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.core_replay_matrix.v1"
    assert payload["scenario"] == "replay_latest_state_apply"
    assert len(payload["routes"]) == 2


def test_normalize_core_replay_matrix_appends_rows(tmp_path: Path) -> None:
    _load_module("normalize_core_replay_matrix", ROOT / "tools" / "normalize_core_replay_matrix.py")
    input_path = _write(
        tmp_path / "core_replay_matrix.json",
        {
            "routes": [
                {
                    "surface": "c",
                    "status": "passed",
                    "scenario": "replay_latest_state_apply",
                    "scenario_suite": "core_matrix",
                    "elapsed_seconds": 0.2,
                    "report": {
                        "packets_received": 300,
                        "packets_parsed": 300,
                        "entity_state": 300,
                        "malformed": 0,
                    },
                    "errors": [],
                },
                {
                    "surface": "cpp",
                    "status": "passed",
                    "scenario": "replay_latest_state_apply",
                    "scenario_suite": "core_matrix",
                    "elapsed_seconds": 0.1,
                    "report": {
                        "packets_received": 300,
                        "packets_parsed": 300,
                        "entity_state": 300,
                        "malformed": 0,
                    },
                    "errors": [],
                },
            ]
        },
    )
    out_dir = tmp_path / "engine_benchmarks"
    for surface in ("c", "cpp"):
        _write(
            out_dir / f"{surface}_engine_benchmark_report.json",
            {
                "schema": "fastdis.engine_benchmark_report.v1",
                "surface": surface,
                "rows": [
                    {
                        "scenario": "entity_state_1x10hz",
                        "metrics": {"runtime_elapsed_seconds": 0.01, "p95_ingest_ms": None},
                        "truth": {"final_truth_match": True},
                    }
                ],
                "summary": {"row_count": 1, "latency_rows": 0, "runtime_metric_rows": 1, "truth_rows": 1},
            },
        )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "normalize_core_replay_matrix.py"),
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    for surface in ("c", "cpp"):
        payload = json.loads((out_dir / f"{surface}_engine_benchmark_report.json").read_text(encoding="utf-8"))
        assert any(row["scenario"] == "replay_latest_state_apply" for row in payload["rows"])
