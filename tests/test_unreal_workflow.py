from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_workflow


def test_linux_profile_for_version_prefers_grill_matched_profile() -> None:
    profile = unreal_workflow.linux_profile_for_version("5.8")

    assert profile.name == "ubuntu_24_04_ue58.env"


def test_doctor_payload_reports_missing_install() -> None:
    payload = unreal_workflow.doctor_payload("9.9")

    assert payload["status"] == "missing-install"
    assert payload["checks"][0]["status"] == "fail"
    assert "no Unreal install discovered" in payload["checks"][0]["detail"]


def test_windows_install_discovery_finds_editor_and_dotnet(monkeypatch, tmp_path: Path) -> None:
    engine_root = tmp_path / "UE_5.8"
    win64 = engine_root / "Engine" / "Binaries" / "Win64"
    dotnet_dir = engine_root / "Engine" / "Binaries" / "ThirdParty" / "DotNet" / "10.0" / "win-x64"
    ubt_dir = engine_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool"
    batch_dir = engine_root / "Engine" / "Build" / "BatchFiles"
    for directory in (win64, dotnet_dir, ubt_dir, batch_dir):
        directory.mkdir(parents=True, exist_ok=True)
    for path in (
        win64 / "UnrealEditor.exe",
        win64 / "UnrealEditor-Cmd.exe",
        dotnet_dir / "dotnet.exe",
        ubt_dir / "UnrealBuildTool.dll",
        batch_dir / "RunUAT.bat",
    ):
        path.write_text("x", encoding="utf-8")

    monkeypatch.setattr(unreal_workflow.unreal_env.platform, "system", lambda: "Windows")

    install = unreal_workflow.unreal_env._install_from_root(engine_root, source="scan")

    assert install is not None
    assert install.editor_path == str((win64 / "UnrealEditor.exe").resolve())
    assert install.editor_cmd_path == str((win64 / "UnrealEditor-Cmd.exe").resolve())
    assert install.dotnet_path == str((dotnet_dir / "dotnet.exe").resolve())


def test_windows_default_work_root_uses_localappdata(monkeypatch) -> None:
    monkeypatch.setattr(unreal_workflow.unreal_env.platform, "system", lambda: "Windows")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\rick\AppData\Local")
    monkeypatch.delenv("FASTDIS_UNREAL_WORK_ROOT", raising=False)

    work_root = unreal_workflow.unreal_env._default_work_root()

    assert str(work_root).replace("\\", "/").endswith("/Local/fastdis_unreal")
    assert " " not in str(work_root)


def test_install_for_version_accepts_patch_version_match(monkeypatch) -> None:
    install = SimpleNamespace(version="5.7.4")
    monkeypatch.setattr(unreal_workflow.unreal_env, "discover_installs", lambda: [install])

    assert unreal_workflow.install_for_version("5.7") is install


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


def test_linux_verify_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.7",
        unreal="/tmp/UnrealEditor",
        json_out="/tmp/linux_verify.json",
        md_out="/tmp/linux_verify.md",
        dry_run=True,
        docker=False,
        profile="/tmp/linux.env",
        engine_archive=None,
        engine_path=None,
        image=None,
        engine_stage_dir=None,
        force_reextract=False,
        timeout_seconds=600,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_linux_verify(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_linux_harness.py",
        "--mode",
        "verify",
        "--engine-version",
        "5.7",
        "--unreal",
        "/tmp/UnrealEditor",
        "--json-out",
        "/tmp/linux_verify.json",
        "--md-out",
        "/tmp/linux_verify.md",
        "--dry-run",
    ]]


def test_linux_demo_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.7",
        unreal=None,
        json_out=None,
        md_out=None,
        dry_run=False,
        docker=False,
        profile="/tmp/linux.env",
        engine_archive=None,
        engine_path=None,
        image=None,
        engine_stage_dir=None,
        force_reextract=False,
        timeout_seconds=600,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_linux_demo(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_linux_harness.py",
        "--mode",
        "demo",
        "--engine-version",
        "5.7",
    ]]


def test_linux_verify_command_builds_expected_docker_runner() -> None:
    profile = str(Path("/tmp/linux.env"))
    json_out = str(Path("/tmp/linux_verify.json"))
    md_out = str(Path("/tmp/linux_verify.md"))
    engine_archive = str(Path("/tmp/engine.zip"))
    engine_stage_dir = str(Path("/tmp/stage"))
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.7",
        unreal=None,
        json_out=json_out,
        md_out=md_out,
        dry_run=False,
        docker=True,
        profile=profile,
        engine_archive=engine_archive,
        engine_path=None,
        image="fastdis-linux-proof:ubuntu24.04",
        engine_stage_dir=engine_stage_dir,
        force_reextract=True,
        timeout_seconds=180,
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_linux_verify(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_linux_harness_docker.py",
        "--mode",
        "verify",
        "--engine-version",
        "5.7",
        "--json-out",
        json_out,
        "--md-out",
        md_out,
        "--profile",
        profile,
        "--engine-archive",
        engine_archive,
        "--image",
        "fastdis-linux-proof:ubuntu24.04",
        "--engine-stage-dir",
        engine_stage_dir,
        "--force-reextract",
        "--timeout-seconds",
        "180",
    ]]


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


def test_linux_verify_alias_is_supported() -> None:
    args = unreal_workflow.parse_args(["linux-verify", "--engine-version", "5.7"])

    assert args.command == "linux-verify"
    assert args.engine_version == "5.7"
    assert args.docker is False


def test_host_lane_matrix_command_builds_expected_runner() -> None:
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        out_dir="/tmp/reports",
        unreal_matrix="/tmp/unreal_version_matrix.json",
        linux_proof="/tmp/fastdis_unreal_linux_proof.json",
        linux_verify="/tmp/fastdis_unreal_linux_verify.json",
        linux_demo="/tmp/fastdis_unreal_linux_demo.json",
    )

    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str]) -> int:
        recorded.append(cmd)
        return 0

    original = unreal_workflow.run_step
    unreal_workflow.run_step = fake_run_step
    try:
        assert unreal_workflow.command_host_lane_matrix(args) == 0
    finally:
        unreal_workflow.run_step = original

    assert recorded == [[
        sys.executable,
        "tools/run_unreal_host_lane_matrix.py",
        "--out-dir",
        "/tmp/reports",
        "--unreal-matrix",
        "/tmp/unreal_version_matrix.json",
        "--linux-proof",
        "/tmp/fastdis_unreal_linux_proof.json",
        "--linux-verify",
        "/tmp/fastdis_unreal_linux_verify.json",
        "--linux-demo",
        "/tmp/fastdis_unreal_linux_demo.json",
    ]]


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
    fastdis = str(Path("/tmp/unreal_engine_benchmark_report.json"))
    grill_report = str(Path("/tmp/grill_unreal_engine_benchmark_report.json"))
    out_dir = Path("/tmp/engine_head_to_head")
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        fastdis=fastdis,
        grill_reports=[grill_report],
        allow_sample_grill=True,
        out_dir=str(out_dir),
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
        fastdis,
        "--json-out",
        str(out_dir / "unreal_vs_grill.json"),
        "--md-out",
        str(out_dir / "unreal_vs_grill.md"),
        "--grill-report",
        grill_report,
        "--allow-sample-grill",
    ]]


def test_grill_doctor_runs_doctor_source_smoke_and_swap(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    def fake_command_doctor(args: object) -> int:
        calls.append(("doctor", args))
        return 0

    def fake_run_step(cmd: list[str]) -> int:
        calls.append(("source-smoke", cmd))
        return 0

    def fake_command_grill_swap_smoke(args: object) -> int:
        calls.append(("swap", args))
        return 0

    monkeypatch.setattr(unreal_workflow, "command_doctor", fake_command_doctor)
    monkeypatch.setattr(unreal_workflow, "run_step", fake_run_step)
    monkeypatch.setattr(unreal_workflow, "command_grill_swap_smoke", fake_command_grill_swap_smoke)
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

    assert unreal_workflow.command_grill_doctor(args) == 0
    assert calls[0][0] == "doctor"
    assert getattr(calls[0][1], "engine_version") == "5.8"
    assert calls[1] == (
        "source-smoke",
        [
            sys.executable,
            "tools/run_grill_unreal_source_smoke.py",
            "--engine-version",
            "5.8",
        ],
    )
    assert calls[2] == ("swap", args)


def test_grill_full_runs_doctor_then_linux_then_benchmark(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    def fake_command_grill_doctor(args: object) -> int:
        calls.append(("doctor", args))
        return 0

    def fake_command_grill_linux_proof(args: object) -> int:
        calls.append(("linux", args))
        return 0

    def fake_command_grill_benchmark(args: object) -> int:
        calls.append(("benchmark", args))
        return 0

    monkeypatch.setattr(unreal_workflow, "command_grill_doctor", fake_command_grill_doctor)
    monkeypatch.setattr(unreal_workflow, "command_grill_linux_proof", fake_command_grill_linux_proof)
    monkeypatch.setattr(unreal_workflow, "command_grill_benchmark", fake_command_grill_benchmark)
    args = unreal_workflow.parse_args.__globals__["argparse"].Namespace(
        engine_version="5.8",
        plugin_root="/tmp/GRILL_DISPluginForUnreal",
        profile="/tmp/linux.env",
        package_dir="/tmp/package",
        json_out="/tmp/linux.json",
        md_out="/tmp/linux.md",
        fastdis="/tmp/fastdis.json",
        grill_reports=["/tmp/grill.json"],
        allow_sample_grill=True,
        out_dir="/tmp/reports",
    )

    assert unreal_workflow.command_grill_full(args) == 0
    assert calls == [("doctor", args), ("linux", args), ("benchmark", args)]


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
