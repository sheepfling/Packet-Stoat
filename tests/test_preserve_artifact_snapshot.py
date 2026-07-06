from __future__ import annotations

import json
from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import preserve_artifact_snapshot


def test_preserve_files_copies_artifacts_with_manifest(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    log = tmp_path / "build.log"
    binary = tmp_path / "libGodot3DTiles.linux.template_release.x86_64.so"
    report.write_text("{}", encoding="utf-8")
    log.write_text("compile output\n", encoding="utf-8")
    binary.write_bytes(b"native-payload")

    snapshot_dir = tmp_path / "preserved" / "lane" / "stamp_label"
    manifest = preserve_artifact_snapshot.preserve_files(
        [report, log, binary],
        out_dir=snapshot_dir,
        lane="cesium-godot-linux-docker",
        label="green",
    )

    manifest_path = snapshot_dir / "SNAPSHOT_MANIFEST.json"
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["artifact_count"] == 3
    assert loaded["schema"] == "packet_stoat.preserved_artifact_snapshot.v2"
    assert all(row["sha256"] for row in loaded["artifacts"])
    assert all(row["storage"] in {"hardlink", "copy"} for row in loaded["artifacts"])
    assert len(list((snapshot_dir / "files").rglob("*.*"))) == 3


def test_collect_paths_from_payload_finds_nested_artifact_paths(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.so"
    artifact.write_text("payload", encoding="utf-8")
    payload = {
        "report_json": str(tmp_path / "report.json"),
        "nested": {
            "artifact_paths": [str(artifact)],
            "not_a_path": "plain text",
        },
    }

    paths = preserve_artifact_snapshot.collect_paths_from_payload(payload)

    assert artifact.resolve() in paths


def test_preserve_files_reuses_shared_blob_for_duplicate_external_payload(tmp_path: Path) -> None:
    external = tmp_path / "external-source" / "Linux_Unreal_Engine_5.8.0.zip"
    external.parent.mkdir(parents=True)
    external.write_bytes(b"same-engine-archive")

    out_root = tmp_path / "preserved"
    first_dir = out_root / "lane" / "first"
    second_dir = out_root / "lane" / "second"

    first = preserve_artifact_snapshot.preserve_files(
        [external],
        out_dir=first_dir,
        lane="cesium-unreal-linux-docker",
        label="first",
        out_root=out_root,
    )
    second = preserve_artifact_snapshot.preserve_files(
        [external],
        out_dir=second_dir,
        lane="cesium-unreal-linux-docker",
        label="second",
        out_root=out_root,
    )

    first_row = first["artifacts"][0]
    second_row = second["artifacts"][0]
    assert first_row["content_store_path"] == second_row["content_store_path"]
    shared_payloads = list((out_root / "_shared_blobs").rglob("payload.zip"))
    assert len(shared_payloads) == 1
