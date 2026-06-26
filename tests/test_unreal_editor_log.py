from __future__ import annotations

from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import unreal_editor_log


def test_classify_plugin_version_incompatible() -> None:
    output = """
    LogInit: Warning: Plugin 'CesiumForUnreal' requires engine version '5.4.0' and may not be compatible with the current build.
    The following modules are missing or built with a different engine version:
    LogPluginManager: Warning: Plugin 'GRILLDISForUnreal' is designed for build 5.0.0
    """
    assert unreal_editor_log.classify_editor_failure(output) == "plugin-version-incompatible"


def test_classify_missing_game_module() -> None:
    output = "The game module 'GRILLDISExample' could not be found. Please ensure that this module exists and that it is compiled."
    assert unreal_editor_log.classify_editor_failure(output) == "missing-game-module"


def test_classify_invalid_package_file_tag() -> None:
    output = "Package is unloadable: Invalid value for PACKAGE_FILE_TAG at start of file."
    assert unreal_editor_log.classify_editor_failure(output) == "invalid-package-file-tag"


def test_summarize_editor_failure_includes_note_and_excerpt(tmp_path: Path) -> None:
    log_path = tmp_path / "editor.log"
    log_path.write_text(
        "\n".join(
            [
                "LogPluginManager: Warning: Plugin 'GRILLDISForUnreal' is designed for build 5.0.0",
                "The game module 'GRILLDISExample' could not be found. Please ensure that this module exists and that it is compiled.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = unreal_editor_log.summarize_editor_failure(log_path)

    assert summary["failure_kind"] == "missing-game-module"
    assert "could not load its game module" in summary["detail"]
    assert len(summary["log_excerpt"]) == 2
