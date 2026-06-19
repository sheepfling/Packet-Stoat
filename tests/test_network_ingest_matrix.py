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
            "report": {"surface": "python"},
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
            "report": {"surface": "c"},
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
            "report": {"surface": "cpp"},
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
    routes = {(row["surface"], row["mode"]): row for row in payload["routes"]}
    assert routes[("python", "localhost_udp")]["status"] == "passed"
    assert routes[("c", "localhost_udp")]["status"] == "passed"
    assert routes[("cpp", "localhost_udp")]["status"] == "passed"
    assert routes[("godot", "live_udp")]["status"] == "passed"
    assert routes[("unreal", "live_udp")]["status"] == "passed"
