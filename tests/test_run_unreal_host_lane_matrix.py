from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_host_lane_matrix


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_build_report_distinguishes_package_and_runtime_lanes(tmp_path: Path) -> None:
    unreal_matrix = tmp_path / "unreal_version_matrix.json"
    linux_proof = tmp_path / "fastdis_unreal_linux_proof.json"
    linux_verify = tmp_path / "fastdis_unreal_linux_verify.json"
    linux_demo = tmp_path / "fastdis_unreal_linux_demo.json"

    _write(
        unreal_matrix,
        {
            "results": [
                {
                    "plugin_build": {"status": "passed"},
                    "orientation": {"status": "passed"},
                    "demo": {"status": "passed"},
                }
            ]
        },
    )
    _write(linux_proof, {"status": "package-proof"})
    _write(linux_verify, {"status": "blocked-host-platform"})
    _write(linux_demo, {"status": "pass"})

    args = run_unreal_host_lane_matrix.parse_args(
        [
            "--unreal-matrix",
            str(unreal_matrix),
            "--linux-proof",
            str(linux_proof),
            "--linux-verify",
            str(linux_verify),
            "--linux-demo",
            str(linux_demo),
            "--out-dir",
            str(tmp_path),
        ]
    )

    report = run_unreal_host_lane_matrix.build_report(args)

    assert report["summary"]["present_count"] == 4
    assert report["summary"]["pass_count"] == 3
    lane_index = {row["lane"]: row for row in report["lanes"]}
    assert lane_index["linux-package-proof"]["evidence_kind"] == "package-proof"
    assert lane_index["linux-verify"]["evidence_kind"] == "blocked"
    assert lane_index["linux-demo"]["evidence_kind"] == "runtime-proof"

