#!/usr/bin/env python3
"""Normalize Cesium engine-lane vendor reports into one comparable matrix."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "reports" / "cesium_engine_matrix"
DEFAULT_JSON_OUT = DEFAULT_OUT_DIR / "cesium_engine_matrix.json"
DEFAULT_MD_OUT = DEFAULT_OUT_DIR / "cesium_engine_matrix.md"


def _preferred_report_path(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


DEFAULT_UNREAL_57 = _preferred_report_path(
    ROOT / "artifacts" / "reports" / "unreal_vendor_plugin" / "cesium_5_7_upstream_handoff.json",
)
DEFAULT_UNREAL_58 = _preferred_report_path(
    ROOT / "artifacts" / "reports" / "unreal_vendor_plugin" / "cesium_5_8_upstream_handoff.json",
)
DEFAULT_UNITY = _preferred_report_path(
    ROOT / "artifacts" / "reports" / "unity_vendor_plugin" / "cesium-unity_6000_5_upstream_handoff.json",
)
DEFAULT_GODOT = _preferred_report_path(
    ROOT / "artifacts" / "reports" / "godot_vendor_plugin" / "cesium-godot_upstream_handoff_windows_live.json",
    ROOT / "artifacts" / "reports" / "godot_vendor_plugin" / "cesium-godot_upstream_handoff.json",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--unreal-57", type=Path, default=DEFAULT_UNREAL_57)
    parser.add_argument("--unreal-58", type=Path, default=DEFAULT_UNREAL_58)
    parser.add_argument("--unity", type=Path, default=DEFAULT_UNITY)
    parser.add_argument("--godot", type=Path, default=DEFAULT_GODOT)
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _status_token(value: object) -> str:
    return str(value or "").strip().lower()


def _line_detail(*values: object) -> str:
    for value in values:
        if isinstance(value, list):
            for row in value:
                text = str(row).strip()
                if text:
                    return text
        text = str(value or "").strip()
        if text:
            return text
    return ""


def summarize_unreal(label: str, path: Path) -> dict[str, object]:
    payload = load_json(path)
    if payload is None:
        return {
            "lane": label,
            "surface": "unreal",
            "engine_version": label.split("-", 1)[1],
            "status": "missing",
            "build_status": "missing",
            "verification_status": "missing",
            "failure_class": "missing-report",
            "detail": f"missing handoff report: {path}",
            "evidence": [str(path)],
        }
    build_report = payload.get("build_report") if isinstance(payload.get("build_report"), dict) else {}
    install_report = payload.get("install_smoke_report") if isinstance(payload.get("install_smoke_report"), dict) else {}
    build_status = _status_token(build_report.get("status"))
    verification_status = _status_token(install_report.get("status")) if install_report else "not-run"
    failure_class = str(payload.get("failure_class") or "")
    overall = "pass" if failure_class == "verified-build" and build_status == "ok" and verification_status == "pass" else "fail"
    toolchain = build_report.get("resolved_msvc_toolchain") if isinstance(build_report.get("resolved_msvc_toolchain"), dict) else {}
    return {
        "lane": label,
        "surface": "unreal",
        "engine_version": str(payload.get("engine_version") or label.split("-", 1)[1]),
        "status": overall,
        "build_status": build_status or "unknown",
        "verification_status": verification_status,
        "failure_class": failure_class or ("verified-build" if overall == "pass" else "unknown"),
        "detail": _line_detail(
            build_report.get("detail"),
            build_report.get("raw_output"),
            install_report.get("status"),
            "build and install smoke passed" if overall == "pass" else "",
        ),
        "selected_compiler_version": toolchain.get("selected_version"),
        "selected_folder_version": toolchain.get("selected_folder_version"),
        "selection_reason": toolchain.get("selection_reason"),
        "evidence": [
            str(path),
            str(payload.get("build_report_json") or ""),
            str(payload.get("install_smoke_json") or ""),
        ],
    }


def summarize_unity(path: Path) -> dict[str, object]:
    payload = load_json(path)
    if payload is None:
        return {
            "lane": "unity-6000.5",
            "surface": "unity",
            "engine_version": "6000.5",
            "status": "missing",
            "build_status": "missing",
            "verification_status": "missing",
            "failure_class": "missing-report",
            "detail": f"missing handoff report: {path}",
            "evidence": [str(path)],
        }
    build_report = payload.get("build_report") if isinstance(payload.get("build_report"), dict) else {}
    build_status = _status_token(build_report.get("status"))
    failure_class = str(payload.get("failure_class") or "")
    overall = "pass" if failure_class == "verified-build" and build_status == "pass" else "fail"
    return {
        "lane": "unity-6000.5",
        "surface": "unity",
        "engine_version": str(build_report.get("unity_version") or "6000.5"),
        "status": overall,
        "build_status": build_status or "unknown",
        "verification_status": build_status or "unknown",
        "failure_class": failure_class or ("verified-build" if overall == "pass" else "unknown"),
        "detail": _line_detail(
            build_report.get("failure_tail"),
            build_report.get("log"),
            "scratch-project import smoke passed" if overall == "pass" else "",
        ),
        "evidence": [
            str(path),
            str(payload.get("build_report_json") or ""),
            str(payload.get("build_log") or ""),
        ],
    }


def summarize_godot(path: Path) -> dict[str, object]:
    payload = load_json(path)
    if payload is None:
        return {
            "lane": "godot-4.7",
            "surface": "godot",
            "engine_version": "4.7",
            "status": "missing",
            "build_status": "missing",
            "verification_status": "missing",
            "failure_class": "missing-report",
            "detail": f"missing handoff report: {path}",
            "evidence": [str(path)],
        }
    build_report = payload.get("build_report") if isinstance(payload.get("build_report"), dict) else {}
    build_status = _status_token(build_report.get("status"))
    failure_class = str(payload.get("failure_class") or "")
    overall = "pass" if failure_class == "verified-build" and build_status == "pass" else "fail"
    return {
        "lane": "godot-4.7",
        "surface": "godot",
        "engine_version": str(build_report.get("godot_version") or "4.7"),
        "status": overall,
        "build_status": build_status or "unknown",
        "verification_status": "n/a",
        "failure_class": failure_class or ("verified-build" if overall == "pass" else "unknown"),
        "detail": _line_detail(
            "native plugin build passed" if overall == "pass" else "",
            build_report.get("failure_tail"),
            build_report.get("log"),
        ),
        "evidence": [
            str(path),
            str(payload.get("build_report_json") or ""),
            str(payload.get("build_log") or ""),
        ],
    }


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    rows = [
        summarize_unreal("unreal-5.7", args.unreal_57.resolve()),
        summarize_unreal("unreal-5.8", args.unreal_58.resolve()),
        summarize_unity(args.unity.resolve()),
        summarize_godot(args.godot.resolve()),
    ]
    passing = [row for row in rows if row["status"] == "pass"]
    failing = [row for row in rows if row["status"] == "fail"]
    missing = [row for row in rows if row["status"] == "missing"]
    plugin_gate_status = "pass" if not failing and not missing else ("fail" if failing else "needs-attention")
    blocked_lanes = [str(row["lane"]) for row in [*failing, *missing]]
    example_gate_status = "ready" if plugin_gate_status == "pass" else "blocked"
    if missing:
        next_phase = "refresh-missing-plugin-proofs"
    elif failing:
        next_phase = "fix-plugin-proof-lanes"
    else:
        next_phase = "build-minimal-example-proofs"
    return {
        "schema": "packet_stoat.cesium_engine_matrix.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vendor": "cesium",
        "goal": {
            "final_goal": "Cesium is a proven cross-engine terrain/tiles dependency for FastDIS examples, with plugin build/import proof before example proof.",
            "phase_order": [
                "plugin_proofs",
                "minimal_example_proofs",
                "killer_app_showcase",
            ],
            "current_phase": "plugin_proofs" if plugin_gate_status != "pass" else "minimal_example_proofs",
            "next_phase": next_phase,
        },
        "overall_status": plugin_gate_status,
        "summary": {
            "lane_count": len(rows),
            "passing_count": len(passing),
            "failing_count": len(failing),
            "missing_count": len(missing),
        },
        "gates": {
            "plugin_proofs": {
                "status": plugin_gate_status,
                "required_lanes": [str(row["lane"]) for row in rows],
                "blocked_lanes": blocked_lanes,
            },
            "minimal_example_proofs": {
                "status": example_gate_status,
                "blocked_by": blocked_lanes,
                "required_after_plugin_gate": [
                    "cesium-backed Unreal minimal example",
                    "cesium-backed Unity minimal example",
                    "cesium-backed Godot minimal example",
                ],
            },
            "killer_app_showcase": {
                "status": "blocked" if example_gate_status != "ready" else "waiting-for-minimal-examples",
                "blocked_by": blocked_lanes if example_gate_status != "ready" else ["minimal_example_proofs"],
            },
        },
        "lanes": rows,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Cesium Engine Matrix",
        "",
        f"- vendor: `{payload['vendor']}`",
        f"- overall_status: `{payload['overall_status']}`",
        f"- generated_at: `{payload['generated_at']}`",
        f"- current_phase: `{payload['goal']['current_phase']}`",
        f"- next_phase: `{payload['goal']['next_phase']}`",
        "",
        str(payload["goal"]["final_goal"]),
        "",
        "## Gates",
        "",
        "| Gate | Status | Blocked By |",
        "| --- | --- | --- |",
        f"| `plugin_proofs` | `{payload['gates']['plugin_proofs']['status']}` | {', '.join(payload['gates']['plugin_proofs']['blocked_lanes']) or 'none'} |",
        f"| `minimal_example_proofs` | `{payload['gates']['minimal_example_proofs']['status']}` | {', '.join(payload['gates']['minimal_example_proofs']['blocked_by']) or 'none'} |",
        f"| `killer_app_showcase` | `{payload['gates']['killer_app_showcase']['status']}` | {', '.join(payload['gates']['killer_app_showcase']['blocked_by']) or 'none'} |",
        "",
        "## Plugin Lanes",
        "",
        "| Lane | Surface | Version | Status | Build | Verify | Why |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload.get("lanes", []):
        lines.append(
            f"| `{row['lane']}` | `{row['surface']}` | `{row['engine_version']}` | `{row['status']}` | "
            f"`{row['build_status']}` | `{row['verification_status']}` | {str(row['detail']).replace('|', '/')} |"
        )
    lines.extend(["", "## Evidence", ""])
    for row in payload.get("lanes", []):
        lines.append(f"- `{row['lane']}`")
        for evidence in row.get("evidence", []):
            if evidence:
                lines.append(f"  - `{evidence}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
