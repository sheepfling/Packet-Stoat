from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_native_canonical_benchmark as native_canonical


def test_build_canonical_row_marks_truth_and_runtime_metrics(tmp_path: Path) -> None:
    row = native_canonical.build_canonical_row(
        {
            "packets_received": 24,
            "packets_parsed": 24,
            "entity_state": 24,
            "malformed": 0,
            "elapsed_seconds": 0.004,
            "latest_entities": [
                {
                    "site": 100,
                    "application": 1,
                    "entity": 1,
                    "force_id": 1,
                    "location_ecef_m": [1.0, 2.0, 3.0],
                    "orientation_dis_rad": [0.1, 0.2, 0.3],
                }
            ],
            "unique_entities": 1,
        },
        {
            "unique_entities": 1,
            "latest_entities": [
                {
                    "site": 100,
                    "application": 1,
                    "entity": 1,
                    "force_id": 1,
                    "location_ecef_m": [1.0, 2.0, 3.0],
                    "orientation_dis_rad": [0.1, 0.2, 0.3],
                }
            ],
        },
        [],
        tmp_path / "capture.fastdispkt",
        scenario="entity_state_1x10hz",
    )

    assert row["scenario"] == "entity_state_1x10hz"
    assert row["metrics"]["runtime_elapsed_seconds"] == 0.004
    assert row["metrics"]["packets_per_sec"] == 6000.0
    assert row["truth"]["final_truth_match"] is True
    assert row["truth"]["network_ingest_mode"] == "replay_native_entity_table"
    assert any("replay_file=" in note for note in row["metrics"]["notes"])


def test_main_if_available_writes_unavailable_sidecar(monkeypatch, tmp_path: Path) -> None:
    out_path = tmp_path / "native_canonical.json"

    monkeypatch.setattr(native_canonical, "run_lane", lambda args: (_ for _ in ()).throw(FileNotFoundError("missing exe")))

    rc = native_canonical.main(["--json-out", str(out_path), "--if-available"])

    assert rc == 0
    payload = native_canonical.json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["status"] == "unavailable"
    assert payload["surface"] == "native"
    assert payload["scenario"] == "entity_state_1x10hz"


def test_replay_path_for_scenario_rewrites_default_suffix(tmp_path: Path) -> None:
    base = tmp_path / "native_canonical_entity_state_1x10hz.fastdispkt"
    path = native_canonical.replay_path_for_scenario(base, "entity_state_100x30hz")
    assert path.name == "native_canonical_entity_state_100x30hz.fastdispkt"
