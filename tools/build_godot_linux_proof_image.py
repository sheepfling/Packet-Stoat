#!/usr/bin/env python3
"""Build the Linux Docker image used by the Godot vendor-plugin proof lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCKERFILE = ROOT / "tools" / "docker" / "godot-linux-proof.Dockerfile"
DEFAULT_IMAGE = "fastdis-godot-linux-proof:godot4.7-ubuntu24.04"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--dockerfile", type=Path, default=DEFAULT_DOCKERFILE)
    parser.add_argument("--godot-version", default="4.7")
    parser.add_argument("--godot-channel", default="stable")
    parser.add_argument("--godot-download-url", default="")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
        "docker",
        "build",
        "--platform",
        args.platform,
        "-f",
        str(args.dockerfile),
        "-t",
        args.image,
        "--build-arg",
        f"GODOT_VERSION={args.godot_version}",
        "--build-arg",
        f"GODOT_CHANNEL={args.godot_channel}",
    ]
    if args.godot_download_url:
        command.extend(["--build-arg", f"GODOT_DOWNLOAD_URL={args.godot_download_url}"])
    command.append(str(ROOT))
    return command


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    command = build_command(args)
    payload = {
        "schema": "packet_stoat.godot_linux_proof_image_build.v1",
        "image": args.image,
        "dockerfile": str(args.dockerfile.resolve()),
        "godot_version": args.godot_version,
        "godot_channel": args.godot_channel,
        "platform": args.platform,
        "command": command,
        "command_text": " ".join(shlex.quote(part) for part in command),
        "status": "dry-run" if args.dry_run else "pending",
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    result = subprocess.run(command)
    payload["returncode"] = result.returncode
    payload["status"] = "pass" if result.returncode == 0 else "fail"
    print(json.dumps(payload, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
