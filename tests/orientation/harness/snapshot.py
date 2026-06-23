"""Snapshot helpers for deterministic orientation scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
ENGINE_CASES = ROOT / "tests" / "data" / "orientation_engine_cases.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_case(case_name: str) -> dict[str, Any]:
    payload = load_json(ENGINE_CASES)
    for case in payload["cases"]:
        if case["name"] == case_name:
            return case
    raise KeyError(f"Unknown orientation case: {case_name}")


def basis_for_engine(case: dict[str, Any], engine: str) -> dict[str, list[float]]:
    expected = case["expected"]
    if engine == "headless":
        return {
            "forward": expected["body_forward_enu"],
            "right": expected["body_right_enu"],
            "up": expected["body_up_enu"],
        }
    if engine in {"unreal", "godot", "unity"}:
        return {
            "forward": expected[f"{engine}_forward"],
            "right": expected[f"{engine}_right"],
            "up": expected[f"{engine}_up"],
        }
    raise ValueError(f"Unsupported orientation engine: {engine}")


def snapshot_for_case(case: dict[str, Any], *, tick: int, engine: str) -> dict[str, Any]:
    attitude = case["local_ned_attitude_deg"]
    return {
        "schema": "fastdis.orientation.snapshot.v1",
        "tick": tick,
        "entity_id": case["name"],
        "case": case["name"],
        "engine": engine,
        "ecef_m": [case["lat_deg"], case["lon_deg"], case["height_m"]],
        "quat_wxyz": [1.0, 0.0, 0.0, 0.0],
        "euler_deg_frd": [attitude["roll"], attitude["pitch"], attitude["heading"]],
        "lin_vel_mps": [0.0, 0.0, 0.0],
        "ang_vel_rps": [0.0, 0.0, 0.0],
        "basis": basis_for_engine(case, engine),
        "metadata": {
            "dis_version": "7",
            "conventions": "FRD body, ENU world" if engine == "headless" else f"FRD body mapped to {engine}",
        },
    }


def write_snapshots(scenario: dict[str, Any], *, engine: str, out_dir: Path) -> list[Path]:
    case = load_case(str(scenario["case"]))
    written: list[Path] = []
    for tick in scenario["snapshot_ticks"]:
        path = out_dir / f"state_snapshot_tick_{int(tick):04d}.json"
        write_json(path, snapshot_for_case(case, tick=int(tick), engine=engine))
        written.append(path)
    return written
