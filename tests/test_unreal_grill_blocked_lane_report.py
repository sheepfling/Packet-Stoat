from __future__ import annotations

import importlib.util
import json
from pathlib import Path


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
