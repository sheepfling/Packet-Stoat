#!/usr/bin/env python3
"""Orientation inspection and calibration toolkit for fastdis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
sys.path.insert(0, str(TESTS_DIR / "oracles"))
import orientation_oracle as oracle


DEFAULT_FIXTURES = TESTS_DIR / "data" / "orientation_engine_cases.json"
DEFAULT_CONFIG_DIR = ROOT / "configs" / "orientation"


AXIS_VECTORS = {
    "positive_x": [1.0, 0.0, 0.0],
    "negative_x": [-1.0, 0.0, 0.0],
    "positive_y": [0.0, 1.0, 0.0],
    "negative_y": [0.0, -1.0, 0.0],
    "positive_z": [0.0, 0.0, 1.0],
    "negative_z": [0.0, 0.0, -1.0],
    "+X": [1.0, 0.0, 0.0],
    "-X": [-1.0, 0.0, 0.0],
    "+Y": [0.0, 1.0, 0.0],
    "-Y": [0.0, -1.0, 0.0],
    "+Z": [0.0, 0.0, 1.0],
    "-Z": [0.0, 0.0, -1.0],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    trace = sub.add_parser("trace")
    trace.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    trace.add_argument("--case", required=True)
    trace.add_argument("--config", required=True)
    trace.add_argument("--out")

    compare = sub.add_parser("compare")
    compare.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    compare.add_argument("--config", required=True)
    compare.add_argument("--target")
    compare.add_argument("--out")

    diff_trace = sub.add_parser("diff-trace")
    diff_trace.add_argument("before")
    diff_trace.add_argument("after")

    diagnose = sub.add_parser("diagnose")
    diagnose.add_argument("--report", required=True)

    solve = sub.add_parser("solve")
    solve.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    solve.add_argument("--config", required=True)
    solve.add_argument("--target")
    solve.add_argument("--search", default="asset_axes")
    solve.add_argument("--out")

    return parser.parse_args()


def load_structured(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Could not parse {path} as JSON and PyYAML is unavailable") from exc
        return yaml.safe_load(text)


def normalize_config_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return payload["config"] if "config" in payload and "target_frame" not in payload else payload


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def normalize(v: list[float]) -> list[float]:
    return oracle.normalize(v)


def dot(a: list[float], b: list[float]) -> float:
    return oracle.dot(a, b)


def cross(a: list[float], b: list[float]) -> list[float]:
    return oracle.cross(a, b)


def determinant(forward: list[float], right: list[float], up: list[float]) -> float:
    return oracle.determinant(forward, right, up)


def angle_between_deg(a: list[float], b: list[float]) -> float:
    da = normalize(a)
    db = normalize(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(da, db)))))


def matrix_from_columns(x: list[float], y: list[float], z: list[float]) -> list[list[float]]:
    return [
        [x[0], y[0], z[0]],
        [x[1], y[1], z[1]],
        [x[2], y[2], z[2]],
    ]


def transpose(m: list[list[float]]) -> list[list[float]]:
    return [[m[c][r] for c in range(3)] for r in range(3)]


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    out = [[0.0, 0.0, 0.0] for _ in range(3)]
    for r in range(3):
        for c in range(3):
            out[r][c] = sum(a[r][k] * b[k][c] for k in range(3))
    return out


def matvec(m: list[list[float]], v: list[float]) -> list[float]:
    return [sum(m[r][c] * v[c] for c in range(3)) for r in range(3)]


def rotation_matrix_euler_deg(yaw_deg: float, pitch_deg: float, roll_deg: float) -> list[list[float]]:
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    rz = [[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]]
    ry = [[cp, 0.0, sp], [0.0, 1.0, 0.0], [-sp, 0.0, cp]]
    rx = [[1.0, 0.0, 0.0], [0.0, cr, -sr], [0.0, sr, cr]]
    return matmul(matmul(rz, ry), rx)


def complete_basis(forward: list[float], up: list[float], handedness: str) -> tuple[list[float], list[float], list[float]]:
    f = AXIS_VECTORS[forward] if isinstance(forward, str) else forward
    u = AXIS_VECTORS[up] if isinstance(up, str) else up
    if handedness == "left":
        r = cross(u, f)
    else:
        r = cross(f, u)
    return normalize(f), normalize(r), normalize(u)


def local_axis_to_engine_vector(axis_name: str) -> list[float]:
    if axis_name not in AXIS_VECTORS:
        raise KeyError(f"unknown axis target {axis_name}")
    return AXIS_VECTORS[axis_name]


def map_enu_to_engine(v_enu: list[float], axis_map: dict[str, str]) -> list[float]:
    east_axis = local_axis_to_engine_vector(axis_map["east"])
    north_axis = local_axis_to_engine_vector(axis_map["north"])
    up_axis = local_axis_to_engine_vector(axis_map["up"])
    return [
        v_enu[0] * east_axis[0] + v_enu[1] * north_axis[0] + v_enu[2] * up_axis[0],
        v_enu[0] * east_axis[1] + v_enu[1] * north_axis[1] + v_enu[2] * up_axis[1],
        v_enu[0] * east_axis[2] + v_enu[1] * north_axis[2] + v_enu[2] * up_axis[2],
    ]


def body_selector(stage2: dict[str, list[float]], selector: str) -> list[float]:
    if selector == "body_forward":
        return stage2["forward_enu"]
    if selector == "body_right":
        return stage2["right_enu"]
    if selector == "body_up":
        return stage2["up_enu"]
    if selector == "negative_body_down":
        return stage2["up_enu"]
    if selector == "negative_body_right":
        return [-value for value in stage2["right_enu"]]
    if selector == "negative_body_forward":
        return [-value for value in stage2["forward_enu"]]
    raise KeyError(f"unknown body selector {selector}")


def actor_basis_from_visible_basis(forward: list[float], right: list[float], up: list[float], engine: str) -> dict[str, list[float]]:
    engine = engine.lower()
    if engine == "unreal":
        return {"x": forward, "y": right, "z": up}
    if engine == "godot":
        return {"x": right, "y": up, "z": [-value for value in forward]}
    if engine == "unity":
        return {"x": right, "y": up, "z": forward}
    raise KeyError(f"unsupported engine {engine}")


def visible_basis_from_actor_basis(actor_basis: dict[str, list[float]], engine: str) -> dict[str, list[float]]:
    engine = engine.lower()
    if engine == "unreal":
        return {"forward": actor_basis["x"], "right": actor_basis["y"], "up": actor_basis["z"]}
    if engine == "godot":
        return {"forward": [-value for value in actor_basis["z"]], "right": actor_basis["x"], "up": actor_basis["y"]}
    if engine == "unity":
        return {"forward": actor_basis["z"], "right": actor_basis["x"], "up": actor_basis["y"]}
    raise KeyError(f"unsupported engine {engine}")


def dot_matrix(forward: list[float], right: list[float], up: list[float]) -> list[list[float]]:
    return [
        [dot(forward, forward), dot(forward, right), dot(forward, up)],
        [dot(right, forward), dot(right, right), dot(right, up)],
        [dot(up, forward), dot(up, right), dot(up, up)],
    ]


def make_stage(forward: list[float], right: list[float], up: list[float]) -> dict[str, Any]:
    det = determinant(forward, right, up)
    return {
        "forward": [float(v) for v in forward],
        "right": [float(v) for v in right],
        "up": [float(v) for v in up],
        "determinant": det,
        "handedness": "right" if det >= 0.0 else "left",
        "dot_matrix": dot_matrix(forward, right, up),
    }


def load_case(fixtures_path: Path, case_name: str) -> dict[str, Any]:
    fixture = load_structured(fixtures_path)
    for case in fixture["cases"]:
        if case["name"] == case_name:
            return case
    raise KeyError(f"case not found: {case_name}")


def desired_visible_basis(case: dict[str, Any], target: str) -> dict[str, list[float]]:
    expected = case["expected"]
    target = target.lower()
    if target == "unreal":
        return {
            "forward": expected["unreal_forward"],
            "right": expected["unreal_right"],
            "up": expected["unreal_up"],
        }
    if target == "godot":
        return {
            "forward": expected["godot_forward"],
            "right": expected["godot_right"],
            "up": expected["godot_up"],
        }
    if target == "unity":
        return {
            "forward": expected["unity_forward"],
            "right": expected["unity_right"],
            "up": expected["unity_up"],
        }
    raise KeyError(f"unsupported target {target}")


def compute_trace(case: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    target = config["target_frame"]["engine"].lower()
    dis_deg = case["expected"]["dis_deg"]
    stage1_ecef = oracle.dis_psi_theta_phi_to_body_frd_ecef(dis_deg["psi"], dis_deg["theta"], dis_deg["phi"])
    stage1 = make_stage(stage1_ecef["forward_ecef"], stage1_ecef["right_ecef"], [-value for value in stage1_ecef["down_ecef"]])
    stage2_enu = oracle.body_frd_ecef_to_body_fru_enu(stage1_ecef, float(case["lat_deg"]), float(case["lon_deg"]))
    stage2 = make_stage(stage2_enu["forward_enu"], stage2_enu["right_enu"], stage2_enu["up_enu"])

    body_to_engine = config["body_to_engine"]
    stage3_forward = normalize(map_enu_to_engine(body_selector(stage2_enu, body_to_engine["forward"]), config["target_frame"]["axis_map"]))
    stage3_right = normalize(map_enu_to_engine(body_selector(stage2_enu, body_to_engine["right"]), config["target_frame"]["axis_map"]))
    stage3_up = normalize(map_enu_to_engine(body_selector(stage2_enu, body_to_engine["up"]), config["target_frame"]["axis_map"]))
    stage3 = make_stage(stage3_forward, stage3_right, stage3_up)

    actor_basis = actor_basis_from_visible_basis(stage3_forward, stage3_right, stage3_up, target)
    actor_matrix = matrix_from_columns(actor_basis["x"], actor_basis["y"], actor_basis["z"])

    handedness = config["target_frame"]["handedness"]
    asset_forward, asset_right, asset_up = complete_basis(
        config["asset"]["forward_axis"],
        config["asset"]["up_axis"],
        handedness,
    )
    correction_cfg = config.get("correction", {})
    correction_enabled = bool(correction_cfg.get("enabled", False))
    if correction_enabled:
        euler = correction_cfg.get("post_engine_euler_deg", {})
        correction_matrix = rotation_matrix_euler_deg(
            float(euler.get("yaw", 0.0)),
            float(euler.get("pitch", 0.0)),
            float(euler.get("roll", 0.0)),
        )
    else:
        correction_matrix = rotation_matrix_euler_deg(0.0, 0.0, 0.0)

    asset_forward_corr = normalize(matvec(correction_matrix, asset_forward))
    asset_right_corr = normalize(matvec(correction_matrix, asset_right))
    asset_up_corr = normalize(matvec(correction_matrix, asset_up))

    mesh_forward = normalize(matvec(actor_matrix, asset_forward_corr))
    mesh_right = normalize(matvec(actor_matrix, asset_right_corr))
    mesh_up = normalize(matvec(actor_matrix, asset_up_corr))
    stage4 = make_stage(mesh_forward, mesh_right, mesh_up)

    visible = visible_basis_from_actor_basis(actor_basis, target)

    return {
        "case": case["name"],
        "target": target,
        "config_hash": config_hash(config),
        "config": config,
        "input": {
            "entity_id": [100, 1, 1],
            "dis_psi_theta_phi_deg": dis_deg,
            "georeference": {
                "lat_deg": case["lat_deg"],
                "lon_deg": case["lon_deg"],
                "height_m": case["height_m"],
            },
        },
        "stage_1_dis_body_ecef": stage1,
        "stage_2_body_enu": stage2,
        "stage_3_engine_basis_before_asset": stage3,
        "actor_basis": actor_basis,
        "engine_visible_basis": visible,
        "stage_4_asset_corrected_basis": stage4,
        "asset_basis": {
            "forward_axis": config["asset"]["forward_axis"],
            "up_axis": config["asset"]["up_axis"],
            "corrected_forward_local": asset_forward_corr,
            "corrected_right_local": asset_right_corr,
            "corrected_up_local": asset_up_corr,
        },
        "final": {
            "position_engine": None,
            "forward_engine": stage4["forward"],
            "right_engine": stage4["right"],
            "up_engine": stage4["up"],
        },
    }


def failure_signature(result: dict[str, Any]) -> str | None:
    f = result["forward_angle_error_deg"]
    r = result["right_angle_error_deg"]
    u = result["up_angle_error_deg"]
    if result["determinant_error"] > 1e-3 and not result["handedness_ok"]:
        return "determinant_negative"
    if f > 179.0 and r > 179.0 and u < 1.0:
        if result["engine_stage_max_axis_error_deg"] < 1.0:
            return "asset_front_mismatch"
        return "forward_error_180"
    if 80.0 < f < 100.0 and 80.0 < r < 100.0 and u < 1.0:
        return "north_east_swap"
    if result["engine_stage_max_axis_error_deg"] < 1.0 and result["asset_stage_max_axis_error_deg"] > 45.0:
        return "asset_front_mismatch"
    if f < 1.0 and r > 5.0 and u > 5.0:
        return "roll_or_asset_up_issue"
    if r < 1.0 and f > 5.0 and u > 5.0:
        return "pitch_or_forward_up_issue"
    return None


def case_compare_result(case: dict[str, Any], config: dict[str, Any], target: str | None = None) -> dict[str, Any]:
    trace = compute_trace(case, config)
    target_name = target or config["target_frame"]["engine"].lower()
    expected = desired_visible_basis(case, target_name)
    engine_visible = trace["engine_visible_basis"]
    asset_stage = trace["stage_4_asset_corrected_basis"]
    f_err = angle_between_deg(asset_stage["forward"], expected["forward"])
    r_err = angle_between_deg(asset_stage["right"], expected["right"])
    u_err = angle_between_deg(asset_stage["up"], expected["up"])
    engine_f_err = angle_between_deg(engine_visible["forward"], expected["forward"])
    engine_r_err = angle_between_deg(engine_visible["right"], expected["right"])
    engine_u_err = angle_between_deg(engine_visible["up"], expected["up"])
    out = {
        "case": case["name"],
        "config_hash": trace["config_hash"],
        "forward_angle_error_deg": f_err,
        "right_angle_error_deg": r_err,
        "up_angle_error_deg": u_err,
        "max_axis_error_deg": max(f_err, r_err, u_err),
        "engine_stage_max_axis_error_deg": max(engine_f_err, engine_r_err, engine_u_err),
        "asset_stage_max_axis_error_deg": max(f_err, r_err, u_err),
        "orthogonality_error": max(
            abs(asset_stage["dot_matrix"][0][1]),
            abs(asset_stage["dot_matrix"][0][2]),
            abs(asset_stage["dot_matrix"][1][2]),
        ),
        "expected_determinant": determinant(
            expected["forward"],
            expected["right"],
            expected["up"],
        ),
        "determinant_error": 0.0,
        "handedness_ok": False,
        "expected_visible_basis": expected,
        "engine_visible_basis": engine_visible,
        "asset_stage": asset_stage,
        "failure_signature": None,
        "pass": False,
        "trace": trace,
    }
    out["determinant_error"] = abs(asset_stage["determinant"] - out["expected_determinant"])
    out["handedness_ok"] = (asset_stage["determinant"] >= 0.0) == (out["expected_determinant"] >= 0.0)
    out["failure_signature"] = failure_signature(out)
    out["pass"] = out["max_axis_error_deg"] <= 0.01 and out["determinant_error"] <= 1e-5 and out["orthogonality_error"] <= 1e-5
    return out


def compare_payload(fixtures_path: Path, config: dict[str, Any], target: str | None = None) -> dict[str, Any]:
    fixture_path = fixtures_path.resolve()
    fixture = load_structured(fixture_path)
    target_name = (target or config["target_frame"]["engine"]).lower()
    results = [case_compare_result(case, config, target_name) for case in fixture["cases"]]
    return {
        "schema": "fastdis.orientation_compare.v1",
        "target": target_name,
        "config_hash": config_hash(config),
        "config": config,
        "fixtures": str(fixture_path.relative_to(ROOT)),
        "results": results,
        "summary": {
            "case_count": len(results),
            "pass_count": sum(1 for item in results if item["pass"]),
            "max_axis_error_deg": max(item["max_axis_error_deg"] for item in results),
        },
    }


def format_compare_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Orientation Compare Report",
        "",
        f"- target: `{payload['target']}`",
        f"- config_hash: `{payload['config_hash']}`",
        "",
        "| case | fwd_err | right_err | up_err | det_err | signature | pass |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['case']} | {item['forward_angle_error_deg']:.4f} | {item['right_angle_error_deg']:.4f} | "
            f"{item['up_angle_error_deg']:.4f} | {item['determinant_error']:.6f} | "
            f"{item['failure_signature'] or ''} | {'PASS' if item['pass'] else 'FAIL'} |"
        )
    return "\n".join(lines) + "\n"


def diagnose_payload(report: dict[str, Any]) -> dict[str, Any]:
    failures = [item for item in report["results"] if not item["pass"]]
    counts: dict[str, int] = {}
    for item in failures:
        sig = item["failure_signature"] or "unknown"
        counts[sig] = counts.get(sig, 0) + 1
    top = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None
    suggestions = {
        "asset_front_mismatch": "Check asset.forward_axis / asset.up_axis in the config.",
        "north_east_swap": "Check target_frame.axis_map for east/north mapping.",
        "forward_error_180": "Check forward-axis sign or a hidden 180-degree yaw correction.",
        "determinant_negative": "A reflection was introduced; inspect handedness or one-axis sign flips.",
        "roll_or_asset_up_issue": "Inspect roll sign and asset up-axis assumptions.",
        "pitch_or_forward_up_issue": "Inspect pitch sign and body forward/up mapping.",
    }
    return {
        "schema": "fastdis.orientation_diagnose.v1",
        "target": report["target"],
        "config_hash": report["config_hash"],
        "config": report.get("config"),
        "failure_counts": counts,
        "most_likely_issue": top,
        "suggestion": suggestions.get(top),
    }


def asset_axis_candidates() -> list[tuple[str, str]]:
    axes = ["positive_x", "negative_x", "positive_y", "negative_y", "positive_z", "negative_z"]
    pairs: list[tuple[str, str]] = []
    for forward in axes:
        for up in axes:
            if forward.split("_")[-1] == up.split("_")[-1]:
                continue
            pairs.append((forward, up))
    return pairs


def solve_payload(fixtures_path: Path, base_config: dict[str, Any], target: str | None, search: str) -> dict[str, Any]:
    target_name = (target or base_config["target_frame"]["engine"]).lower()
    variants: list[dict[str, Any]] = []
    if "asset_axes" in search:
        for forward_axis, up_axis in asset_axis_candidates():
            candidate = json.loads(json.dumps(base_config))
            candidate["asset"]["forward_axis"] = forward_axis
            candidate["asset"]["up_axis"] = up_axis
            payload = compare_payload(fixtures_path, candidate, target_name)
            score = payload["summary"]["max_axis_error_deg"]
            variants.append(
                {
                    "variant": {
                        "asset.forward_axis": forward_axis,
                        "asset.up_axis": up_axis,
                    },
                    "score": score,
                    "max_axis_error_deg": score,
                    "pass_count": payload["summary"]["pass_count"],
                    "config_hash": payload["config_hash"],
                }
            )
    variants.sort(key=lambda item: (item["score"], -item["pass_count"]))
    return {
        "schema": "fastdis.orientation_solve.v1",
        "target": target_name,
        "base_config_hash": config_hash(base_config),
        "base_config": base_config,
        "search": search,
        "candidates": variants[:12],
    }


def diff_trace_payload(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    diffs: list[dict[str, Any]] = []
    stages = [
        "stage_1_dis_body_ecef",
        "stage_2_body_enu",
        "stage_3_engine_basis_before_asset",
        "stage_4_asset_corrected_basis",
    ]
    for stage in stages:
        for axis in ("forward", "right", "up"):
            b = before[stage][axis]
            a = after[stage][axis]
            angle = angle_between_deg(b, a)
            if angle > 1e-9:
                diffs.append(
                    {
                        "path": f"{stage}.{axis}",
                        "before": b,
                        "after": a,
                        "angular_difference_deg": angle,
                    }
                )
    return {
        "schema": "fastdis.orientation_diff_trace.v1",
        "before_config_hash": before["config_hash"],
        "before_config": before.get("config"),
        "after_config_hash": after["config_hash"],
        "after_config": after.get("config"),
        "differences": diffs,
    }


def main() -> int:
    args = parse_args()
    if args.command == "trace":
        config = normalize_config_payload(load_structured(Path(args.config)))
        case = load_case(Path(args.fixtures), args.case)
        payload = compute_trace(case, config)
        if args.out:
            dump_json(Path(args.out), payload)
        else:
            print(json.dumps(payload, indent=2))
        return 0
    if args.command == "compare":
        config = normalize_config_payload(load_structured(Path(args.config)))
        payload = compare_payload(Path(args.fixtures), config, args.target)
        if args.out:
            out = Path(args.out)
            if out.suffix.lower() == ".md":
                out.write_text(format_compare_markdown(payload), encoding="utf-8")
            else:
                dump_json(out, payload)
        else:
            print(json.dumps(payload, indent=2))
        return 0 if payload["summary"]["pass_count"] == payload["summary"]["case_count"] else 1
    if args.command == "diagnose":
        report = load_structured(Path(args.report))
        payload = diagnose_payload(report)
        print(json.dumps(payload, indent=2))
        return 0
    if args.command == "solve":
        config = normalize_config_payload(load_structured(Path(args.config)))
        payload = solve_payload(Path(args.fixtures), config, args.target, args.search)
        if args.out:
            out = Path(args.out)
            if out.suffix.lower() == ".md":
                lines = ["# Orientation Solve Report", ""]
                for index, item in enumerate(payload["candidates"], start=1):
                    lines.append(
                        f"{index}. forward={item['variant']['asset.forward_axis']} "
                        f"up={item['variant']['asset.up_axis']} "
                        f"max_err={item['max_axis_error_deg']:.4f} pass_count={item['pass_count']}"
                    )
                out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            else:
                dump_json(out, payload)
        else:
            print(json.dumps(payload, indent=2))
        return 0
    if args.command == "diff-trace":
        before = load_structured(Path(args.before))
        after = load_structured(Path(args.after))
        payload = diff_trace_payload(before, after)
        print(json.dumps(payload, indent=2))
        return 0
    raise RuntimeError(f"unknown command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
