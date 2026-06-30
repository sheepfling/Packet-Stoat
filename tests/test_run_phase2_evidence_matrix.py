from __future__ import annotations

import importlib.util
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


def test_build_steps_default_runs_refresh_and_storefront_renders() -> None:
    module = _load_module("run_phase2_evidence_matrix", ROOT / "tools" / "run_phase2_evidence_matrix.py")

    args = module.parse_args([])
    steps = module.build_steps(args)
    rendered = [" ".join(step[1:]) for step in steps]

    assert rendered == [
        "tools/refresh_engine_benchmark_artifacts.py",
        "tools/render_benchmark_storefront_charts.py",
        "tools/render_orientation_storefront_collages.py",
    ]


def test_build_steps_imports_bundles_before_single_refresh() -> None:
    module = _load_module("run_phase2_evidence_matrix", ROOT / "tools" / "run_phase2_evidence_matrix.py")

    args = module.parse_args(
        [
            "--unity-host-report",
            "unity-windows.zip",
            "--alpha2-host-report",
            "alpha2-linux.zip",
            "--competitor-handoff",
            "competitor.zip",
            "--core-only",
        ]
    )
    steps = module.build_steps(args)
    rendered = [" ".join(step[1:]) for step in steps]

    assert rendered[0] == "tools/import_unity_host_report.py unity-windows.zip --overwrite"
    assert rendered[1] == "tools/import_alpha2_host_report.py alpha2-linux.zip --overwrite"
    assert rendered[2] == "tools/import_competitor_benchmark_handoff.py competitor.zip --overwrite --skip-refresh"
    assert rendered[3] == "tools/refresh_engine_benchmark_artifacts.py --core-only"
    assert rendered[4] == "tools/render_benchmark_storefront_charts.py"
    assert rendered[5] == "tools/render_orientation_storefront_collages.py"


def test_build_steps_forwards_extra_refresh_args() -> None:
    module = _load_module("run_phase2_evidence_matrix", ROOT / "tools" / "run_phase2_evidence_matrix.py")

    args = module.parse_args(
        [
            "--core-only",
            "--refresh-arg=--skip-network-ingest-matrix",
            "--refresh-arg=--skip-network-ingest-normalize",
        ]
    )
    steps = module.build_steps(args)
    rendered = [" ".join(step[1:]) for step in steps]

    assert rendered[0] == (
        "tools/refresh_engine_benchmark_artifacts.py --core-only "
        "--skip-network-ingest-matrix --skip-network-ingest-normalize"
    )


def test_list_steps_mode_prints_exact_phase2_sequence(capsys) -> None:
    module = _load_module("run_phase2_evidence_matrix", ROOT / "tools" / "run_phase2_evidence_matrix.py")

    rc = module.main(["--core-only", "--list-steps"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "# run_phase2_evidence_matrix planned steps" in captured.out
    assert "tools/refresh_engine_benchmark_artifacts.py --core-only" in captured.out
    assert "tools/render_benchmark_storefront_charts.py" in captured.out
    assert "tools/render_orientation_storefront_collages.py" in captured.out
