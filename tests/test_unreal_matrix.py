from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_unreal_matrix


def test_classify_failure_recognizes_known_failure_modes() -> None:
    assert run_unreal_matrix.classify_failure(
        "Platform Mac is not a valid platform to build. Check that the SDK is installed properly."
    ) == "host-mac-platform-unavailable"
    assert run_unreal_matrix.classify_failure(
        "host Mac SDK/platform rejected by this engine install before plugin code compiled; verify the engine/Xcode/macOS compatibility for this Unreal minor"
    ) == "host-mac-platform-unavailable"
    assert run_unreal_matrix.classify_failure(
        "Access to the path '/Users/rick/Library/Logs/Unreal Engine/LocalBuildLogs' is denied."
    ) == "sandbox-home-write-denied"
    assert run_unreal_matrix.classify_failure(
        "managed/sandboxed run denied Unreal writes under ~/Library; rerun outside the sandbox or provide writable Unreal log/cache paths"
    ) == "sandbox-home-write-denied"
    assert run_unreal_matrix.classify_failure(
        "A conflicting instance of AutomationTool is already running"
    ) == "automationtool-conflict"
    assert run_unreal_matrix.classify_failure(
        "Could not find an Unreal editor executable for version 5.8"
    ) == "missing-editor"
    assert run_unreal_matrix.classify_failure(
        "Could not locate an Unreal Engine install for version 5.8"
    ) == "missing-install"


def test_failure_note_maps_known_failure_kinds() -> None:
    assert "managed/sandboxed run denied Unreal writes" in run_unreal_matrix.failure_note("sandbox-home-write-denied")
    assert "host Mac SDK/platform rejected" in run_unreal_matrix.failure_note("host-mac-platform-unavailable")
    assert "AutomationTool instance" in run_unreal_matrix.failure_note("automationtool-conflict")
    assert "editor executable" in run_unreal_matrix.failure_note("missing-editor")
    assert "install was not discovered" in run_unreal_matrix.failure_note("missing-install")
    assert run_unreal_matrix.failure_note("unknown-kind") is None


def test_summarize_markdown_includes_demo_column_and_notes() -> None:
    report = {
        "generated_at": "2026-06-19T12:00:00Z",
        "host_platform": "darwin",
        "results": [
            {
                "version": "5.7",
                "discovered": True,
                "notes": ["plugin build failed", "host Mac SDK/platform rejected by this engine install before plugin code compiled"],
                "plugin_build": {"status": "failed"},
                "orientation": {"status": "passed"},
                "demo": {"status": "skipped"},
                "install": {
                    "install_root": "/Users/Shared/Epic Games/UE_5.7",
                    "editor_path": "/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor",
                    "uat_path": "/Users/Shared/Epic Games/UE_5.7/Engine/Build/BatchFiles/RunUAT.sh",
                    "quirks": ["editor app bundle present"],
                },
            }
        ],
    }

    markdown = run_unreal_matrix.summarize_markdown(report)

    assert "| Version | Discovered | Plugin Build | Orientation | Demo | Notes |" in markdown
    assert "| 5.7 | yes | failed | passed | skipped | plugin build failed; host Mac SDK/platform rejected by this engine install before plugin code compiled |" in markdown
    assert "### 5.7" in markdown
    assert "- quirk: editor app bundle present" in markdown


def test_main_writes_matrix_reports_and_classifies_lane_failures(monkeypatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"

    class FakeInstall:
        def __init__(self, version: str) -> None:
            self.version = version

        def to_dict(self) -> dict[str, object]:
            return {
                "version": self.version,
                "install_root": f"/Engines/UE_{self.version}",
                "editor_path": f"/Engines/UE_{self.version}/UnrealEditor",
                "uat_path": f"/Engines/UE_{self.version}/RunUAT.sh",
                "quirks": [],
            }

    monkeypatch.setattr(
        run_unreal_matrix,
        "parse_args",
        lambda: run_unreal_matrix.argparse.Namespace(
            versions=["5.6", "5.8"],
            out_dir=str(out_dir),
            skip_orientation=False,
            skip_plugin_build=False,
            skip_demo=False,
        ),
    )
    monkeypatch.setattr(run_unreal_matrix.load_local_env, "load", lambda: None)
    monkeypatch.setattr(
        run_unreal_matrix.unreal_env,
        "discover_installs",
        lambda: [FakeInstall("5.6"), FakeInstall("5.8")],
    )

    def fake_run_step(cmd: list[str]) -> tuple[int, str]:
        if any(part.endswith("build_unreal_plugin.py") for part in cmd):
            version = cmd[cmd.index("--engine-version") + 1]
            if version == "5.6":
                return 1, "Platform Mac is not a valid platform to build"
            return 0, "plugin ok"
        if any(part.endswith("run_unreal_orientation_verification.py") for part in cmd):
            return 0, "orientation ok"
        if any(part.endswith("run_unreal_demo_smoke.py") for part in cmd):
            return 0, "demo ok"
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(run_unreal_matrix, "run_step", fake_run_step)

    exit_code = run_unreal_matrix.main()

    assert exit_code == 2
    json_path = out_dir / "unreal_version_matrix.json"
    md_path = out_dir / "unreal_version_matrix.md"
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload["results"]) == 2
    lane_56 = next(result for result in payload["results"] if result["version"] == "5.6")
    lane_58 = next(result for result in payload["results"] if result["version"] == "5.8")
    assert lane_56["plugin_build"]["status"] == "failed"
    assert lane_56["plugin_build"]["failure_kind"] == "host-mac-platform-unavailable"
    assert any("host Mac SDK/platform rejected" in note for note in lane_56["notes"])
    assert lane_56["orientation"]["status"] == "passed"
    assert lane_56["demo"]["status"] == "passed"
    assert lane_58["plugin_build"]["status"] == "passed"
    assert lane_58["orientation"]["status"] == "passed"
    assert lane_58["demo"]["status"] == "passed"
