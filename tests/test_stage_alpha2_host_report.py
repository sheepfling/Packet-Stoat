from __future__ import annotations

import json
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import stage_alpha2_host_report


def write_source_report_set(base: Path) -> None:
    for name in stage_alpha2_host_report.REQUIRED_FILES:
        suffix = Path(name).suffix
        if suffix == ".json":
            payload = {"name": name, "ok": True}
            (base / name).write_text(json.dumps(payload), encoding="utf-8")
        else:
            (base / name).write_text(f"{name}\n", encoding="utf-8")


def test_stage_report_set_copies_required_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    write_source_report_set(source)

    stage_alpha2_host_report.stage_report_set(source, dest, overwrite=False)

    for name in stage_alpha2_host_report.REQUIRED_FILES:
        assert (dest / name).exists()


def test_main_writes_manifest_files(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    write_source_report_set(source)
    monkeypatch.setattr(
        stage_alpha2_host_report,
        "parse_args",
        lambda: stage_alpha2_host_report.argparse.Namespace(
            source_dir=str(source),
            dest_root=str(tmp_path / "hosts"),
            host_label="PB-Air Alpha2",
            overwrite=False,
        ),
    )
    monkeypatch.setattr(stage_alpha2_host_report.load_local_env, "load", lambda: None)
    monkeypatch.setattr(stage_alpha2_host_report.platform, "node", lambda: "pb-air")
    monkeypatch.setattr(stage_alpha2_host_report.platform, "platform", lambda: "macOS-15-arm64")
    monkeypatch.setattr(stage_alpha2_host_report.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(stage_alpha2_host_report.platform, "release", lambda: "24.5.0")
    monkeypatch.setattr(stage_alpha2_host_report.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(stage_alpha2_host_report.platform, "python_version", lambda: "3.12.9")

    rc = stage_alpha2_host_report.main()

    assert rc == 0
    dest = tmp_path / "hosts" / "pb-air-alpha2"
    manifest = json.loads((dest / "host_report_manifest.json").read_text(encoding="utf-8"))
    assert manifest["host_label"] == "pb-air-alpha2"
    assert manifest["platform"] == "macOS-15-arm64"
    assert len(manifest["host_fingerprint"]) == 64
    assert len(manifest["report_digest_sha256"]) == 64
    markdown = (dest / "host_report_manifest.md").read_text(encoding="utf-8")
    assert "# Alpha 2 Host Report Manifest" in markdown
    assert "- host_label: `pb-air-alpha2`" in markdown
    assert "- host_fingerprint: `" in markdown
