from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import host_evidence_capability_trace


def _profile(label: str) -> object:
    return type(
        "Profile",
        (),
        {
            "host_slug": label,
            "host_label": label,
            "host_platform": "windows",
            "hostname": label,
            "platform_string": "Windows-11-x86_64",
            "system": "Windows",
            "release": "11",
            "machine": "x86_64",
            "python_version": "3.13.0",
            "host_fingerprint": f"fingerprint-{label}",
            "identity_source": "detected",
        },
    )()


def test_build_trace_projects_alpha2_and_alpha3_baselines(monkeypatch) -> None:
    monkeypatch.setattr(
        host_evidence_capability_trace.host_capability_matrix,
        "build_payload",
        lambda **_kwargs: {
            "schema": "fastdis.host_capability_matrix.v1",
            "workspace": {"id": "packet-stoat"},
            "route_summary": {"ready_now": ["python-core", "godot-native", "unreal-native"]},
            "competitor_summary": {"ready_now": [], "blocked_on_competitor": [], "missing_source": []},
            "routes": [
                {
                    "name": "python-core",
                    "label": "Python Core",
                    "activation": "ready-now",
                    "evidence_commands": ["python -m pytest"],
                    "tasks": [],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "python ready",
                },
                {
                    "name": "godot-native",
                    "label": "Godot Native",
                    "activation": "ready-now",
                    "evidence_commands": ["python tools/run_godot_report.py --out-dir artifacts/verification_reports/alpha2_sample"],
                    "tasks": [{"artifacts": ["artifacts/verification_reports/alpha2_sample/godot_workflow_report.json"]}],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "godot ready",
                },
                {
                    "name": "unreal-native",
                    "label": "Unreal Native",
                    "activation": "ready-now",
                    "evidence_commands": ["python tools/run_unreal_matrix.py --out-dir artifacts/verification_reports/alpha2_sample --versions 5.7 5.8"],
                    "tasks": [{"artifacts": ["artifacts/verification_reports/alpha2_sample/unreal_version_matrix.json"]}],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "unreal ready",
                },
            ],
            "competitor_routes": [],
        },
    )
    monkeypatch.setattr(host_evidence_capability_trace.host_profile, "resolve_host_profile", lambda **_kwargs: _profile("trace-host"))

    trace = host_evidence_capability_trace.build_trace()

    targets = {row["id"]: row for row in trace["evidence_targets"]}
    assert trace["schema"] == "fastdis.host_evidence_capability_trace.v1"
    assert targets["route.godot-native"]["potentially_runnable"] is True
    assert targets["alpha2.release_audit"]["potentially_runnable"] is True
    assert targets["alpha2.release_audit"]["depends_on"] == ["alpha2.signoff_matrix"]
    assert targets["alpha3.orientation_verification"]["potentially_runnable"] is True
    assert trace["baselines"]["alpha2"]["potentially_sufficient"] is True
    assert trace["baselines"]["alpha3"]["potentially_sufficient"] is True


def test_analyze_recomputes_union_sufficiency_from_multiple_hosts(monkeypatch) -> None:
    base_payload = {
        "schema": "fastdis.host_capability_matrix.v1",
        "workspace": {"id": "packet-stoat"},
        "route_summary": {"ready_now": ["python-core"]},
        "competitor_summary": {"ready_now": [], "blocked_on_competitor": [], "missing_source": []},
        "competitor_routes": [],
    }

    def build_payload(**_kwargs):
        profile = build_payload.current
        routes = [
            {
                "name": "python-core",
                "label": "Python Core",
                "activation": "ready-now",
                "evidence_commands": ["python -m pytest"],
                "tasks": [],
                "missing_installs": [],
                "missing_setup_steps": [],
                "requirement_failures": [],
                "remediation_steps": [],
                "detail": "python ready",
            }
        ]
        if profile.host_label == "host-a":
            routes.append(
                {
                    "name": "godot-native",
                    "label": "Godot Native",
                    "activation": "ready-now",
                    "evidence_commands": ["python tools/run_godot_report.py --out-dir artifacts/verification_reports/alpha2_sample"],
                    "tasks": [],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "godot ready",
                }
            )
            routes.append(
                {
                    "name": "unreal-native",
                    "label": "Unreal Native",
                    "activation": "supported-on-host",
                    "evidence_commands": ["python tools/run_unreal_matrix.py --out-dir artifacts/verification_reports/alpha2_sample --versions 5.7 5.8"],
                    "tasks": [],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "unreal discovered but not installed",
                }
            )
        else:
            routes.append(
                {
                    "name": "godot-native",
                    "label": "Godot Native",
                    "activation": "ready-after-install",
                    "evidence_commands": ["python tools/run_godot_report.py --out-dir artifacts/verification_reports/alpha2_sample"],
                    "tasks": [],
                    "missing_installs": ["godot"],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "godot installable",
                }
            )
            routes.append(
                {
                    "name": "unreal-native",
                    "label": "Unreal Native",
                    "activation": "ready-now",
                    "evidence_commands": ["python tools/run_unreal_matrix.py --out-dir artifacts/verification_reports/alpha2_sample --versions 5.7 5.8"],
                    "tasks": [],
                    "missing_installs": [],
                    "missing_setup_steps": [],
                    "requirement_failures": [],
                    "remediation_steps": [],
                    "detail": "unreal ready",
                }
            )
        return {**base_payload, "routes": routes}

    monkeypatch.setattr(host_evidence_capability_trace.host_capability_matrix, "build_payload", build_payload)

    traces = []
    for label in ("host-a", "host-b"):
        profile = _profile(label)
        build_payload.current = profile
        monkeypatch.setattr(host_evidence_capability_trace.host_profile, "resolve_host_profile", lambda **_kwargs: profile)
        traces.append(host_evidence_capability_trace.build_trace())

    report = host_evidence_capability_trace.analyze_traces(traces, baselines=["alpha2"])

    alpha2 = report["baselines"]["alpha2"]
    assert alpha2["potentially_sufficient"] is True
    assert alpha2["host_local_sufficient"] is True
    assert alpha2["host_local_hosts"] == ["host-a", "host-b"]


def test_main_capture_and_analyze_write_json(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        host_evidence_capability_trace,
        "build_trace",
        lambda **_kwargs: {
            "schema": "fastdis.host_evidence_capability_trace.v1",
            "host": {"host_label": "sample-host", "host_platform": "windows", "system": "Windows", "machine": "x86_64"},
            "evidence_targets": [],
            "baselines": {"alpha2": {"potentially_sufficient": False, "runnable_now": False, "missing_or_blocked": ["alpha2.unreal_version_matrix"]}},
        },
    )

    out_path = tmp_path / "trace.json"
    rc = host_evidence_capability_trace.main(["capture", "--out", str(out_path)])

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "fastdis.host_evidence_capability_trace.v1"

    union_path = tmp_path / "union.json"
    rc = host_evidence_capability_trace.main(["analyze", str(out_path), "--out", str(union_path), "--baseline", "alpha2"])

    assert rc == 0
    union_payload = json.loads(union_path.read_text(encoding="utf-8"))
    assert union_payload["schema"] == "fastdis.evidence_capability_union.v1"
    captured = capsys.readouterr()
    assert captured.out == ""


def test_analyze_auto_discovers_trace_dir(monkeypatch, tmp_path, capsys) -> None:
    trace_path = tmp_path / "sample.trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.host_evidence_capability_trace.v1",
                "host": {"host_label": "sample-host", "host_platform": "windows", "host_fingerprint": "abc"},
                "evidence_targets": [],
                "baselines": {"alpha2": {"potentially_sufficient": False}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        host_evidence_capability_trace,
        "analyze_traces",
        lambda traces, baselines: {
            "schema": "fastdis.evidence_capability_union.v1",
            "trace_count": len(traces),
            "hosts": [{"host_label": "sample-host"}],
            "baselines": {"alpha2": {"potentially_sufficient": False, "runnable_now": False, "host_local_sufficient": False, "host_local_hosts": [], "missing_or_blocked": ["alpha2.unreal_version_matrix"]}},
        },
    )

    rc = host_evidence_capability_trace.main(["analyze", "--trace-dir", str(tmp_path), "--baseline", "alpha2", "--format", "summary"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "FastDIS evidence capability union" in out
    assert "trace_count=1" in out


def test_refresh_writes_standard_trace_and_union_files(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        host_evidence_capability_trace,
        "build_trace",
        lambda **_kwargs: {
            "schema": "fastdis.host_evidence_capability_trace.v1",
            "host": {
                "host_label": "sample-host",
                "host_platform": "windows",
                "system": "Windows",
                "machine": "x86_64",
                "host_fingerprint": "fingerprint-sample-host",
            },
            "evidence_targets": [],
            "baselines": {
                "alpha2": {
                    "potentially_sufficient": True,
                    "runnable_now": True,
                    "missing_or_blocked": [],
                }
            },
        },
    )
    monkeypatch.setattr(
        host_evidence_capability_trace,
        "analyze_traces",
        lambda traces, baselines: {
            "schema": "fastdis.evidence_capability_union.v1",
            "trace_count": len(traces),
            "hosts": [{"host_label": "sample-host"}],
            "baselines": {
                "alpha2": {
                    "potentially_sufficient": True,
                    "runnable_now": True,
                    "host_local_sufficient": True,
                    "host_local_hosts": ["sample-host"],
                    "missing_or_blocked": [],
                }
            },
            "union_targets": [],
        },
    )

    rc = host_evidence_capability_trace.main(["refresh", "--trace-dir", str(tmp_path)])

    assert rc == 0
    assert (tmp_path / "current-host.trace.json").is_file()
    assert (tmp_path / "sample-host.trace.json").is_file()
    assert (tmp_path / "all-hosts.union.json").is_file()
    assert (tmp_path / "all-hosts.union.summary.txt").is_file()
    out = capsys.readouterr().out
    assert "current_trace=" in out
    assert "labelled_trace=" in out


def test_remaining_targets_subtracts_union_coverage_from_other_hosts() -> None:
    current_trace = {
        "host": {"host_label": "host-a", "host_platform": "windows"},
        "evidence_targets": [
            {"id": "route.python-core", "potentially_runnable": True, "activation": "ready-now", "commands": ["python -m pytest"], "artifacts": []},
            {"id": "route.unreal-native", "potentially_runnable": True, "activation": "ready-now", "commands": ["python tools/run_unreal_matrix.py"], "artifacts": []},
            {"id": "alpha2.release_audit", "potentially_runnable": True, "activation": "ready-now", "commands": ["python tools/run_alpha2_release_audit.py"], "artifacts": []},
        ],
    }
    union_report = {
        "union_targets": [
            {"id": "route.python-core", "potentially_runnable": True, "provider_hosts": ["host-b"]},
            {"id": "route.unreal-native", "potentially_runnable": True, "provider_hosts": ["host-a"]},
        ],
        "baselines": {
            "alpha2": {"potentially_sufficient": False},
        },
    }

    report = host_evidence_capability_trace.remaining_targets_for_host(current_trace, union_report, baselines=["alpha2"])

    remaining_ids = [row["id"] for row in report["remaining_targets"]]
    assert report["schema"] == "fastdis.remaining_evidence_targets.v1"
    assert "route.python-core" not in remaining_ids
    assert "route.unreal-native" in remaining_ids
    assert "alpha2.release_audit" in remaining_ids


def test_remaining_targets_suppresses_baseline_targets_when_union_is_already_sufficient() -> None:
    current_trace = {
        "host": {"host_label": "host-a", "host_platform": "windows"},
        "evidence_targets": [
            {"id": "alpha2.unreal_version_matrix", "potentially_runnable": True, "activation": "ready-now", "commands": [], "artifacts": []},
            {"id": "alpha2.release_audit", "potentially_runnable": True, "activation": "ready-now", "commands": [], "artifacts": []},
            {"id": "route.godot-native", "potentially_runnable": True, "activation": "ready-now", "commands": [], "artifacts": []},
        ],
    }
    union_report = {
        "union_targets": [],
        "baselines": {
            "alpha2": {"potentially_sufficient": True},
        },
    }

    report = host_evidence_capability_trace.remaining_targets_for_host(current_trace, union_report, baselines=["alpha2"])

    remaining_ids = [row["id"] for row in report["remaining_targets"]]
    assert "alpha2.unreal_version_matrix" not in remaining_ids
    assert "alpha2.release_audit" not in remaining_ids
    assert remaining_ids == ["route.godot-native"]


def test_main_remaining_uses_discovered_traces(monkeypatch, tmp_path, capsys) -> None:
    trace_path = tmp_path / "host-b.trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "schema": "fastdis.host_evidence_capability_trace.v1",
                "host": {"host_label": "host-b", "host_platform": "linux", "host_fingerprint": "b"},
                "evidence_targets": [],
                "baselines": {"alpha2": {"potentially_sufficient": True}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        host_evidence_capability_trace,
        "build_trace",
        lambda **_kwargs: {
            "schema": "fastdis.host_evidence_capability_trace.v1",
            "host": {"host_label": "host-a", "host_platform": "windows", "host_fingerprint": "a"},
            "evidence_targets": [
                {"id": "alpha2.release_audit", "potentially_runnable": True, "activation": "ready-now", "commands": [], "artifacts": []}
            ],
            "baselines": {"alpha2": {"potentially_sufficient": True}},
        },
    )
    monkeypatch.setattr(
        host_evidence_capability_trace,
        "analyze_traces",
        lambda traces, baselines: {
            "schema": "fastdis.evidence_capability_union.v1",
            "trace_count": len(traces),
            "hosts": [{"host_label": "host-b"}],
            "baselines": {"alpha2": {"potentially_sufficient": True}},
            "union_targets": [],
        },
    )

    rc = host_evidence_capability_trace.main(["remaining", "--trace-dir", str(tmp_path), "--baseline", "alpha2", "--format", "summary"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "FastDIS remaining evidence targets" in out
    assert "remaining=0" in out
