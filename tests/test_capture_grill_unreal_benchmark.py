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


def test_build_baseline_payload_uses_experiment_style_shape(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("capture_grill_unreal_benchmark", ROOT / "tools" / "capture_grill_unreal_benchmark.py")
    plugin_root = tmp_path / "GRILL_DISPluginForUnreal"
    plugin_root.mkdir()
    monkeypatch.setattr(module, "_git_output", lambda _path, *args: "abc123" if args[:2] == ("rev-parse", "HEAD") else "https://github.com/AF-GRILL/DISPluginForUnreal")
    measurements = {
        "runtime": {"build_configuration": "Development Editor"},
        "scenario": {"entity_counts": [1, 100], "update_hz": [10, 30]},
        "results": [
            {
                "scenario": "entity_state_1x10hz",
                "packets_received": 24,
                "packets_parsed": 24,
                "packets_accepted": 24,
                "packets_rejected": 0,
                "malformed": 0,
                "socket_drops": 0,
                "queue_drops": 0,
                "p50_ingest_ms": 0.2,
                "p95_ingest_ms": 0.3,
                "p99_ingest_ms": 0.4,
                "steady_state_gc_bytes": 0,
                "main_thread_apply_ms": 0.1,
                "packets_per_sec": 1000.0,
            }
        ],
    }

    payload = module.build_baseline_payload(
        measurements,
        plugin_root=plugin_root,
        engine_version="5.8",
        map_name="LoopbackBench",
        traffic_mix="100% Entity State",
    )

    assert payload["schema"] == "fastdis.unreal_grill_benchmark_baseline.v1"
    assert payload["engine"]["version"] == "5.8"
    assert payload["scenario"]["map"] == "LoopbackBench"
    assert payload["results"][0]["scenario"] == "entity_state_1x10hz"


def test_capture_grill_unreal_benchmark_cli_writes_raw_and_normalized(tmp_path: Path) -> None:
    measurements = tmp_path / "grill_unreal_measurements.json"
    measurements.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario": "entity_state_1x10hz",
                        "packets_received": 24,
                        "packets_parsed": 24,
                        "packets_accepted": 24,
                        "packets_rejected": 0,
                        "malformed": 0,
                        "socket_drops": 0,
                        "queue_drops": 0,
                        "p50_ingest_ms": 0.2,
                        "p95_ingest_ms": 0.3,
                        "p99_ingest_ms": 0.4,
                        "steady_state_gc_bytes": 0,
                        "main_thread_apply_ms": 0.1,
                        "packets_per_sec": 1000.0,
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    plugin_root = tmp_path / "GRILL_DISPluginForUnreal"
    plugin_root.mkdir()
    subprocess.run(["git", "init"], cwd=plugin_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=plugin_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=plugin_root, check=True, capture_output=True, text=True)
    (plugin_root / "README.md").write_text("demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=plugin_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=plugin_root, check=True, capture_output=True, text=True)
    raw_out = tmp_path / "grill_unreal_benchmark_baseline.json"
    out_dir = tmp_path / "engine_benchmarks"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "capture_grill_unreal_benchmark.py"),
            "--measurements",
            str(measurements),
            "--plugin-root",
            str(plugin_root),
            "--engine-version",
            "5.8",
            "--map",
            "LoopbackBench",
            "--traffic-mix",
            "100% Entity State",
            "--raw-out",
            str(raw_out),
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    raw_payload = json.loads(raw_out.read_text(encoding="utf-8"))
    normalized = json.loads((out_dir / "grill_unreal_engine_benchmark_report.json").read_text(encoding="utf-8"))
    assert raw_payload["schema"] == "fastdis.unreal_grill_benchmark_baseline.v1"
    assert raw_payload["engine"]["version"] == "5.8"
    assert raw_payload["scenario"]["map"] == "LoopbackBench"
    assert normalized["surface"] == "grill_unreal"
    assert normalized["rows"][0]["metrics"]["p95_ingest_ms"] == 0.3
