from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_export_report


def test_detect_library_prefers_unversioned_host_library(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    preferred = build / "libfastdis.dylib"
    preferred.write_text("", encoding="utf-8")
    (build / "libfastdis.0.12.0.dylib").write_text("", encoding="utf-8")

    assert run_export_report.detect_library(tmp_path) == preferred


def test_generate_report_writes_bundled_manifests(monkeypatch, tmp_path: Path) -> None:
    library = tmp_path / "libfastdis.dylib"
    library.write_text("", encoding="utf-8")
    out_dir = tmp_path / "reports"

    monkeypatch.setattr(run_export_report.check_exports, "expected_symbols_from_header", lambda header: ["fastdis_a", "fastdis_b"])
    monkeypatch.setattr(run_export_report.check_exports, "exported_symbols", lambda path: {"fastdis_a", "fastdis_b"})

    summary, expected_manifest, exported_manifest = run_export_report.generate_report(library, out_dir)

    assert summary["status"] == "passed"
    assert expected_manifest.read_text(encoding="utf-8").splitlines() == ["fastdis_a", "fastdis_b"]
    assert exported_manifest.read_text(encoding="utf-8").splitlines() == ["fastdis_a", "fastdis_b"]

    report_json = out_dir / "export_check_report.json"
    report_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["expected_manifest"].endswith("expected_exports.txt")
    assert payload["exported_manifest"].endswith("exported_symbols_macos.txt")
