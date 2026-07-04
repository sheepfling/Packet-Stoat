from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_godot_linux_proof_image


def test_build_command_pins_godot_version_and_image() -> None:
    args = build_godot_linux_proof_image.parse_args(
        [
            "--image",
            "godot-proof:test",
            "--godot-version",
            "4.7",
            "--godot-channel",
            "stable",
            "--dry-run",
        ]
    )

    command = build_godot_linux_proof_image.build_command(args)

    assert command[:3] == ["docker", "build", "--platform"]
    assert "godot-proof:test" in command
    assert "GODOT_VERSION=4.7" in command
    assert "GODOT_CHANNEL=stable" in command
    assert str(build_godot_linux_proof_image.DEFAULT_DOCKERFILE) in command
