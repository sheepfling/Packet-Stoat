from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_workflow


def test_doctor_payload_reports_missing_install() -> None:
    payload = unreal_workflow.doctor_payload("9.9")

    assert payload["status"] == "missing-install"
    assert payload["checks"][0]["status"] == "fail"
    assert "no Unreal install discovered" in payload["checks"][0]["detail"]


def test_build_command_defaults_to_clean_package() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        open_rider=False,
        no_clean_package=False,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_build(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/build_unreal_plugin.py", "--engine-version", "5.8", "--clean-package"]]


def test_verify_command_forwards_dry_run() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.7",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_verify(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_unreal_orientation_verification.py", "--engine-version", "5.7", "--dry-run"]]


def test_demo_command_forwards_dry_run() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_demo(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_unreal_demo_smoke.py", "--engine-version", "5.8", "--dry-run"]]


def test_install_smoke_command_forwards_dry_run() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_install_smoke(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[sys.executable, "tools/run_unreal_packaged_install_smoke.py", "--engine-version", "5.8", "--dry-run"]]


def test_grill_baseline_init_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        out="/tmp/grill_unreal.json",
        fastdis="/tmp/current.json",
        engine_version="5.8",
        map="LoopbackBench",
        traffic_mix="100% Entity State",
        commit="def456",
        limit_cases=5,
        overwrite=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_grill_baseline_init(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/init_unreal_grill_benchmark_baseline.py",
        "--out",
        "/tmp/grill_unreal.json",
        "--fastdis",
        "/tmp/current.json",
        "--engine-version",
        "5.8",
        "--map",
        "LoopbackBench",
        "--traffic-mix",
        "100% Entity State",
        "--commit",
        "def456",
        "--limit-cases",
        "5",
        "--overwrite",
    ]]


def test_swap_baseline_init_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["swap-baseline-init", "--engine-version", "5.8"])

    assert args.command == "swap-baseline-init"
    assert args.engine_version == "5.8"


def test_grill_mapping_export_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        example_root="/tmp/GRILL_DISForUnrealExample",
        asset_path="/Game/DISEnumerationMappings",
        export_json="/tmp/grill_mapping_export.json",
        json_out="/tmp/grill_mapping_export_report.json",
        markdown_out="/tmp/grill_mapping_export_report.md",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_grill_mapping_export(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_grill_unreal_mapping_export.py",
        "--example-root",
        "/tmp/GRILL_DISForUnrealExample",
        "--asset-path",
        "/Game/DISEnumerationMappings",
        "--export-json",
        "/tmp/grill_mapping_export.json",
        "--json-out",
        "/tmp/grill_mapping_export_report.json",
        "--markdown-out",
        "/tmp/grill_mapping_export_report.md",
        "--engine-version",
        "5.8",
        "--dry-run",
    ]]


def test_swap_mapping_export_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["swap-mapping-export", "--engine-version", "5.8"])

    assert args.command == "swap-mapping-export"
    assert args.engine_version == "5.8"


def test_grill_mapping_import_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        input="/tmp/grill_mapping_export.json",
        fastdis_out="/tmp/fastdis_mapping_manifest.json",
        json_out="/tmp/grill_mapping_import_report.json",
        md_out="/tmp/grill_mapping_import_report.md",
        source_route="AF-GRILL/DISPluginForUnreal@ue5",
        search_roots=["/tmp/GRILL_DISForUnrealExample"],
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_grill_mapping_import(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/import_unreal_grill_mapping_manifest.py",
        "--input",
        "/tmp/grill_mapping_export.json",
        "--fastdis-out",
        "/tmp/fastdis_mapping_manifest.json",
        "--json-out",
        "/tmp/grill_mapping_import_report.json",
        "--md-out",
        "/tmp/grill_mapping_import_report.md",
        "--source-route",
        "AF-GRILL/DISPluginForUnreal@ue5",
        "--search-root",
        "/tmp/GRILL_DISForUnrealExample",
    ]]


def test_swap_mapping_import_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["swap-mapping-import", "--input", "/tmp/grill_mapping_export.json"])

    assert args.command == "swap-mapping-import"
    assert args.input == "/tmp/grill_mapping_export.json"


def test_grill_mapping_materialize_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        example_root="/tmp/GRILL_DISForUnrealExample",
        input_manifest="/tmp/fastdis_mapping_manifest.json",
        asset_path="/Game/FastDis/DA_ImportedGRILLMappings",
        result_json="/tmp/grill_mapping_materialize.json",
        json_out="/tmp/grill_mapping_materialize_report.json",
        markdown_out="/tmp/grill_mapping_materialize_report.md",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_grill_mapping_materialize(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_grill_mapping_materialize.py",
        "--example-root",
        "/tmp/GRILL_DISForUnrealExample",
        "--input-manifest",
        "/tmp/fastdis_mapping_manifest.json",
        "--asset-path",
        "/Game/FastDis/DA_ImportedGRILLMappings",
        "--result-json",
        "/tmp/grill_mapping_materialize.json",
        "--json-out",
        "/tmp/grill_mapping_materialize_report.json",
        "--markdown-out",
        "/tmp/grill_mapping_materialize_report.md",
        "--engine-version",
        "5.8",
        "--dry-run",
    ]]


def test_swap_mapping_materialize_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["swap-mapping-materialize", "--engine-version", "5.8"])

    assert args.command == "swap-mapping-materialize"
    assert args.engine_version == "5.8"


def test_grill_swap_smoke_command_builds_expected_runner_sequence() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        example_root="/tmp/GRILL_DISForUnrealExample",
        asset_path="/Game/DISEnumerationMappings",
        export_json="/tmp/grill_mapping_export.json",
        export_report_json="/tmp/grill_mapping_export_report.json",
        export_report_md="/tmp/grill_mapping_export_report.md",
        fastdis_out="/tmp/fastdis_mapping_manifest.json",
        import_report_json="/tmp/grill_mapping_import_report.json",
        import_report_md="/tmp/grill_mapping_import_report.md",
        source_route="AF-GRILL/DISPluginForUnreal@ue5",
        search_roots=["/tmp/GRILL_DISForUnrealExample"],
        materialized_asset_path="/Game/FastDis/DA_ImportedGRILLMappings",
        materialize_result_json="/tmp/grill_mapping_materialize.json",
        materialize_report_json="/tmp/grill_mapping_materialize_report.json",
        materialize_report_md="/tmp/grill_mapping_materialize_report.md",
        dry_run=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_grill_swap_smoke(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [
        [
            sys.executable,
            "tools/run_grill_unreal_mapping_export.py",
            "--example-root",
            "/tmp/GRILL_DISForUnrealExample",
            "--asset-path",
            "/Game/DISEnumerationMappings",
            "--export-json",
            "/tmp/grill_mapping_export.json",
            "--json-out",
            "/tmp/grill_mapping_export_report.json",
            "--markdown-out",
            "/tmp/grill_mapping_export_report.md",
            "--engine-version",
            "5.8",
            "--dry-run",
        ],
        [
            sys.executable,
            "tools/import_unreal_grill_mapping_manifest.py",
            "--input",
            "/tmp/grill_mapping_export.json",
            "--fastdis-out",
            "/tmp/fastdis_mapping_manifest.json",
            "--json-out",
            "/tmp/grill_mapping_import_report.json",
            "--md-out",
            "/tmp/grill_mapping_import_report.md",
            "--source-route",
            "AF-GRILL/DISPluginForUnreal@ue5",
            "--search-root",
            "/tmp/GRILL_DISForUnrealExample",
        ],
        [
            sys.executable,
            "tools/run_unreal_grill_mapping_materialize.py",
            "--example-root",
            "/tmp/GRILL_DISForUnrealExample",
            "--input-manifest",
            "/tmp/fastdis_mapping_manifest.json",
            "--asset-path",
            "/Game/FastDis/DA_ImportedGRILLMappings",
            "--result-json",
            "/tmp/grill_mapping_materialize.json",
            "--json-out",
            "/tmp/grill_mapping_materialize_report.json",
            "--markdown-out",
            "/tmp/grill_mapping_materialize_report.md",
            "--engine-version",
            "5.8",
            "--dry-run",
        ],
    ]


def test_swap_smoke_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["swap-smoke", "--engine-version", "5.8"])

    assert args.command == "swap-smoke"
    assert args.engine_version == "5.8"


def test_grill_benchmark_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        fastdis="/tmp/unreal_engine_benchmark_report.json",
        grill_reports=["/tmp/grill_unreal_engine_benchmark_report.json"],
        allow_sample_grill=True,
        out_dir="/tmp/engine_head_to_head",
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_grill_benchmark(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_grill_benchmark.py",
        "--fastdis",
        "/tmp/unreal_engine_benchmark_report.json",
        "--json-out",
        "/tmp/engine_head_to_head/unreal_vs_grill.json",
        "--md-out",
        "/tmp/engine_head_to_head/unreal_vs_grill.md",
        "--grill-report",
        "/tmp/grill_unreal_engine_benchmark_report.json",
        "--allow-sample-grill",
    ]]


def test_swap_benchmark_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["swap-benchmark"])

    assert args.command == "swap-benchmark"


def test_matrix_command_forwards_skip_flags() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        versions=["5.6", "5.7", "5.8"],
        skip_plugin_build=True,
        skip_orientation=False,
        skip_demo=True,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_matrix(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_matrix.py",
        "--versions",
        "5.6",
        "5.7",
        "5.8",
        "--skip-plugin-build",
        "--skip-demo",
    ]]


def test_doctor_payload_marks_platform_probe_failure(monkeypatch) -> None:
    install = SimpleNamespace(
        version="5.6",
        install_root="/Users/Shared/Epic Games/UE_5.6",
        editor_path="/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/Mac/UnrealEditor",
        uat_path="/Users/Shared/Epic Games/UE_5.6/Engine/Build/BatchFiles/RunUAT.sh",
        ubt_path="/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll",
        dotnet_path="/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/ThirdParty/DotNet/8.0.300/mac-arm64/dotnet",
        quirks=("editor app bundle present",),
        to_dict=lambda: {
            "version": "5.6",
            "install_root": "/Users/Shared/Epic Games/UE_5.6",
            "editor_path": "/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/Mac/UnrealEditor",
            "uat_path": "/Users/Shared/Epic Games/UE_5.6/Engine/Build/BatchFiles/RunUAT.sh",
            "ubt_path": "/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll",
            "dotnet_path": "/Users/Shared/Epic Games/UE_5.6/Engine/Binaries/ThirdParty/DotNet/8.0.300/mac-arm64/dotnet",
            "quirks": ["editor app bundle present"],
        },
    )

    monkeypatch.setattr(unreal_workflow, "install_for_version", lambda version: install)
    monkeypatch.setattr(
        unreal_workflow.unreal_env,
        "probe_host_platform_support",
        lambda install, project_path=None: {
            "status": "fail",
            "failure_kind": "host-mac-platform-unavailable",
            "detail": "host Mac SDK/platform rejected by this engine install before plugin code compiled; verify the engine/Xcode/macOS compatibility for this Unreal minor",
        },
    )

    payload = unreal_workflow.doctor_payload("5.6")
    assert payload["status"] == "needs-attention"
    assert any(check["name"] == "host platform probe" and check["status"] == "fail" for check in payload["checks"])
