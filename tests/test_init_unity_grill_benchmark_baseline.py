from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_init_unity_grill_benchmark_baseline_scaffolds_from_fastdis_cases(tmp_path: Path) -> None:
    out = tmp_path / "grill.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "init_unity_grill_benchmark_baseline.py"),
            "--out",
            str(out),
            "--unity-version",
            "6000.5.0f1",
            "--scene",
            "LoopbackBench",
            "--traffic-mix",
            "100% Entity State",
            "--scripting-backend",
            "Mono",
            "--commit",
            "abc123",
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
    assert payload["unity"]["version"] == "6000.5.0f1"
    assert payload["scenario"]["scene"] == "LoopbackBench"
    assert payload["scenario"]["traffic_mix"] == "100% Entity State"
    assert payload["repository"]["commit"] == "abc123"
    assert len(payload["results"]) == 3
    assert payload["results"][0]["case"] == "header_all_no_callback"


def test_init_unity_grill_benchmark_baseline_refuses_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "grill.json"
    out.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "init_unity_grill_benchmark_baseline.py"),
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
