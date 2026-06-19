from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_network_send_matrix


def test_main_writes_matrix_with_python_c_cpp_routes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_network_send_matrix,
        "run_python_send_route",
        lambda **kwargs: {
            "surface": "python",
            "mode": "localhost_udp_send",
            "status": "passed",
            "recv_report": {"surface": "send-matrix"},
            "send_command": ["python"],
            "recv_command": ["recv"],
        },
    )
    monkeypatch.setattr(
        run_network_send_matrix,
        "run_c_send_route",
        lambda **kwargs: {
            "surface": "c",
            "mode": "localhost_udp_send",
            "status": "passed",
            "recv_report": {"surface": "send-matrix"},
            "send_command": ["c"],
            "recv_command": ["recv"],
        },
    )
    monkeypatch.setattr(
        run_network_send_matrix,
        "run_cpp_send_route",
        lambda **kwargs: {
            "surface": "cpp",
            "mode": "localhost_udp_send",
            "status": "passed",
            "recv_report": {"surface": "send-matrix"},
            "send_command": ["cpp"],
            "recv_command": ["recv"],
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_network_send_matrix.py", "--out-dir", str(tmp_path)])
    rc = run_network_send_matrix.main()
    assert rc == 0
    payload = json.loads((tmp_path / "network_send_matrix.json").read_text(encoding="utf-8"))
    routes = {(row["surface"], row["mode"]): row for row in payload["routes"]}
    assert routes[("python", "localhost_udp_send")]["status"] == "passed"
    assert routes[("c", "localhost_udp_send")]["status"] == "passed"
    assert routes[("cpp", "localhost_udp_send")]["status"] == "passed"
