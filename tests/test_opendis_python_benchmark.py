from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summarize_comparison_computes_speedup() -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")

    comparison = module.summarize_comparison(
        {"packets_per_sec": 2000.0},
        {"packets_per_sec": 500.0},
    )

    assert comparison["fastdis_vs_open_dis_speedup"] == 4.0
    assert "Same-host Python-route comparison" in comparison["claim_boundary"]


def test_render_markdown_includes_scenarios() -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")

    report = {
        "fixture": {
            "path": "/tmp/EntityStatePdu.raw",
            "fixture_count": 3,
            "packets_per_round": 1000,
            "rounds": 5,
        },
        "oracle": {
            "root": "/tmp/open-dis-python",
        },
        "scenarios": [
            {
                "scenario": "entity_state_fixture_header_scan",
                "comparison": {
                    "fastdis_packets_per_sec": 1000.0,
                    "open_dis_packets_per_sec": 250.0,
                    "fastdis_vs_open_dis_speedup": 4.0,
                    "claim_boundary": "Same-host route.",
                },
            }
        ],
    }

    text = module.render_markdown(report)

    assert "# Python vs OpenDIS benchmark" in text
    assert "fixture_count" in text
    assert "entity_state_fixture_header_scan" in text
    assert "FastDIS/OpenDIS speedup" in text


def test_build_report_uses_fixture_and_stubs(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")
    fixture = tmp_path / "EntityStatePdu.raw"
    fixture.write_bytes(b"packet")

    class FakeLib:
        path = "/tmp/libfastdis.dylib"

        def abi_version(self) -> int:
            return 7

        def version_string(self) -> str:
            return "0.0-test"

    monkeypatch.setattr(module, "load_open_dis", lambda root: object())
    monkeypatch.setattr(module.native, "load_native", lambda _path: FakeLib())
    monkeypatch.setattr(module, "maybe_git_rev", lambda root: "deadbeef")
    monkeypatch.setattr(
        module,
        "run_fastdis_header_benchmark",
        lambda lib, packets, rounds: {"packets_per_sec": 1000.0, "parsed_packets": len(packets) * rounds, "rounds": rounds, "packets_per_round": len(packets), "total_seconds": 1.0, "avg_ms": 1.0, "best_ms": 1.0, "p50_ms": 1.0, "p95_ms": 1.0, "p99_ms": 1.0, "worst_ms": 1.0, "mpps": 0.001, "stats": {}, "measurement_meaning": "fast"},
    )
    monkeypatch.setattr(
        module,
        "run_fastdis_entity_benchmark",
        lambda lib, packets, rounds: {"packets_per_sec": 900.0, "parsed_packets": len(packets) * rounds, "rounds": rounds, "packets_per_round": len(packets), "total_seconds": 1.0, "avg_ms": 1.0, "best_ms": 1.0, "p50_ms": 1.0, "p95_ms": 1.0, "p99_ms": 1.0, "worst_ms": 1.0, "mpps": 0.001, "stats": {}, "measurement_meaning": "fast-entity"},
    )
    monkeypatch.setattr(
        module,
        "run_open_dis_benchmark",
        lambda create_pdu, packets, rounds, extract_entity_fields: {"packets_per_sec": 300.0 if not extract_entity_fields else 200.0, "parsed_packets": len(packets) * rounds, "rounds": rounds, "packets_per_round": len(packets), "total_seconds": 1.0, "avg_ms": 1.0, "best_ms": 1.0, "p50_ms": 1.0, "p95_ms": 1.0, "p99_ms": 1.0, "worst_ms": 1.0, "mpps": 0.001, "stats": {}, "measurement_meaning": "open"},
    )

    report = module.build_report(
        open_dis_root=tmp_path,
        fixture_path=fixture,
        fixture_paths=[fixture],
        lib_path=None,
        packets=10,
        rounds=2,
    )

    assert report["schema"] == "fastdis.python_opendis_benchmark_report.v1"
    assert report["oracle"]["git_rev"] == "deadbeef"
    assert report["fixture"]["packet_bytes"] == 6
    assert report["summary"]["scenario_count"] == 3
    assert report["summary"]["best_speedup"] == 4.5


def test_resolve_fixture_path_prefers_entity_state_fixture(tmp_path: Path) -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    generic = tests_dir / "SignalPdu.raw"
    entity = tests_dir / "EntityStatePdu-26.raw"
    generic.write_bytes(b"x")
    entity.write_bytes(b"y")

    resolved = module.resolve_fixture_path(tmp_path, None)

    assert resolved == entity


def test_resolve_fixture_paths_returns_all_raw_fixtures(tmp_path: Path) -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    first = tests_dir / "SignalPdu.raw"
    second = tests_dir / "EntityStatePdu-26.raw"
    first.write_bytes(b"x")
    second.write_bytes(b"y")

    resolved = module.resolve_fixture_paths(tmp_path, None)

    assert resolved == [second, first]


def test_build_packet_replay_round_robins_fixtures(tmp_path: Path) -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")
    first = tmp_path / "a.raw"
    second = tmp_path / "b.raw"
    first.write_bytes(b"a")
    second.write_bytes(b"b")

    replay = module.build_packet_replay([first, second], 5)

    assert replay == [b"a", b"b", b"a", b"b", b"a"]


def test_main_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    module = _load_module("run_opendis_python_benchmark", ROOT / "tools" / "run_opendis_python_benchmark.py")
    open_dis_root = tmp_path / "open-dis-python"
    tests_dir = open_dis_root / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "EntityStatePdu.raw").write_bytes(b"packet")
    json_out = tmp_path / "out" / "python_vs_opendis.json"
    md_out = tmp_path / "out" / "python_vs_opendis.md"

    monkeypatch.setattr(
        module,
        "build_report",
        lambda **kwargs: {
            "schema": "fastdis.python_opendis_benchmark_report.v1",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "oracle": {"name": "open-dis-python", "root": str(open_dis_root)},
            "fastdis": {"library_path": "/tmp/lib", "abi_version": 7, "library_version": "0.0-test"},
            "fixture": {
                "path": str(tests_dir / "EntityStatePdu.raw"),
                "packet_bytes": 6,
                "packets_per_round": 10,
                "rounds": 2,
                "fixture_count": 1,
                "fixture_names": ["EntityStatePdu.raw"],
            },
            "scenarios": [],
            "summary": {"scenario_count": 0, "measured_scenarios": 0, "best_speedup": None, "notes": []},
        },
    )

    assert module.main(
        [
            "--open-dis-root",
            str(open_dis_root),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    ) == 0

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.python_opendis_benchmark_report.v1"
    assert md_out.is_file()
