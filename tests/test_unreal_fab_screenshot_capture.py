from __future__ import annotations

from pathlib import Path
import struct
import subprocess
import sys
import zlib


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import capture_unreal_fab_screenshots


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def make_minimal_png(path: Path, width: int = 2, height: int = 1) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def test_unreal_fab_screenshot_capture_scripts_exist_and_target_expected_files() -> None:
    runner = read(ROOT / "tools" / "capture_unreal_fab_screenshots.py")
    script = read(ROOT / "tools" / "unreal" / "capture_fab_demo_screenshots.py")

    assert "ExecutePythonScript" in runner
    assert "RenderOffscreen" in runner
    assert "CaptureFastDisFabScreenshots.log" in runner
    assert "live_udp_status" in runner
    assert "entity_spawn" in runner
    assert "pdu_event_marker" in runner
    assert "setup_view" in runner
    assert [path.name for path in capture_unreal_fab_screenshots.SCREENSHOTS] == [
        "live_udp_status.png",
        "entity_spawn.png",
        "pdu_event_marker.png",
        "setup_view.png",
    ]
    assert "/FastDis/Examples/FastDis_Demo" in script
    assert "capture_example_scene_png" in script
    assert "FASTDIS_FAB_SCREENSHOT" in script
    assert "TextRenderActor" in script


def test_unreal_fab_screenshot_capture_dry_run_command_shape() -> None:
    completed = subprocess.run(
        [
            "python3",
            "tools/capture_unreal_fab_screenshots.py",
            "--dry-run",
            "--engine-version",
            "5.8",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )

    output = completed.stdout
    assert "FastDisOrientationVerification.uproject" in output
    assert "-ExecutePythonScript=" in output
    assert "tools/unreal/capture_fab_demo_screenshots.py" in output
    assert "-RenderOffscreen" in output
    assert "CaptureFastDisFabScreenshots.log" in output


def test_unreal_fab_screenshot_capture_validates_png_dimensions(tmp_path: Path) -> None:
    image = tmp_path / "sample.png"
    make_minimal_png(image, width=3, height=2)

    assert capture_unreal_fab_screenshots.png_dimensions(image) == (3, 2)
