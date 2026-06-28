from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_network_ingest_matrix


def test_main_writes_matrix_with_python_and_cpp_routes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_python_udp_route",
        lambda **kwargs: {
            "surface": "python",
            "mode": "localhost_udp",
            "status": "passed",
            "scenario": kwargs["scenario"],
            "report": {"surface": "python"},
            "truth": {"schema": "fastdis.network_truth.v1", "packet_count": 24},
            "send_command": ["python"],
            "recv_command": ["recv"],
            "send_returncode": 0,
            "recv_returncode": 0,
            "send_output": "",
            "recv_output": "",
            "errors": [],
        },
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_c_udp_route",
        lambda **kwargs: {
            "surface": "c",
            "mode": "localhost_udp",
            "status": "passed",
            "scenario": kwargs["scenario"],
            "report": {"surface": "c"},
            "truth": {"schema": "fastdis.network_truth.v1", "packet_count": 24},
            "send_command": ["python"],
            "recv_command": ["c"],
            "send_returncode": 0,
            "recv_returncode": 0,
            "send_output": "",
            "recv_output": "",
            "errors": [],
        },
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_cpp_udp_route",
        lambda **kwargs: {
            "surface": "cpp",
            "mode": "localhost_udp",
            "status": "passed",
            "scenario": kwargs["scenario"],
            "report": {"surface": "cpp"},
            "truth": {"schema": "fastdis.network_truth.v1", "packet_count": 24},
            "send_command": ["python"],
            "recv_command": ["cpp"],
            "send_returncode": 0,
            "recv_returncode": 0,
            "send_output": "",
            "recv_output": "",
            "errors": [],
        },
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_godot_live_udp_route",
        lambda **kwargs: {
            "surface": "godot",
            "mode": "live_udp",
            "scenario": kwargs["scenario"],
            "status": "passed",
            "notes": "godot smoke",
            "report": {"surface": "godot"},
            "recv_command": ["godot"],
            "recv_returncode": 0,
            "recv_output": "",
            "errors": [],
        },
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_unreal_live_udp_route",
        lambda **kwargs: {
            "surface": "unreal",
            "mode": "live_udp",
            "scenario": run_network_ingest_matrix.CORE_SCENARIO_NAME,
            "status": "passed",
            "notes": "unreal smoke",
            "report": {"surface": "unreal"},
            "recv_command": ["unreal"],
            "recv_returncode": 0,
            "recv_output": "",
            "errors": [],
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_network_ingest_matrix.py", "--out-dir", str(tmp_path)])
    rc = run_network_ingest_matrix.main()
    assert rc == 0
    payload = json.loads((tmp_path / "network_ingest_matrix.json").read_text(encoding="utf-8"))
    routes = {(row["surface"], row["mode"], row.get("scenario")): row for row in payload["routes"]}
    assert routes[("python", "localhost_udp", "entity_state_1x10hz")]["status"] == "passed"
    assert routes[("python", "localhost_udp", "entity_state_100x30hz")]["status"] == "passed"
    assert routes[("python", "localhost_udp", "entity_state_1000x60hz")]["status"] == "passed"
    assert routes[("c", "localhost_udp", "entity_state_1x10hz")]["status"] == "passed"
    assert routes[("c", "localhost_udp", "entity_state_100x30hz")]["status"] == "passed"
    assert routes[("c", "localhost_udp", "entity_state_1000x60hz")]["status"] == "passed"
    assert routes[("cpp", "localhost_udp", "entity_state_1x10hz")]["status"] == "passed"
    assert routes[("cpp", "localhost_udp", "entity_state_100x30hz")]["status"] == "passed"
    assert routes[("cpp", "localhost_udp", "entity_state_1000x60hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_1x10hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_100x30hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_1000x60hz")]["status"] == "passed"
    assert routes[("unreal", "live_udp", run_network_ingest_matrix.CORE_SCENARIO_NAME)]["status"] == "passed"
    assert Path(routes[("python", "localhost_udp", "entity_state_1x10hz")]["truth_file"]).is_file()
    assert json.loads(Path(routes[("python", "localhost_udp", "entity_state_1x10hz")]["truth_file"]).read_text(encoding="utf-8"))["packet_count"] == 24


def test_main_core_only_keeps_godot_and_skips_unreal_routes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_python_udp_route",
        lambda **kwargs: {"surface": "python", "mode": "localhost_udp", "status": "passed", "scenario": kwargs["scenario"], "report": {"surface": "python"}, "errors": [], "notes": "python", "elapsed_seconds": 0.1},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_c_udp_route",
        lambda **kwargs: {"surface": "c", "mode": "localhost_udp", "scenario": kwargs["scenario"], "status": "pending", "notes": "c missing"},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_cpp_udp_route",
        lambda **kwargs: {"surface": "cpp", "mode": "localhost_udp", "scenario": kwargs["scenario"], "status": "passed", "report": {"surface": "cpp"}, "errors": [], "notes": "cpp", "elapsed_seconds": 0.2},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_godot_live_udp_route",
        lambda **kwargs: {"surface": "godot", "mode": "live_udp", "scenario": kwargs["scenario"], "status": "passed", "report": {"surface": "godot"}, "errors": [], "notes": "godot", "elapsed_seconds": 0.3},
    )
    monkeypatch.setattr(sys, "argv", ["run_network_ingest_matrix.py", "--out-dir", str(tmp_path), "--core-only", "--if-available"])
    rc = run_network_ingest_matrix.main()
    assert rc == 0
    payload = json.loads((tmp_path / "network_ingest_matrix.json").read_text(encoding="utf-8"))
    routes = {(row["surface"], row["mode"], row.get("scenario")): row for row in payload["routes"]}
    assert ("unreal", "live_udp", run_network_ingest_matrix.CORE_SCENARIO_NAME) not in routes
    assert routes[("godot", "live_udp", "entity_state_1x10hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_100x30hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_1000x60hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "filter_reject_90pct")]["status"] == "passed"
    assert routes[("c", "localhost_udp", "entity_state_1x10hz")]["status"] == "pending"
    assert routes[("c", "localhost_udp", "entity_state_100x30hz")]["status"] == "pending"
    assert routes[("c", "localhost_udp", "entity_state_1000x60hz")]["status"] == "pending"


def test_main_if_available_allows_pending_engine_routes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_python_udp_route",
        lambda **kwargs: {"surface": "python", "mode": "localhost_udp", "status": "passed", "scenario": kwargs["scenario"], "report": {"surface": "python"}, "errors": [], "notes": "python", "elapsed_seconds": 0.1},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_c_udp_route",
        lambda **kwargs: {"surface": "c", "mode": "localhost_udp", "status": "passed", "scenario": kwargs["scenario"], "report": {"surface": "c"}, "errors": [], "notes": "c", "elapsed_seconds": 0.1},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_cpp_udp_route",
        lambda **kwargs: {"surface": "cpp", "mode": "localhost_udp", "status": "passed", "scenario": kwargs["scenario"], "report": {"surface": "cpp"}, "errors": [], "notes": "cpp", "elapsed_seconds": 0.1},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_godot_live_udp_route",
        lambda **kwargs: {"surface": "godot", "mode": "live_udp", "status": "passed", "scenario": kwargs["scenario"], "report": {"surface": "godot"}, "errors": [], "notes": "godot", "elapsed_seconds": 0.2},
    )
    monkeypatch.setattr(
        run_network_ingest_matrix,
        "run_unreal_live_udp_route",
        lambda **kwargs: {
            "surface": "unreal",
            "mode": "live_udp",
            "scenario": run_network_ingest_matrix.CORE_SCENARIO_NAME,
            "scenario_suite": run_network_ingest_matrix.CORE_SCENARIO_SUITE,
            "status": "pending",
            "notes": "unreal host pending",
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_network_ingest_matrix.py", "--out-dir", str(tmp_path), "--if-available"])
    rc = run_network_ingest_matrix.main()
    assert rc == 0
    payload = json.loads((tmp_path / "network_ingest_matrix.json").read_text(encoding="utf-8"))
    routes = {(row["surface"], row["mode"], row.get("scenario")): row for row in payload["routes"]}
    assert routes[("godot", "live_udp", "entity_state_1x10hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_100x30hz")]["status"] == "passed"
    assert routes[("godot", "live_udp", "entity_state_1000x60hz")]["status"] == "passed"
    assert routes[("unreal", "live_udp", run_network_ingest_matrix.CORE_SCENARIO_NAME)]["status"] == "pending"
    assert routes[("unreal", "live_udp", run_network_ingest_matrix.CORE_SCENARIO_NAME)]["scenario"] == run_network_ingest_matrix.CORE_SCENARIO_NAME
    assert routes[("unreal", "live_udp", run_network_ingest_matrix.CORE_SCENARIO_NAME)]["scenario_suite"] == run_network_ingest_matrix.CORE_SCENARIO_SUITE
