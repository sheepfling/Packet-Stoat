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


def test_build_steps_core_only_excludes_blocked_engine_and_competitor_lanes() -> None:
    module = _load_module("refresh_engine_benchmark_artifacts", ROOT / "tools" / "refresh_engine_benchmark_artifacts.py")
    args = module.parse_args(["--core-only"])
    steps = module.build_steps(args)
    rendered = [" ".join(step[1:]) for step in steps]

    assert "tools/run_native_canonical_benchmark.py --if-available" in rendered
    assert "tools/normalize_current_benchmarks.py" in rendered
    assert "tools/run_network_ingest_matrix.py --if-available --out-dir build/reports/network_ingest_matrix --core-only" in rendered
    assert "tools/normalize_godot_proof_reports.py" in rendered
    assert "tools/build_benchmark_matrix_report.py" in rendered
    assert "tools/build_benchmark_coverage_report.py" in rendered
    assert "tools/build_scenario_contract_report.py" in rendered
    assert "tools/build_core_cross_platform_harness_report.py" in rendered
    assert "tools/check_benchmark_contract_stack.py --fail-missing" in rendered

    assert not any("unreal" in step for step in rendered)
    assert not any("unity" in step for step in rendered)
    assert not any("competitor" in step for step in rendered)
    assert not any("build_cross_engine_equivalence_report.py" in step for step in rendered)
    assert not any("audit_engine_benchmark_completion.py" in step for step in rendered)


def test_build_steps_core_only_keeps_downstream_reports_after_benchmark_matrix() -> None:
    module = _load_module("refresh_engine_benchmark_artifacts", ROOT / "tools" / "refresh_engine_benchmark_artifacts.py")
    args = module.parse_args(["--core-only"])
    steps = module.build_steps(args)
    rendered = [" ".join(step[1:]) for step in steps]

    matrix_index = rendered.index("tools/build_benchmark_matrix_report.py")
    coverage_index = rendered.index("tools/build_benchmark_coverage_report.py")
    scenario_index = rendered.index("tools/build_scenario_contract_report.py")
    harness_index = rendered.index("tools/build_core_cross_platform_harness_report.py")
    contract_index = rendered.index("tools/check_benchmark_contract_stack.py --fail-missing")

    assert matrix_index < coverage_index < scenario_index < harness_index < contract_index


def test_render_steps_and_list_steps_mode_show_exact_commands(capsys) -> None:
    module = _load_module("refresh_engine_benchmark_artifacts", ROOT / "tools" / "refresh_engine_benchmark_artifacts.py")
    args = module.parse_args(["--core-only"])
    steps = module.build_steps(args)
    rendered = module.render_steps(steps)

    assert rendered[0].endswith("tools/run_native_canonical_benchmark.py --if-available")
    assert any("tools/build_benchmark_matrix_report.py" in row for row in rendered)

    rc = module.main(["--core-only", "--list-steps"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "# refresh_engine_benchmark_artifacts planned steps" in captured.out
    assert "tools/run_native_canonical_benchmark.py --if-available" in captured.out
