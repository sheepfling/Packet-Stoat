from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_init_unreal_grill_benchmark_baseline_scaffolds_from_fastdis_cases(tmp_path: Path) -> None:
    out = tmp_path / "grill_unreal.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "init_unreal_grill_benchmark_baseline.py"),
            "--out",
            str(out),
            "--engine-version",
            "5.8",
            "--map",
            "LoopbackBench",
            "--traffic-mix",
            "100% Entity State",
            "--commit",
            "def456",
            "--limit-cases",
            "3",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["engine"]["version"] == "5.8"
    assert payload["scenario"]["map"] == "LoopbackBench"
    assert payload["scenario"]["traffic_mix"] == "100% Entity State"
    assert payload["repository"]["commit"] == "def456"
    assert len(payload["results"]) == 3
    assert payload["results"][0]["scenario"] == "header_all_no_callback"
    assert payload["results"][0]["packets_per_sec"] > 0


def test_init_unreal_grill_benchmark_baseline_refuses_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "grill_unreal.json"
    out.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "init_unreal_grill_benchmark_baseline.py"),
            "--out",
            str(out),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode != 0
    assert "Refusing to overwrite" in result.stdout
