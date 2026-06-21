#!/usr/bin/env python3
"""Smoke-test locally staged Alpha5 release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv
import zipfile

from artifacts import RELEASE_ARTIFACTS_DIR, REPORTS_DIR


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_zips(artifact_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(artifact_dir.glob("*.zip")):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
        rows.append({"name": path.name, "kind": "zip", "status": "pass" if bad is None else "fail", "bad_entry": bad})
    return rows


def check_manifest(artifact_dir: Path) -> list[dict[str, object]]:
    manifest_path = artifact_dir / "RELEASE_MANIFEST.json"
    if not manifest_path.is_file():
        return [{"name": "RELEASE_MANIFEST.json", "kind": "manifest", "status": "fail", "reason": "missing"}]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for artifact in manifest.get("artifacts", []):
        path = artifact_dir / artifact["name"]
        ok = path.is_file() and sha256_file(path) == artifact["sha256"]
        rows.append({"name": artifact["name"], "kind": "checksum", "status": "pass" if ok else "fail"})
    return rows


def python_in_venv(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def check_wheel_install(artifact_dir: Path) -> list[dict[str, object]]:
    wheels = sorted(artifact_dir.glob("fastdis-*.whl"))
    if not wheels:
        return [{"name": "fastdis wheel", "kind": "wheel-install", "status": "fail", "reason": "missing"}]
    wheel = wheels[-1]
    with tempfile.TemporaryDirectory(prefix="fastdis_alpha5_wheel_") as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        py = python_in_venv(venv_dir)
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        install = subprocess.run([str(py), "-m", "pip", "install", "--no-index", "--force-reinstall", str(wheel)], text=True, env=env)
        if install.returncode != 0:
            return [{"name": wheel.name, "kind": "wheel-install", "status": "fail", "returncode": install.returncode}]
        probe = subprocess.run([str(py), "-c", "import fastdis; print(fastdis.__version__)"], text=True, env=env)
        return [{"name": wheel.name, "kind": "wheel-install", "status": "pass" if probe.returncode == 0 else "fail", "returncode": probe.returncode}]


def render_markdown(report: dict[str, object]) -> str:
    lines = ["# Alpha5 Release Artifact Smoke Report", "", f"- status: `{report['overall_status']}`", ""]
    for row in report["checks"]:
        detail = row.get("reason") or row.get("bad_entry") or ""
        lines.append(f"- `{row['status']}` {row['kind']} `{row['name']}` {detail}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=RELEASE_ARTIFACTS_DIR / "alpha5")
    parser.add_argument("--out-dir", type=Path, default=REPORTS_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = check_zips(args.artifact_dir) + check_manifest(args.artifact_dir) + check_wheel_install(args.artifact_dir)
    overall = "pass" if checks and all(row["status"] == "pass" for row in checks) else "fail"
    report = {
        "schema": "fastdis.alpha5_release_artifact_smoke.v1",
        "overall_status": overall,
        "artifact_dir": str(args.artifact_dir),
        "checks": checks,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "alpha5_release_artifact_smoke.json"
    md_path = args.out_dir / "alpha5_release_artifact_smoke.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
