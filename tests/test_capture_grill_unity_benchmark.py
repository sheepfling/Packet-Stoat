from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_baseline_payload_uses_runner_metrics(tmp_path: Path) -> None:
    module = _load_module("capture_grill_unity_benchmark", ROOT / "tools" / "capture_grill_unity_benchmark.py")
    plugin_root = tmp_path / "GRILL_DISPluginForUnity"
    plugin_root.mkdir()

    runner_report = {
        "status": "pass",
        "packets_per_sec": 12000.5,
        "main_thread_ms_avg": 0.83,
        "gc_alloc_bytes_per_packet": 12,
        "notes": ["note one"],
    }

    payload = module.build_baseline_payload(
        runner_report,
        plugin_root=plugin_root,
        unity_version="6000.5.0f1",
        count=24,
        entity_count=1,
        rate_hz=10.0,
    )

    assert payload["schema"] == "fastdis.unity_grill_benchmark_baseline.v1"
    assert payload["product"] == "GRILL DIS for Unity"
    assert payload["unity"]["version"] == "6000.5.0f1"
    assert payload["results"][0]["case"] == "entity_state_1x10hz"
    assert payload["results"][0]["packets_per_sec"] == 12000.5
    assert payload["results"][0]["main_thread_ms_avg"] == 0.83


def test_load_json_accepts_utf8_bom(tmp_path: Path) -> None:
    module = _load_module("capture_grill_unity_benchmark", ROOT / "tools" / "capture_grill_unity_benchmark.py")
    payload_path = tmp_path / "runner.json"
    payload_path.write_text("\ufeff{\"status\":\"pass\"}\n", encoding="utf-8")

    payload = module._load_json(payload_path)

    assert payload["status"] == "pass"
