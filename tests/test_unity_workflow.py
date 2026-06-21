from __future__ import annotations

from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_unity_native_matrix
import run_unity_editor_tests
import unity_env
import stage_unity_native
import unity_workflow


def test_unity_env_discovers_editor_from_versioned_env(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "6000.5.0f1"
    app = root / "Unity.app"
    executable = app / "Contents" / "MacOS" / "Unity"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("FASTDIS_UNITY_EDITOR_6000_5", str(app))

    install = unity_env.resolve_install("6000.5")

    assert install is not None
    assert install.version == "6000.5"
    assert install.editor_path == str(executable.resolve())


def test_unity_package_state_has_required_surface() -> None:
    state = unity_workflow.package_state()

    assert state
    assert all(state.values())


def test_stage_unity_native_copies_host_library(tmp_path: Path) -> None:
    package = tmp_path / "package"
    build = tmp_path / "build"
    out = tmp_path / "reports"
    build.mkdir()
    (build / "libfastdis.dylib").write_bytes(b"native")

    report = stage_unity_native.stage("macos", package, build, out)

    staged = package / "Runtime" / "Plugins" / "macOS" / "libfastdis.dylib"
    assert report["status"] == "pass"
    assert staged.read_bytes() == b"native"
    assert staged.with_name("libfastdis.dylib.meta").is_file()
    assert (out / "unity_native_stage_macos.json").is_file()


def test_unity_native_matrix_doctor_has_three_targets() -> None:
    payload = build_unity_native_matrix.doctor_payload()

    assert {"macos", "windows", "linux"} <= set(payload["targets"])
    assert payload["targets"]["macos"]["method"] == "host CMake"
    assert payload["targets"]["windows"]["method"] == "MinGW-w64 cross compile"
    assert payload["targets"]["linux"]["method"] == "Docker linux/amd64 CMake build"


def test_unity_build_env_redirects_home_cache_and_tmp(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FASTDIS_UNITY_WORK_ROOT", str(tmp_path / "unity_work"))

    env = unity_env.build_env()

    assert env["HOME"].startswith(str(tmp_path / "unity_work"))
    assert env["TMPDIR"].startswith(str(tmp_path / "unity_work"))
    assert env["XDG_CACHE_HOME"].startswith(str(tmp_path / "unity_work"))


def test_unity_doctor_reports_permission_checks() -> None:
    payload = unity_workflow.doctor_payload(None)
    check_names = {check["name"] for check in payload["checks"]}

    assert "permission:work_root" in check_names
    assert "permission:package_plugins" in check_names


def test_unity_doctor_payload_reports_package_and_warns_for_unstaged_native() -> None:
    payload = unity_workflow.doctor_payload(None)
    check_names = {check["name"] for check in payload["checks"]}

    assert payload["unity_alpha5_result"] in {"pass", "fail"}
    assert payload["passed_scope"] == "workflow/package/native-staging parity"
    assert payload["next_scope"] == "Unity Editor runtime verification"
    assert payload["unity_workflow_status"] in {"pass", "fail"}
    assert payload["unity_native_status"] in {"pass", "not_verified"}
    assert payload["unity_runtime_status"] in {"pass", "fail", "blocked_license", "not_run"}
    assert payload["unity_runtime_launcher"] in {
        "macos-login-shell-interactive",
        "batchmode",
        "batchmode-nographics",
    }
    assert payload["unity_demo_status"] == "not_run"
    assert payload["runtime_notes"]
    assert "package:package_json" in check_names
    assert "native:current-platform" in check_names
    assert "native:macos" in check_names
    assert "runtime:launcher" in check_names
    assert payload["package_root"].endswith("integrations/unity/com.sheepfling.fastdis")


def test_unity_runtime_verify_command_builds_expected_runner(monkeypatch) -> None:
    recorded: list[list[str]] = []

    def fake_run_step(cmd: list[str], **_kwargs: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr(unity_workflow, "run_step", fake_run_step)
    args = type(
        "Args",
        (),
        {
            "unity_version": "6000.5",
            "platform": ["EditMode"],
            "project_dir": "/tmp/fastdis_unity_test_project",
            "out_dir": "/tmp/fastdis_unity_reports",
            "timeout": 123,
            "dry_run": True,
        },
    )()

    assert unity_workflow.command_runtime_verify(args) == 0
    assert recorded
    assert recorded[0][:2] == unity_env.python_command() + ["tools/run_unity_editor_tests.py"][-1:]
    assert "--unity-version" in recorded[0]
    assert "--platform" in recorded[0]
    assert "--dry-run" in recorded[0]


def test_unity_editor_test_project_manifest_references_local_package(tmp_path: Path) -> None:
    project = tmp_path / "unity_project"

    run_unity_editor_tests.create_project(project)

    manifest = (project / "Packages" / "manifest.json").read_text(encoding="utf-8")
    assert "com.sheepfling.fastdis" in manifest
    assert "testables" in manifest


def test_unity_log_analysis_identifies_headless_entitlement(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "[Licensing::Module] Error: 'com.unity.editor.headless' was not found.\n"
        "No valid Unity Editor license found. Please activate your license.\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "blocked_license"
    assert analysis["code"] == "unity_headless_entitlement_missing"
    assert "FASTDIS_UNITY_BATCHMODE" in " ".join(analysis["remediation"])


def test_unity_log_analysis_identifies_ui_entitlement_environment_issue(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "[Licensing::Module] Error: 'com.unity.editor.ui' was not found.\n"
        "No valid Unity Editor license found. Please activate your license.\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "blocked_license"
    assert analysis["code"] == "unity_ui_entitlement_missing"
    assert "login-shell" in " ".join(analysis["remediation"])


def test_unity_log_analysis_identifies_invalid_meta_yaml(tmp_path: Path) -> None:
    log = tmp_path / "unity.log"
    log.write_text(
        "YAML Parsing error 'Parser Failure at line 18: Expect ':' between key and value within mapping'\n",
        encoding="utf-8",
    )

    analysis = run_unity_editor_tests.analyze_log(log)

    assert analysis["status"] == "unity_asset_meta_invalid"
    assert analysis["code"] == "unity_yaml_meta_invalid"
