from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_alpha3_verification_closeout


def test_closeout_runner_writes_summary(monkeypatch, tmp_path: Path) -> None:
    def fake_run_step(command: list[str]) -> tuple[int, str]:
        return 0, "ok"

    monkeypatch.setattr(run_alpha3_verification_closeout, "run_step", fake_run_step)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_alpha3_verification_closeout.py",
            "--out-dir",
            str(tmp_path),
        ],
    )
    rc = run_alpha3_verification_closeout.main()
    assert rc == 0
    payload = json.loads((tmp_path / "alpha3_verification_closeout.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "passed"
    names = [lane["name"] for lane in payload["lanes"]]
    assert names == [
        "orientation_core",
        "orientation_pipeline",
        "orientation_visual",
        "network_ingest",
        "sanitizer_smoke",
        "benchmark_matrix",
        "release_audit",
        "stage_host_bundle",
    ]
    assert (tmp_path / "alpha3_verification_closeout.md").is_file()
