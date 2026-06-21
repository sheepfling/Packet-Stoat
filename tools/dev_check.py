#!/usr/bin/env python3
"""Run the local Packet Stoat development verification lanes.

This is the junior-friendly "is the repo green?" entry point. It keeps the
default lane fast and deterministic, while making heavier checks explicit.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import venv

from artifacts import BENCHMARK_RESULTS_DIR, CMAKE_HOST, DIST_DIR, RELEASE_ARTIFACTS_DIR, REPORTS_DIR, TOOL_VENVS_DIR


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPORTS_DIR / "dev_check_report.json"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not pythonpath else f"{src}{os.pathsep}{pythonpath}"
    return env


def _run(label: str, cmd: list[str], *, required: bool = True) -> dict[str, object]:
    print(f"\n== {label} ==")
    print("+", " ".join(cmd))
    started = time.monotonic()
    completed = subprocess.run(cmd, cwd=ROOT, env=_env(), text=True)
    elapsed = round(time.monotonic() - started, 3)
    status = "pass" if completed.returncode == 0 else ("fail" if required else "warn")
    print(f"[{status}] {label} ({elapsed}s)")
    return {
        "label": label,
        "command": cmd,
        "required": required,
        "returncode": completed.returncode,
        "status": status,
        "elapsed_seconds": elapsed,
    }


def _ensure_twine_command() -> list[str] | None:
    if shutil.which("twine"):
        return [sys.executable, "-m", "twine"]
    try:
        import twine  # type: ignore  # noqa: F401

        return [sys.executable, "-m", "twine"]
    except Exception:
        pass
    venv_dir = TOOL_VENVS_DIR / "twine"
    py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.exists():
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    install = subprocess.run([str(py), "-m", "pip", "install", "--upgrade", "twine"], cwd=ROOT, text=True)
    if install.returncode != 0:
        return None
    return [str(py), "-m", "twine"]


def _write_report(results: list[dict[str, object]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "overall_status": "pass" if all(row["status"] != "fail" for row in results) else "fail",
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nreport: {REPORT_PATH}")


def _cleanup_duplicate_local_artifacts() -> None:
    """Remove known ignored iCloud duplicate outputs before deliverables reporting."""
    roots = [DIST_DIR, ROOT / "generated"]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("* 2*"), reverse=True):
            try:
                if path.is_dir():
                    path.rmdir()
                else:
                    path.unlink()
            except OSError:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="Run only import, CLI, generated, and unit tests")
    parser.add_argument("--native", action="store_true", help="Also build and run native CMake tests")
    parser.add_argument("--package", action="store_true", help="Also build/check Python sdist/wheel")
    parser.add_argument("--engine-doctors", action="store_true", help="Also run Unreal/Godot/Unity doctor checks")
    parser.add_argument("--unity-runtime", action="store_true", help="Also run Unity Editor batchmode package tests")
    parser.add_argument("--benchmarks", action="store_true", help="Also run native + Python ctypes benchmark report generation")
    parser.add_argument("--lattice", action="store_true", help="Also run the Lattice SDK gap report")
    parser.add_argument("--release-artifacts", action="store_true", help="Also stage and smoke-test local Alpha5 release artifacts")
    parser.add_argument("--release-ready", action="store_true", help="Run all credential-free Alpha5 release gates")
    parser.add_argument("--allow-credential-blockers", action="store_true", help="Treat known credential/license-gated checks as warnings")
    parser.add_argument("--all", action="store_true", help="Run all local non-destructive lanes")
    parser.add_argument("--pytest-args", nargs=argparse.REMAINDER, default=[], help="Extra args passed to pytest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    release_ready = bool(args.release_ready)
    run_all = bool(args.all or release_ready)
    quick = bool(args.quick)
    results: list[dict[str, object]] = []

    results.append(_run("python import", [sys.executable, "-c", "import fastdis; print(fastdis.HAS_C_ACCELERATOR)"]))
    results.append(_run("fastdis doctor", [sys.executable, "-m", "fastdis", "doctor"]))
    results.append(_run("generated bootstrap catalog", [sys.executable, "tools/generate_pdu_catalog.py"]))
    results.append(_run("generated bootstrap IR", [sys.executable, "tools/generate_fastdis_ir.py"]))
    results.append(_run("generated bootstrap message views", [sys.executable, "tools/generate_message_views.py"]))
    results.append(_run("generated bootstrap PDU coverage", [sys.executable, "tools/generate_pdu_coverage.py"]))
    results.append(_run("generated bootstrap typed PDU parsers", [sys.executable, "tools/generate_typed_pdu_parsers.py"]))
    results.append(_run("generated bootstrap semantic PDU parsers", [sys.executable, "tools/generate_semantic_pdu_parsers.py"]))
    results.append(_run("generated bootstrap PDU logging", [sys.executable, "tools/generate_pdu_log_catalog.py"]))
    results.append(_run("generated bootstrap dead-reckoning coverage", [sys.executable, "tools/generate_dead_reckoning_coverage.py"]))
    results.append(_run("generated bootstrap version translation", [sys.executable, "tools/generate_version_translation_manifest.py"]))
    results.append(_run("generated bootstrap endpoint mapping", [sys.executable, "tools/generate_endpoint_mapping_manifest.py"]))
    results.append(_run("generated bootstrap shallow fuzz", [sys.executable, "tools/generate_shallow_fuzz_corpus.py"]))
    results.append(_run("generated freshness", [sys.executable, "tools/check_generated_fresh.py"]))
    results.append(_run("logging coverage", [sys.executable, "-m", "fastdis.tools.logging_check"]))
    results.append(_run("Alpha5 integration matrix", [sys.executable, "tools/run_alpha5_integration_matrix.py"], required=False))
    results.append(_run("ruff", [sys.executable, "-m", "ruff", "check", "."]))
    results.append(_run("pyright", [sys.executable, "-m", "pyright"]))
    results.append(_run("pytest", [sys.executable, "-m", "pytest", *(args.pytest_args or [])]))

    if run_all or args.native:
        results.append(_run("native build", [sys.executable, "tools/build_native.py"]))
        results.append(_run("native ctest", ["ctest", "--test-dir", str(CMAKE_HOST), "--build-config", "Release", "--output-on-failure"]))

    if run_all or args.package:
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        results.append(_run("build package", [sys.executable, "-m", "build", "--outdir", str(DIST_DIR)]))
        twine_cmd = _ensure_twine_command()
        if twine_cmd is not None:
            artifacts = [str(path) for path in sorted(DIST_DIR.glob("*"))]
            results.append(_run("twine check", [*twine_cmd, "check", *artifacts]))
        elif release_ready:
            results.append(
                {
                    "label": "twine check",
                    "command": [sys.executable, "-m", "twine", "check", f"{DIST_DIR}/*"],
                    "required": True,
                    "returncode": 1,
                    "status": "fail",
                    "elapsed_seconds": 0.0,
                    "detail": "twine could not be installed into the local build/tool_venvs/twine environment",
                }
            )
            print("\n== twine check ==\n[fail] twine could not be installed into the local tool virtualenv")
        else:
            results.append(
                {
                    "label": "twine check",
                    "command": [sys.executable, "-m", "twine", "check", f"{DIST_DIR}/*"],
                    "required": False,
                    "returncode": 0,
                    "status": "skip",
                    "elapsed_seconds": 0.0,
                    "detail": "twine not installed",
                }
            )
            print("\n== twine check ==\n[skip] twine not installed")

    if run_all or args.engine_doctors:
        results.append(_run("Unreal doctor", [sys.executable, "tools/unreal_workflow.py", "doctor", "--engine-version", "5.8"], required=False))
        results.append(_run("Godot doctor", [sys.executable, "tools/godot_workflow.py", "doctor"], required=False))
        results.append(_run("Unity doctor", [sys.executable, "tools/unity_workflow.py", "doctor", "--unity-version", "6000.5"], required=False))

    if release_ready or args.unity_runtime:
        results.append(
            _run(
                "Unity runtime verification",
                [sys.executable, "tools/unity_workflow.py", "runtime-verify", "--unity-version", "6000.5"],
                required=not args.allow_credential_blockers,
            )
        )

    if release_ready or args.benchmarks:
        results.append(
            _run(
                "benchmark report",
                [
                    sys.executable,
                    "tools/run_benchmarks.py",
                    "--format",
                    "json",
                    "--out-dir",
                    str(BENCHMARK_RESULTS_DIR / "alpha5"),
                    "--native-packets",
                    "1000000",
                    "--native-rounds",
                    "5",
                    "--ctypes-packets",
                    "50000",
                    "--ctypes-repeats",
                    "5",
                ],
            )
        )

    if run_all or args.lattice:
        results.append(_run("Lattice SDK gap report", [sys.executable, "tools/run_alpha4_1_sdk_gap_report.py"]))

    if release_ready or args.release_artifacts:
        results.append(_run("stage Alpha5 release artifacts", [sys.executable, "tools/build_alpha5_release_artifacts.py", "--clean"]))
        results.append(_run("smoke Alpha5 release artifacts", [sys.executable, "tools/smoke_alpha5_release_artifacts.py", "--artifact-dir", str(RELEASE_ARTIFACTS_DIR / "alpha5")]))

    _cleanup_duplicate_local_artifacts()
    results.append(_run("deliverables report", [sys.executable, "tools/list_deliverables.py"], required=False))

    _write_report(results)
    failures = [row for row in results if row["status"] == "fail"]
    if failures:
        print("\nfailed lanes:")
        for row in failures:
            print(f"  - {row['label']}")
        return 1
    if quick:
        print("\nquick check passed")
    else:
        print("\nlocal check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
