#!/usr/bin/env python3
"""Trace host evidence-generation capability without running the evidence lanes."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import evidence_layout
import host_capability_matrix
import host_profile
import load_local_env
import run_alpha2_signoff_matrix


ROOT = Path(__file__).resolve().parents[1]
ALPHA2_VERSIONS = tuple(run_alpha2_signoff_matrix.DEFAULT_REQUIRED_UNREAL_VERSIONS)
ALPHA3_VERSIONS = ("5.7", "5.8")
DEFAULT_TRACE_DIR = ROOT / "dist" / "host_evidence_traces"

READY_ACTIVATIONS = ("ready-now", "ready-after-install", "ready-after-setup", "supported-on-host")
READY_ORDER = {name: index for index, name in enumerate(READY_ACTIVATIONS)}
BLOCKED_ORDER = {
    "blocked-by-version-policy": 0,
    "blocked-on-competitor": 1,
    "missing-source": 2,
    "unsupported-on-host": 3,
}


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _route_blockers(route: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for name in route.get("missing_installs") or []:
        blockers.append(f"missing install: {name}")
    for step in route.get("missing_setup_steps") or []:
        blockers.append(f"missing setup: {step}")
    for failure in route.get("requirement_failures") or []:
        if not isinstance(failure, dict):
            continue
        reason = str(failure.get("reason") or failure.get("message") or "").strip()
        if reason:
            blockers.append(reason)
    for step in route.get("remediation_steps") or []:
        blockers.append(f"remediation: {step}")
    return blockers


def _artifacts_from_route(route: dict[str, Any]) -> list[str]:
    artifacts: list[str] = []
    for task in route.get("tasks") or []:
        if not isinstance(task, dict):
            continue
        for artifact in task.get("artifacts") or []:
            value = str(artifact).strip()
            if value and value not in artifacts:
                artifacts.append(value)
    return artifacts


def _activation_for_requirements(required: list[dict[str, Any]]) -> tuple[str, bool, bool, list[str]]:
    if not required:
        return "ready-now", True, True, []
    blockers: list[str] = []
    if all(bool(item.get("potentially_runnable")) for item in required):
        activation = "ready-now"
        for item in required:
            candidate = str(item.get("activation") or "ready-now")
            if READY_ORDER.get(candidate, 0) > READY_ORDER.get(activation, 0):
                activation = candidate
        runnable_now = all(bool(item.get("runnable_now")) for item in required)
        for item in required:
            for blocker in item.get("blockers") or []:
                if blocker not in blockers:
                    blockers.append(str(blocker))
        return activation, runnable_now, True, blockers
    blocking_candidates = [
        str(item.get("activation") or "unsupported-on-host")
        for item in required
        if not bool(item.get("potentially_runnable"))
    ]
    activation = min(blocking_candidates, key=lambda name: BLOCKED_ORDER.get(name, 99)) if blocking_candidates else "unsupported-on-host"
    for item in required:
        if bool(item.get("potentially_runnable")):
            continue
        for blocker in item.get("blockers") or []:
            if blocker not in blockers:
                blockers.append(str(blocker))
    if not blockers:
        for item in required:
            if not bool(item.get("potentially_runnable")):
                blockers.append(f"{item.get('id', 'target')} is {item.get('activation', 'unavailable')}")
    return activation, False, False, blockers


def _spec(
    *,
    label: str,
    commands: list[str],
    artifacts: list[str],
    requires: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "label": label,
        "commands": commands,
        "artifacts": artifacts,
        "requires": requires or [],
        "notes": notes,
    }


def _baseline_specs() -> dict[str, dict[str, dict[str, Any]]]:
    alpha2_out = "artifacts/verification_reports/alpha2_sample"
    alpha2_versions = " ".join(ALPHA2_VERSIONS)
    alpha3_out = "verification_reports/alpha3_current"
    alpha3_versions = " ".join(ALPHA3_VERSIONS)
    return {
        "alpha2": {
            "alpha2.unreal_version_matrix": _spec(
                label="Alpha 2 Unreal Version Matrix",
                commands=[f"python tools/run_unreal_matrix.py --out-dir {alpha2_out} --versions {alpha2_versions}"],
                artifacts=[f"{alpha2_out}/unreal_version_matrix.json", f"{alpha2_out}/unreal_version_matrix.md"],
                requires=["route.unreal-native"],
            ),
            "alpha2.godot_workflow": _spec(
                label="Alpha 2 Godot Workflow Report",
                commands=[f"python tools/run_godot_report.py --out-dir {alpha2_out}"],
                artifacts=[f"{alpha2_out}/godot_workflow_report.json", f"{alpha2_out}/godot_workflow_report.md"],
                requires=["route.godot-native"],
            ),
            "alpha2.orientation_runtime": _spec(
                label="Alpha 2 Orientation Runtime Report",
                commands=[
                    f"python tools/run_orientation_runtime_report.py --out-dir {alpha2_out}"
                    + "".join(f" --engine-version {version}" for version in ALPHA2_VERSIONS)
                ],
                artifacts=[f"{alpha2_out}/orientation_runtime_report.json", f"{alpha2_out}/orientation_runtime_report.md"],
                requires=["route.unreal-native", "route.godot-native"],
            ),
            "alpha2.orientation_visual": _spec(
                label="Alpha 2 Orientation Visual Report",
                commands=[
                    f"python tools/run_orientation_visual_report.py --out-dir {alpha2_out}"
                    + "".join(f" --engine-version {version}" for version in ALPHA2_VERSIONS)
                ],
                artifacts=[f"{alpha2_out}/orientation_visual_report.json", f"{alpha2_out}/orientation_visual_report.md"],
                requires=["route.unreal-native", "route.godot-native"],
            ),
            "alpha2.unreal_host_compat": _spec(
                label="Alpha 2 Unreal Host Compatibility Report",
                commands=[f"python tools/run_unreal_host_compat_report.py --out-dir {alpha2_out} --versions {alpha2_versions}"],
                artifacts=[f"{alpha2_out}/unreal_host_compat_report.json", f"{alpha2_out}/unreal_host_compat_report.md"],
                requires=["route.unreal-native"],
            ),
            "alpha2.signoff_matrix": _spec(
                label="Alpha 2 Signoff Matrix",
                commands=[f"python tools/run_alpha2_signoff_matrix.py --out-dir {alpha2_out} --min-host-count 1"],
                artifacts=[f"{alpha2_out}/alpha2_signoff_matrix.json", f"{alpha2_out}/alpha2_signoff_matrix.md"],
                requires=[
                    "alpha2.unreal_version_matrix",
                    "alpha2.godot_workflow",
                    "alpha2.orientation_runtime",
                    "alpha2.orientation_visual",
                    "alpha2.unreal_host_compat",
                ],
            ),
            "alpha2.release_audit": _spec(
                label="Alpha 2 Release Audit",
                commands=[f"python tools/run_alpha2_release_audit.py --out-dir {alpha2_out}"],
                artifacts=[f"{alpha2_out}/alpha2_release_audit_report.json", f"{alpha2_out}/alpha2_release_audit_report.md"],
                requires=["alpha2.signoff_matrix"],
            ),
        },
        "alpha3": {
            "alpha3.orientation_verification": _spec(
                label="Alpha 3 Orientation Verification Report",
                commands=[f"python tools/run_orientation_report.py --output-dir {alpha3_out}"],
                artifacts=[f"{alpha3_out}/orientation_verification_report.json", f"{alpha3_out}/orientation_verification_report.md"],
                requires=["route.python-core"],
            ),
            "alpha3.orientation_visual": _spec(
                label="Alpha 3 Orientation Visual Report",
                commands=[
                    f"python tools/run_orientation_visual_report.py --out-dir {alpha3_out}"
                    + "".join(f" --engine-version {version}" for version in ALPHA3_VERSIONS[-1:])
                ],
                artifacts=[f"{alpha3_out}/orientation_visual_report.json", f"{alpha3_out}/orientation_visual_report.md"],
                requires=["route.unreal-native", "route.godot-native"],
            ),
            "alpha3.orientation_pipeline": _spec(
                label="Alpha 3 Orientation Pipeline Report",
                commands=[f"python tools/run_orientation_pipeline_report.py --out-dir {alpha3_out}"],
                artifacts=[f"{alpha3_out}/orientation_pipeline_report.json", f"{alpha3_out}/orientation_pipeline_report.md"],
                requires=["route.python-core"],
            ),
            "alpha3.godot_workflow": _spec(
                label="Alpha 3 Godot Workflow Report",
                commands=[f"python tools/run_godot_report.py --out-dir {alpha3_out}"],
                artifacts=[f"{alpha3_out}/godot_workflow_report.json", f"{alpha3_out}/godot_workflow_report.md"],
                requires=["route.godot-native"],
            ),
            "alpha3.unreal_version_matrix": _spec(
                label="Alpha 3 Unreal Version Matrix",
                commands=[f"python tools/run_unreal_matrix.py --out-dir {alpha3_out} --versions {alpha3_versions}"],
                artifacts=[f"{alpha3_out}/unreal_version_matrix.json", f"{alpha3_out}/unreal_version_matrix.md"],
                requires=["route.unreal-native"],
            ),
            "alpha3.sanitizer_smoke": _spec(
                label="Alpha 3 Sanitizer Smoke Report",
                commands=[f"python tools/run_alpha3_sanitizer_report.py --out-dir {alpha3_out}"],
                artifacts=[f"{alpha3_out}/sanitizer_smoke_report.json", f"{alpha3_out}/sanitizer_smoke_report.md"],
                requires=["route.python-core"],
            ),
            "alpha3.io_routes": _spec(
                label="Alpha 3 I/O Routes Report",
                commands=[f"python tools/run_io_routes_report.py --out-dir {alpha3_out}"],
                artifacts=[f"{alpha3_out}/io_routes_report.json", f"{alpha3_out}/io_routes_report.md"],
                requires=["route.python-core"],
            ),
            "alpha3.network_ingest_matrix": _spec(
                label="Alpha 3 Network Ingest Matrix",
                commands=[f"python tools/run_network_ingest_matrix.py --out-dir {alpha3_out}"],
                artifacts=[f"{alpha3_out}/network_ingest_matrix.json", f"{alpha3_out}/network_ingest_matrix.md"],
                requires=["route.python-core"],
                notes="This capability trace models the shared/core route dependency only; actual host truth may still depend on local engine/runtime setup.",
            ),
        },
    }


def _baseline_required_targets() -> dict[str, list[str]]:
    return {
        "alpha2": [
            "alpha2.unreal_version_matrix",
            "alpha2.godot_workflow",
            "alpha2.orientation_runtime",
            "alpha2.orientation_visual",
            "alpha2.unreal_host_compat",
            "alpha2.signoff_matrix",
            "alpha2.release_audit",
        ],
        "alpha3": [
            "alpha3.orientation_verification",
            "alpha3.orientation_visual",
            "alpha3.orientation_pipeline",
            "alpha3.godot_workflow",
            "alpha3.unreal_version_matrix",
            "alpha3.sanitizer_smoke",
            "alpha3.io_routes",
            "alpha3.network_ingest_matrix",
        ],
    }


def _route_target(route: dict[str, Any], *, prefix: str, kind: str, baseline_ids: list[str] | None = None) -> dict[str, Any]:
    activation = str(route.get("activation") or "unsupported-on-host")
    return {
        "id": f"{prefix}.{route['name']}",
        "label": str(route.get("label") or route["name"]),
        "kind": kind,
        "activation": activation,
        "runnable_now": activation == "ready-now",
        "potentially_runnable": activation in READY_ACTIVATIONS,
        "commands": list(route.get("evidence_commands") or []),
        "artifacts": _artifacts_from_route(route),
        "source_routes": [route["name"]],
        "depends_on": [],
        "baseline_ids": list(baseline_ids or []),
        "blockers": _route_blockers(route),
        "detail": str(route.get("detail") or ""),
        "notes": str(route.get("notes") or ""),
    }


def _best_target(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    a_ready = bool(a.get("potentially_runnable"))
    b_ready = bool(b.get("potentially_runnable"))
    if a_ready and not b_ready:
        return a
    if b_ready and not a_ready:
        return b
    if a_ready and b_ready:
        a_rank = READY_ORDER.get(str(a.get("activation") or "supported-on-host"), 99)
        b_rank = READY_ORDER.get(str(b.get("activation") or "supported-on-host"), 99)
        return a if a_rank <= b_rank else b
    a_rank = BLOCKED_ORDER.get(str(a.get("activation") or "unsupported-on-host"), 99)
    b_rank = BLOCKED_ORDER.get(str(b.get("activation") or "unsupported-on-host"), 99)
    return a if a_rank <= b_rank else b


def _evaluate_spec_target(
    target_id: str,
    spec: dict[str, Any],
    available: dict[str, dict[str, Any]],
    spec_map: dict[str, dict[str, Any]],
    stack: set[str] | None = None,
) -> dict[str, Any]:
    if target_id in available:
        return available[target_id]
    if stack is None:
        stack = set()
    if target_id in stack:
        raise ValueError(f"cyclic evidence target dependency detected at {target_id}")
    stack.add(target_id)
    requirements = [
        _evaluate_spec_target(required_id, spec_map[required_id], available, spec_map, stack)
        if required_id in spec_map
        else available.get(
            required_id,
            {
                "id": required_id,
                "label": required_id,
                "kind": "missing-target",
                "activation": "unsupported-on-host",
                "runnable_now": False,
                "potentially_runnable": False,
                "commands": [],
                "artifacts": [],
                "source_routes": [],
                "depends_on": [],
                "baseline_ids": [],
                "blockers": [f"missing target: {required_id}"],
                "detail": "",
                "notes": "",
            },
        )
        for required_id in spec.get("requires") or []
    ]
    activation, runnable_now, potentially_runnable, blockers = _activation_for_requirements(requirements)
    commands: list[str] = []
    for command in spec.get("commands") or []:
        value = str(command)
        if value not in commands:
            commands.append(value)
    source_routes: list[str] = []
    for item in requirements:
        for route_name in item.get("source_routes") or []:
            value = str(route_name)
            if value not in source_routes:
                source_routes.append(value)
    target = {
        "id": target_id,
        "label": str(spec.get("label") or target_id),
        "kind": "baseline-target",
        "activation": activation,
        "runnable_now": runnable_now,
        "potentially_runnable": potentially_runnable,
        "commands": commands,
        "artifacts": [str(value) for value in spec.get("artifacts") or []],
        "source_routes": source_routes,
        "depends_on": [str(value) for value in spec.get("requires") or []],
        "baseline_ids": [target_id.split(".", 1)[0]],
        "blockers": blockers,
        "detail": "",
        "notes": str(spec.get("notes") or ""),
    }
    available[target_id] = target
    stack.remove(target_id)
    return target


def _evaluate_baseline(
    baseline_id: str,
    available: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = _baseline_specs()[baseline_id]
    required_targets = _baseline_required_targets()[baseline_id]
    computed = dict(available)
    rows = [_evaluate_spec_target(target_id, specs[target_id], computed, specs) for target_id in specs]
    required_rows = [computed[target_id] for target_id in required_targets]
    summary = {
        "baseline": baseline_id,
        "required_targets": required_targets,
        "potentially_sufficient": all(bool(item.get("potentially_runnable")) for item in required_rows),
        "runnable_now": all(bool(item.get("runnable_now")) for item in required_rows),
        "missing_or_blocked": [item["id"] for item in required_rows if not bool(item.get("potentially_runnable"))],
        "not_ready_now": [item["id"] for item in required_rows if not bool(item.get("runnable_now"))],
    }
    return rows, summary


def build_trace(*, host_system_override: str | None = None, host_machine_override: str | None = None, host_platform_override: str | None = None) -> dict[str, Any]:
    payload = host_capability_matrix.build_payload(
        host_system_override=host_system_override,
        host_machine_override=host_machine_override,
        host_platform_override=host_platform_override,
    )
    profile = host_profile.resolve_host_profile(
        system_override=host_system_override or host_platform_override,
        machine_override=host_machine_override,
        host_platform_override=host_platform_override,
    )
    generic_targets = [
        *[_route_target(route, prefix="route", kind="workspace-route") for route in payload.get("routes", [])],
        *[_route_target(route, prefix="competitor", kind="competitor-route") for route in payload.get("competitor_routes", [])],
    ]
    available = {target["id"]: target for target in generic_targets}
    baseline_targets: list[dict[str, Any]] = []
    baselines: dict[str, Any] = {}
    for baseline_id in sorted(_baseline_specs()):
        rows, summary = _evaluate_baseline(baseline_id, available)
        baseline_targets.extend(rows)
        baselines[baseline_id] = summary
    targets = generic_targets + [
        target for target in baseline_targets if target["id"] not in {item["id"] for item in generic_targets}
    ]
    return {
        "schema": "fastdis.host_evidence_capability_trace.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "workspace": payload.get("workspace") or {},
        "host": {
            "host_label": profile.host_label,
            "host_platform": profile.host_platform,
            "hostname": profile.hostname,
            "platform": profile.platform_string,
            "system": profile.system,
            "release": profile.release,
            "machine": profile.machine,
            "python_version": profile.python_version,
            "host_fingerprint": profile.host_fingerprint,
            "identity_source": profile.identity_source,
        },
        "source": {
            "host_capability_matrix_schema": payload.get("schema"),
            "route_summary": payload.get("route_summary") or {},
            "competitor_summary": payload.get("competitor_summary") or {},
        },
        "evidence_targets": targets,
        "baselines": baselines,
        "claim_boundaries": [
            "This is a capability trace, not a proof artifact. It describes what the host appears able to generate without running the evidence lanes.",
            "Baseline sufficiency here means route and dependency coverage only. It does not claim that the eventual generated evidence will pass its truth checks.",
        ],
    }


def merge_trace_targets(traces: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for trace in traces:
        host = (trace.get("host") or {}) if isinstance(trace.get("host"), dict) else {}
        host_label = str(host.get("host_label") or "host")
        for item in trace.get("evidence_targets") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            target = dict(item)
            target["provider_hosts"] = [host_label]
            current = merged.get(target["id"])
            if current is None:
                merged[target["id"]] = target
                continue
            best = _best_target(current, target)
            provider_hosts = sorted(set((current.get("provider_hosts") or []) + [host_label]))
            commands = sorted(set((current.get("commands") or []) + (target.get("commands") or [])))
            artifacts = sorted(set((current.get("artifacts") or []) + (target.get("artifacts") or [])))
            source_routes = sorted(set((current.get("source_routes") or []) + (target.get("source_routes") or [])))
            blockers = sorted(set((current.get("blockers") or []) + (target.get("blockers") or [])))
            depends_on = sorted(set((current.get("depends_on") or []) + (target.get("depends_on") or [])))
            baseline_ids = sorted(set((current.get("baseline_ids") or []) + (target.get("baseline_ids") or [])))
            merged[target["id"]] = {
                **best,
                "provider_hosts": provider_hosts,
                "commands": commands,
                "artifacts": artifacts,
                "source_routes": source_routes,
                "blockers": blockers,
                "depends_on": depends_on,
                "baseline_ids": baseline_ids,
                "runnable_now": bool(current.get("runnable_now")) or bool(target.get("runnable_now")),
                "potentially_runnable": bool(current.get("potentially_runnable")) or bool(target.get("potentially_runnable")),
            }
    return merged


def analyze_traces(traces: list[dict[str, Any]], *, baselines: list[str]) -> dict[str, Any]:
    merged_generic = {
        target_id: row
        for target_id, row in merge_trace_targets(traces).items()
        if not target_id.startswith("alpha2.") and not target_id.startswith("alpha3.")
    }
    baseline_rows: list[dict[str, Any]] = []
    baseline_summaries: dict[str, Any] = {}
    for baseline_id in baselines:
        rows, summary = _evaluate_baseline(baseline_id, merged_generic)
        baseline_rows.extend(rows)
        host_local = [
            str((trace.get("host") or {}).get("host_label") or "host")
            for trace in traces
            if bool(((trace.get("baselines") or {}).get(baseline_id) or {}).get("potentially_sufficient"))
        ]
        summary["host_local_sufficient"] = bool(host_local)
        summary["host_local_hosts"] = host_local
        baseline_summaries[baseline_id] = summary
    host_rows = [
        {
            "host_label": str(((trace.get("host") or {}).get("host_label") or "")),
            "host_platform": str(((trace.get("host") or {}).get("host_platform") or "")),
            "host_fingerprint": str(((trace.get("host") or {}).get("host_fingerprint") or "")),
        }
        for trace in traces
    ]
    return {
        "schema": "fastdis.evidence_capability_union.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "trace_count": len(traces),
        "hosts": host_rows,
        "baselines": baseline_summaries,
        "union_targets": sorted(
            list(merged_generic.values()) + baseline_rows,
            key=lambda item: str(item.get("id") or ""),
        ),
        "claim_boundaries": [
            "This union report combines capability traces from one or more hosts.",
            "A baseline marked sufficient here means the union of hosts appears able to generate the required evidence set; it does not mean the generated artifacts already exist or would automatically pass.",
        ],
    }


def render_trace_summary(trace: dict[str, Any]) -> str:
    host = trace["host"]
    lines = [
        "FastDIS host evidence capability trace",
        f"host={host['host_label']} platform={host['host_platform']} system={host['system']} machine={host['machine']}",
    ]
    for baseline_id, summary in sorted((trace.get("baselines") or {}).items()):
        lines.append(
            f"{baseline_id}=potentially_sufficient={summary['potentially_sufficient']};"
            + f"runnable_now={summary['runnable_now']};"
            + f"missing_or_blocked={','.join(summary['missing_or_blocked']) or 'none'}"
        )
    return "\n".join(lines)


def render_union_summary(report: dict[str, Any]) -> str:
    lines = [
        "FastDIS evidence capability union",
        f"trace_count={report['trace_count']}",
        "hosts=" + ",".join(row["host_label"] for row in report.get("hosts", [])) if report.get("hosts") else "hosts=none",
    ]
    for baseline_id, summary in sorted((report.get("baselines") or {}).items()):
        lines.append(
            f"{baseline_id}=potentially_sufficient={summary['potentially_sufficient']};"
            + f"runnable_now={summary['runnable_now']};"
            + f"host_local_sufficient={summary['host_local_sufficient']};"
            + f"host_local_hosts={','.join(summary['host_local_hosts']) or 'none'};"
            + f"missing_or_blocked={','.join(summary['missing_or_blocked']) or 'none'}"
        )
    return "\n".join(lines)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")


def _load_trace_paths(paths: list[str]) -> list[dict[str, Any]]:
    return [
        json.loads(Path(raw).expanduser().resolve().read_text(encoding="utf-8"))
        for raw in paths
    ]


def _discover_trace_paths(trace_dir: Path) -> list[Path]:
    if not trace_dir.is_dir():
        return []
    return sorted(
        path.resolve()
        for path in trace_dir.glob("*.trace.json")
        if path.is_file()
    )


def refresh_trace_dir(
    *,
    trace_dir: Path,
    baselines: list[str],
    host_system_override: str | None = None,
    host_machine_override: str | None = None,
    host_platform_override: str | None = None,
) -> dict[str, Any]:
    trace = build_trace(
        host_system_override=host_system_override,
        host_machine_override=host_machine_override,
        host_platform_override=host_platform_override,
    )
    host_label = str(((trace.get("host") or {}).get("host_label") or "host"))
    trace_json = json.dumps(trace, indent=2)
    trace_dir.mkdir(parents=True, exist_ok=True)
    current_path = trace_dir / "current-host.trace.json"
    labelled_path = trace_dir / f"{host_label}.trace.json"
    _write_text(current_path, trace_json)
    _write_text(labelled_path, trace_json)

    trace_paths = _discover_trace_paths(trace_dir)
    union = analyze_traces(_load_trace_paths([str(path) for path in trace_paths]), baselines=baselines)
    union_json = json.dumps(union, indent=2)
    union_summary = render_union_summary(union)
    union_json_path = trace_dir / "all-hosts.union.json"
    union_summary_path = trace_dir / "all-hosts.union.summary.txt"
    _write_text(union_json_path, union_json)
    _write_text(union_summary_path, union_summary)
    return {
        "trace": trace,
        "trace_paths": [str(path) for path in trace_paths],
        "current_path": str(current_path.resolve()),
        "labelled_path": str(labelled_path.resolve()),
        "union": union,
        "union_json_path": str(union_json_path.resolve()),
        "union_summary_path": str(union_summary_path.resolve()),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture", help="Capture one host's evidence capability trace")
    capture.add_argument("--format", choices=("json", "summary"), default="json")
    capture.add_argument("--out")
    capture.add_argument("--host-platform-override", choices=("windows", "macos", "linux"))
    capture.add_argument("--host-system-override")
    capture.add_argument("--host-machine-override")

    analyze = subparsers.add_parser("analyze", help="Union one or more host traces and evaluate baseline sufficiency")
    analyze.add_argument("trace", nargs="*", help="One or more host trace JSON files")
    analyze.add_argument("--trace-dir", default=str(DEFAULT_TRACE_DIR), help="Directory to auto-discover `*.trace.json` files from when no explicit trace paths are provided")
    analyze.add_argument("--baseline", action="append", choices=sorted(_baseline_specs()), help="Baseline to evaluate; repeat as needed")
    analyze.add_argument("--format", choices=("json", "summary"), default="json")
    analyze.add_argument("--out")

    refresh = subparsers.add_parser("refresh", help="Capture this host into the standard trace folder and refresh the all-hosts union reports")
    refresh.add_argument("--trace-dir", default=str(DEFAULT_TRACE_DIR), help="Directory for host trace JSON files and generated union reports")
    refresh.add_argument("--baseline", action="append", choices=sorted(_baseline_specs()), help="Baseline to include in the generated union report; repeat as needed")
    refresh.add_argument("--format", choices=("json", "summary"), default="summary", help="Output format for the terminal summary")
    refresh.add_argument("--host-platform-override", choices=("windows", "macos", "linux"))
    refresh.add_argument("--host-system-override")
    refresh.add_argument("--host-machine-override")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_local_env.load()
    args = parse_args(argv)
    if args.command == "capture":
        trace = build_trace(
            host_system_override=args.host_system_override,
            host_machine_override=args.host_machine_override,
            host_platform_override=args.host_platform_override,
        )
        rendered = json.dumps(trace, indent=2) if args.format == "json" else render_trace_summary(trace)
        if args.out:
            _write_text(Path(args.out).expanduser().resolve(), rendered)
        else:
            print(rendered)
        return 0
    if args.command == "refresh":
        result = refresh_trace_dir(
            trace_dir=Path(args.trace_dir).expanduser().resolve(),
            baselines=args.baseline or sorted(_baseline_specs()),
            host_system_override=args.host_system_override,
            host_machine_override=args.host_machine_override,
            host_platform_override=args.host_platform_override,
        )
        if args.format == "json":
            print(json.dumps(result["union"], indent=2))
        else:
            print(render_trace_summary(result["trace"]))
            print("")
            print(f"current_trace={_display_path(Path(result['current_path']))}")
            print(f"labelled_trace={_display_path(Path(result['labelled_path']))}")
            print(f"union_json={_display_path(Path(result['union_json_path']))}")
            print(f"union_summary={_display_path(Path(result['union_summary_path']))}")
        return 0
    trace_paths = list(args.trace)
    if not trace_paths:
        trace_paths = [str(path) for path in _discover_trace_paths(Path(args.trace_dir).expanduser().resolve())]
        if not trace_paths:
            raise SystemExit("No trace files were provided and none were found in the trace directory.")
    traces = _load_trace_paths(trace_paths)
    report = analyze_traces(traces, baselines=args.baseline or sorted(_baseline_specs()))
    rendered = json.dumps(report, indent=2) if args.format == "json" else render_union_summary(report)
    if args.out:
        _write_text(Path(args.out).expanduser().resolve(), rendered)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
