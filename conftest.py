from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from workflow_versions import DEFAULT_UNREAL_ENGINE_VERSION, DEFAULT_UNITY_EDITOR_VERSION, DEFAULT_UNITY_VERSION_PREFIX  # noqa: E402


TEST_UNREAL_ENGINE_VERSION = DEFAULT_UNREAL_ENGINE_VERSION
TEST_UNITY_EDITOR_VERSION = DEFAULT_UNITY_EDITOR_VERSION
TEST_UNITY_VERSION_PREFIX = DEFAULT_UNITY_VERSION_PREFIX
