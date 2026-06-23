from __future__ import annotations

import json
from pathlib import Path

from fastdis.tools import simtest


def _write_meta(path: Path, *, x: float = 1.0) -> None:
    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "id": "100/1/42",
                        "type": "airtrack",
                        "position": {"x": x, "y": 2.0, "z": 3.0},
                        "velocity": [10.0, 0.0, 0.0],
                        "orientation": [0.0, 0.0, 0.0, 1.0],
                    }
                ],
                "camera": {"name": "main"},
            }
        ),
        encoding="utf-8",
    )


def test_simtest_compare_passes_metadata_within_tolerance(tmp_path: Path) -> None:
    run = tmp_path / "run"
    baseline = tmp_path / "baseline"
    run.mkdir()
    baseline.mkdir()
    _write_meta(run / "meta_000330.json", x=1.001)
    _write_meta(baseline / "meta_000330.json", x=1.0)

    report = simtest.compare(run, baseline, None, tmp_path / "report")

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "report.md").is_file()


def test_simtest_compare_fails_metadata_outside_tolerance(tmp_path: Path) -> None:
    run = tmp_path / "run"
    baseline = tmp_path / "baseline"
    run.mkdir()
    baseline.mkdir()
    _write_meta(run / "meta_000330.json", x=2.0)
    _write_meta(baseline / "meta_000330.json", x=1.0)

    report = simtest.compare(run, baseline, None, None)

    assert report["status"] == "fail"
    assert any(check["name"].endswith("position_m") for check in report["checks"] if check["status"] == "fail")


def test_simtest_bless_copies_run_to_baseline(tmp_path: Path) -> None:
    run = tmp_path / "run"
    baseline = tmp_path / "baseline"
    run.mkdir()
    _write_meta(run / "meta_000330.json")

    report = simtest.bless(run, baseline)

    assert report["status"] == "pass"
    assert (baseline / "meta_000330.json").is_file()


def test_simtest_inspect_lists_metadata_and_crops(tmp_path: Path) -> None:
    root = tmp_path / "run"
    crops = root / "crops"
    crops.mkdir(parents=True)
    _write_meta(root / "meta_000330.json")
    (crops / "reticle_000330.png").write_bytes(b"placeholder")

    report = simtest.inspect(root)

    assert report["meta_count"] == 1
    assert report["meta_stamps"] == ["000330"]
    assert report["crop_count"] == 1
