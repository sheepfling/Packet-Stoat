from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import stage_alpha3_host_report
import host_profile


def test_stage_report_set_copies_required_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name in stage_alpha3_host_report.REQUIRED_FILES:
        (source / name).write_text(name, encoding="utf-8")

    dest = tmp_path / "dest"
    stage_alpha3_host_report.stage_report_set(source, dest, overwrite=False)

    for name in stage_alpha3_host_report.REQUIRED_FILES:
        assert (dest / name).read_text(encoding="utf-8") == name


def test_collect_manifest_lists_required_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name in stage_alpha3_host_report.REQUIRED_FILES:
        (source / name).write_text(name, encoding="utf-8")

    profile = host_profile.resolve_host_profile(host_label_override="sample-host", env={})
    manifest = stage_alpha3_host_report.collect_manifest(source, profile)
    assert manifest["host_label"] == "sample-host"
    assert manifest["required_files"] == list(stage_alpha3_host_report.REQUIRED_FILES)
    assert manifest["report_digest_sha256"]


def test_main_writes_manifest(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name in stage_alpha3_host_report.REQUIRED_FILES:
        (source / name).write_text(name, encoding="utf-8")

    dest_root = tmp_path / "dest"

    monkeypatch.setattr(
        stage_alpha3_host_report,
        "parse_args",
        lambda: stage_alpha3_host_report.argparse.Namespace(
            source_dir=str(source),
            dest_root=str(dest_root),
            host_label="demo-host",
            hostname=None,
            host_system=None,
            host_release=None,
            host_machine=None,
            host_python_version=None,
            host_fingerprint_seed=None,
            overwrite=False,
        ),
    )
    monkeypatch.setattr(stage_alpha3_host_report.load_local_env, "load", lambda: None)

    rc = stage_alpha3_host_report.main()
    assert rc == 0

    host_dir = dest_root / "demo-host"
    manifest_path = host_dir / stage_alpha3_host_report.HOST_MANIFEST
    assert manifest_path.is_file()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["host_label"] == "demo-host"
