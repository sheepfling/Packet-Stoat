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


def test_build_unreal_grill_blocked_lane_report_classifies_upstream_sample_plugins(tmp_path: Path) -> None:
    module = _load_module("build_unreal_grill_blocked_lane_report", ROOT / "tools" / "build_unreal_grill_blocked_lane_report.py")
    source = tmp_path / "grill_unreal_source_smoke.json"
    source.write_text(
        json.dumps(
            {
                "status": "probe-fail",
                "requested_engine_version": "5.8",
                "platform_probe": {
                    "failure_kind": "probe-timeout",
                    "output": "\n".join(
                        [
                            "CesiumRuntime.cpp(10): error C2039: 'PlatformData': is not a member of 'UTexture2D'",
                            "LowEntryExtendedStandardLibrary.cpp(20): error C2039: 'IsPendingKill': is not a member",
                        ]
                    ),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = module.build_report(source)

    assert report["lane"] == "ue5.8"
    assert "Cesium sample plugin is not forward-compatible with UE 5.8 on this route" in report["blockers"]
    assert "LowEntry sample plugin is not forward-compatible with UE 5.8 on this route" in report["blockers"]
    assert report["upstream_dependencies"]["CesiumForUnreal"]["blocked"] is True
    assert report["upstream_dependencies"]["LowEntryExtStdLib"]["blocked"] is True


def test_build_unreal_grill_blocked_lane_report_cli_writes_enveloped_json(tmp_path: Path) -> None:
    source = tmp_path / "grill_unreal_source_smoke.json"
    source.write_text(
        json.dumps(
            {
                "status": "probe-fail",
                "requested_engine_version": "5.8",
                "platform_probe": {
                    "failure_kind": "probe-timeout",
                    "output": "CesiumRuntime.cpp(10): error C2039: 'PlatformData': is not a member of 'UTexture2D'",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    json_out = tmp_path / "blocked.json"
    md_out = tmp_path / "blocked.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_unreal_grill_blocked_lane_report.py"),
            "--source-smoke",
            str(source),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["report_meta"]["canonical_format"] == "json"
    assert payload["report_meta"]["markdown_policy"] == "leaf-only"
    assert "Unreal GRILL Blocked Lane" in md_out.read_text(encoding="utf-8")
