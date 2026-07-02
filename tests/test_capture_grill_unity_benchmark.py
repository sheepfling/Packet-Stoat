from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from conftest import TEST_UNITY_EDITOR_VERSION


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
        unity_version=TEST_UNITY_EDITOR_VERSION,
        count=24,
        entity_count=1,
        rate_hz=10.0,
    )

    assert payload["schema"] == "fastdis.unity_grill_benchmark_baseline.v1"
    assert payload["product"] == "GRILL DIS for Unity"
    assert payload["unity"]["version"] == TEST_UNITY_EDITOR_VERSION
    assert payload["results"][0]["case"] == "entity_state_1x10hz"
    assert payload["results"][0]["packets_per_sec"] == 12000.5
    assert payload["results"][0]["main_thread_ms_avg"] == 0.83


def test_load_json_accepts_utf8_bom(tmp_path: Path) -> None:
    module = _load_module("capture_grill_unity_benchmark", ROOT / "tools" / "capture_grill_unity_benchmark.py")
    payload_path = tmp_path / "runner.json"
    payload_path.write_text("\ufeff{\"status\":\"pass\"}\n", encoding="utf-8")

    payload = module._load_json(payload_path)

    assert payload["status"] == "pass"


def test_main_normalizes_written_unity_baseline(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("capture_grill_unity_benchmark", ROOT / "tools" / "capture_grill_unity_benchmark.py")
    plugin_root = tmp_path / "GRILL_DISPluginForUnity"
    plugin_root.mkdir()
    out_dir = tmp_path / "unity_grill_baseline"
    normalized_out_dir = tmp_path / "engine_benchmarks"
    runner_json = out_dir / "grill_unity_benchmark_capture_runner.json"

    args = module.argparse.Namespace(
        plugin_root=plugin_root,
        unity_version=TEST_UNITY_EDITOR_VERSION,
        project_dir=tmp_path / "project",
        out_dir=out_dir,
        count=24,
        entity_count=1,
        rate_hz=10.0,
        normalized_out_dir=normalized_out_dir,
        timeout=180,
        overwrite=True,
        prepare_checkout=False,
    )

    monkeypatch.setattr(module, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(module.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        module.unity_env,
        "resolve_install",
        lambda version: module.unity_env.UnityInstall(
            version=version,
            install_root="C:/Unity",
            editor_path="C:/Unity/Editor/Unity.exe",
            editor_app_path=None,
            source="test",
            quirks=(),
        ),
    )
    monkeypatch.setattr(module.run_grill_unity_import_smoke, "create_project", lambda *a, **k: None)
    monkeypatch.setattr(module.run_grill_unity_import_smoke, "enable_required_builtin_modules", lambda *a, **k: None)
    monkeypatch.setattr(module, "_write_text", lambda path, text: None)
    monkeypatch.setattr(
        module,
        "_attempts",
        lambda install, project_dir, report_dir: [
            {
                "launch": "login-shell",
                "cmd": ["unity"],
                "launcher_log": tmp_path / "launcher.log",
                "results_json": runner_json,
            }
        ],
    )
    monkeypatch.setattr(module.run_unity_install_smoke, "clear_previous_artifacts", lambda *a: None)
    monkeypatch.setattr(module.unity_env, "build_env", lambda: {})
    def fake_run_attempt(cmd, env, launcher_log_path, timeout):
        runner_json.parent.mkdir(parents=True, exist_ok=True)
        runner_json.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "packets_per_sec": 12000.5,
                    "main_thread_ms_avg": 0.83,
                    "gc_alloc_bytes_per_packet": 12,
                    "notes": ["note one"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 0, False

    monkeypatch.setattr(module, "_run_attempt", fake_run_attempt)
    monkeypatch.setattr(module, "_git_commit", lambda path: "abc123")

    recorded: list[list[str]] = []

    def fake_normalize(argv: list[str]) -> int:
        recorded.append(argv)
        return 0

    monkeypatch.setattr(module.normalize_grill_harness_capture, "main", fake_normalize)

    rc = module.main()

    assert rc == 0
    payload = json.loads((out_dir / "grill_unity_benchmark_baseline.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.unity_grill_benchmark_baseline.v1"
    assert payload["results"][0]["packets_per_sec"] == 12000.5
    assert recorded == [
        [
            "--input",
            str((out_dir / "grill_unity_benchmark_baseline.json").resolve()),
            "--out-dir",
            str(normalized_out_dir.resolve()),
        ]
    ]
