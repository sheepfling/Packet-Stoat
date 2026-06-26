from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import export_competitor_benchmark_handoff


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_competitor_handoff_workbench_passes_for_exported_archive(tmp_path: Path) -> None:
    export_path = tmp_path / "out" / f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}.zip"
    export_competitor_benchmark_handoff.export_archive(export_path)

    module = _load_module("check_competitor_handoff_workbench", ROOT / "tools" / "check_competitor_handoff_workbench.py")
    bundle_root, tmp_dir = module.load_bundle_root(export_path)
    try:
        report = module.build_report(bundle_root)
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()

    assert report["schema"] == "fastdis.competitor_handoff_workbench_check.v1"
    assert report["status"] == "pass"
    assert report["summary"]["missing_file_count"] == 0
    assert report["summary"]["readme_present"] is True
    assert report["summary"]["manifest_present"] is True
    assert report["summary"]["manifest_valid"] is True
    assert report["summary"]["checksum_mismatch_count"] == 0
    assert report["summary"]["bundle_kind"] == "archive_bundle"
    assert report["summary"]["self_describing_bundle"] is True


def test_check_competitor_handoff_workbench_cli_writes_outputs(tmp_path: Path) -> None:
    export_path = tmp_path / "out" / f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}.zip"
    export_competitor_benchmark_handoff.export_archive(export_path)
    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "check_competitor_handoff_workbench.py"),
            str(export_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
            "--fail-missing",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.competitor_handoff_workbench_check.v1"
    assert payload["status"] == "pass"
    assert "Competitor Handoff Workbench Check" in md_out.read_text(encoding="utf-8")


def test_check_competitor_handoff_workbench_fails_when_manifest_entry_is_missing(tmp_path: Path) -> None:
    export_path = tmp_path / "out" / f"fastdis-competitor-benchmark-handoff-{export_competitor_benchmark_handoff.package_stamp()}.zip"
    export_competitor_benchmark_handoff.export_archive(export_path)
    extracted = tmp_path / "bundle"
    with zipfile.ZipFile(export_path) as archive:
        archive.extractall(extracted)
    bundle_root = next(child for child in extracted.iterdir() if child.is_dir())
    missing_target = bundle_root / "tools" / "check_competitor_handoff_workbench.py"
    missing_target.unlink()

    module = _load_module("check_competitor_handoff_workbench_missing", ROOT / "tools" / "check_competitor_handoff_workbench.py")
    report = module.build_report(bundle_root)

    assert report["status"] == "fail"
    assert report["summary"]["manifest_present"] is True
    assert report["summary"]["missing_file_count"] >= 1
    assert report["summary"]["bundle_kind"] == "archive_bundle"
    missing_rows = [row for row in report["rows"] if row["path"] == "tools/check_competitor_handoff_workbench.py"]
    assert len(missing_rows) == 1
    assert missing_rows[0]["exists"] is False
    assert missing_rows[0]["checksum_match"] is False
