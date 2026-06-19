#!/usr/bin/env python3
"""Generate deterministic orientation projection images and semantic compare reports."""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import ImageChops
from PIL import ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VISUAL_CASES = ROOT / "tests" / "data" / "orientation_visual_cases.json"


AXIS_COLORS = {
    "forward": (235, 58, 58),
    "right": (52, 210, 84),
    "up": (72, 118, 255),
}
EXPECTED_COLOR = (230, 230, 230)
BACKGROUND = (22, 24, 28)
GRID_COLOR = (58, 62, 68)
TEXT_COLOR = (240, 240, 240)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare", required=True, help="Orientation compare JSON payload")
    parser.add_argument("--visual-cases", default=str(DEFAULT_VISUAL_CASES))
    parser.add_argument("--label", required=True, help="Stable label for the generated artifacts")
    parser.add_argument("--out-dir", required=True, help="Directory that will receive images, sidecars, and reports")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def normalize(vec: list[float]) -> list[float]:
    mag = math.sqrt(sum(value * value for value in vec))
    if mag == 0.0:
        return [0.0, 0.0, 0.0]
    return [value / mag for value in vec]


def dot(a: list[float], b: list[float]) -> float:
    return sum(ax * bx for ax, bx in zip(a, b))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def angle_deg_2d(a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    amag = math.hypot(ax, ay)
    bmag = math.hypot(bx, by)
    if amag == 0.0 or bmag == 0.0:
        return 0.0
    return math.degrees(math.acos(clamp((ax * bx + ay * by) / (amag * bmag), -1.0, 1.0)))


def project_vector(vec: list[float], camera: dict[str, Any], axis_scale_px: float) -> tuple[float, float]:
    right = normalize(camera["screen_right"])
    up = normalize(camera["screen_up"])
    return (
        dot(vec, right) * axis_scale_px,
        -dot(vec, up) * axis_scale_px,
    )


def endpoint(origin: tuple[float, float], delta: tuple[float, float]) -> tuple[float, float]:
    return (origin[0] + delta[0], origin[1] + delta[1])


def render_projection_image(
    *,
    origin: tuple[float, float],
    expected_lines: dict[str, tuple[tuple[float, float], tuple[float, float]]],
    actual_lines: dict[str, tuple[tuple[float, float], tuple[float, float]]],
    width: int,
    height: int,
    title: str,
    status: str,
    output_path: Path,
) -> None:
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.line((0, origin[1], width, origin[1]), fill=GRID_COLOR, width=1)
    draw.line((origin[0], 0, origin[0], height), fill=GRID_COLOR, width=1)

    for axis in ("forward", "right", "up"):
        start, end = expected_lines[axis]
        draw.line((start[0], start[1], end[0], end[1]), fill=EXPECTED_COLOR, width=2)
    for axis in ("forward", "right", "up"):
        start, end = actual_lines[axis]
        draw.line((start[0], start[1], end[0], end[1]), fill=AXIS_COLORS[axis], width=5)

    draw.text((12, 10), title, fill=TEXT_COLOR)
    draw.text((12, 30), status, fill=TEXT_COLOR)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def image_diff_metrics(path_a: Path, path_b: Path) -> dict[str, float]:
    with Image.open(path_a) as image_a, Image.open(path_b) as image_b:
        diff = ImageChops.difference(image_a.convert("RGB"), image_b.convert("RGB"))
        hist = diff.histogram()
        total = sum(hist)
        if total == 0:
            return {"mean_abs_error": 0.0, "max_channel_error": 0.0}
        weighted = sum(index % 256 * count for index, count in enumerate(hist))
        mean_abs_error = weighted / total
        max_channel_error = float(max(index % 256 for index, count in enumerate(hist) if count))
        return {
            "mean_abs_error": mean_abs_error,
            "max_channel_error": max_channel_error,
        }


def compare_case(
    *,
    case_result: dict[str, Any],
    camera: dict[str, Any],
    image_meta: dict[str, Any],
    engine: str,
    out_dir: Path,
    label: str,
) -> dict[str, Any]:
    axis_scale = float(image_meta["axis_scale_px"])
    origin = (float(image_meta["origin"][0]), float(image_meta["origin"][1]))
    width = int(image_meta["width"])
    height = int(image_meta["height"])

    expected_basis = case_result["expected_visible_basis"]
    actual_basis = case_result["asset_stage"]
    expected_lines: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {}
    actual_lines: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {}
    sidecar_expected: dict[str, list[list[float]]] = {}
    sidecar_actual: dict[str, list[list[float]]] = {}
    max_endpoint_error = 0.0
    max_screen_angle = 0.0

    for axis in ("forward", "right", "up"):
        expected_delta = project_vector(expected_basis[axis], camera, axis_scale)
        actual_delta = project_vector(actual_basis[axis], camera, axis_scale)
        expected_end = endpoint(origin, expected_delta)
        actual_end = endpoint(origin, actual_delta)
        expected_lines[axis] = (origin, expected_end)
        actual_lines[axis] = (origin, actual_end)
        sidecar_expected[f"{axis}_screen"] = [[origin[0], origin[1]], [expected_end[0], expected_end[1]]]
        sidecar_actual[f"{axis}_screen"] = [[origin[0], origin[1]], [actual_end[0], actual_end[1]]]
        max_endpoint_error = max(max_endpoint_error, math.dist(expected_end, actual_end))
        max_screen_angle = max(max_screen_angle, angle_deg_2d(expected_delta, actual_delta))

    base_name = f"{engine}_{label}_{case_result['case']}_{camera['name']}"
    expected_path = out_dir / "baselines" / f"{base_name}_expected.png"
    actual_path = out_dir / "renders" / f"{base_name}_actual.png"
    render_projection_image(
        origin=origin,
        expected_lines=expected_lines,
        actual_lines=expected_lines,
        width=width,
        height=height,
        title=f"{engine} {case_result['case']} {camera['name']}",
        status="EXPECTED",
        output_path=expected_path,
    )
    render_projection_image(
        origin=origin,
        expected_lines=expected_lines,
        actual_lines=actual_lines,
        width=width,
        height=height,
        title=f"{engine} {case_result['case']} {camera['name']}",
        status="PASS" if case_result["pass"] else f"FAIL {case_result.get('failure_signature') or 'unknown'}",
        output_path=actual_path,
    )

    sidecar = {
        "schema": "fastdis.orientation_visual_sidecar.v1",
        "engine": engine,
        "label": label,
        "case": case_result["case"],
        "camera": camera["name"],
        "config_hash": case_result["config_hash"],
        "expected": sidecar_expected,
        "actual": sidecar_actual,
        "actual_engine_basis": {
            "forward": actual_basis["forward"],
            "right": actual_basis["right"],
            "up": actual_basis["up"],
        },
        "max_angle_error_deg": case_result["max_axis_error_deg"],
        "visual_projection_error_px": max_endpoint_error,
        "visual_projection_angle_error_deg": max_screen_angle,
        "failure_signature": case_result.get("failure_signature"),
        "pass": case_result["pass"] and max_screen_angle <= 0.01,
    }
    sidecar_path = out_dir / "sidecars" / f"{base_name}.json"
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

    diff_metrics = image_diff_metrics(expected_path, actual_path)
    return {
        "case": case_result["case"],
        "camera": camera["name"],
        "expected_image": display_path(expected_path),
        "actual_image": display_path(actual_path),
        "sidecar": display_path(sidecar_path),
        "visual_projection_error_px": max_endpoint_error,
        "visual_projection_angle_error_deg": max_screen_angle,
        "mean_abs_error": diff_metrics["mean_abs_error"],
        "max_channel_error": diff_metrics["max_channel_error"],
        "failure_signature": case_result.get("failure_signature"),
        "pass": sidecar["pass"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Orientation Visual Projection Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- engine: `{report['engine']}`",
        f"- label: `{report['label']}`",
        f"- config_hash: `{report['config_hash']}`",
        "",
        "| case | camera | projection_err_px | screen_angle_deg | image_mae | signature | pass |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for item in report["results"]:
        lines.append(
            f"| {item['case']} | {item['camera']} | {item['visual_projection_error_px']:.3f} | "
            f"{item['visual_projection_angle_error_deg']:.3f} | {item['mean_abs_error']:.3f} | "
            f"{item['failure_signature'] or ''} | {'PASS' if item['pass'] else 'FAIL'} |"
        )
    return "\n".join(lines) + "\n"


def run_from_namespace(args: argparse.Namespace) -> int:
    compare_payload = load_json(Path(args.compare))
    visual_cases = load_json(Path(args.visual_cases))
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    enabled_cases = set(visual_cases["cases"])
    results: list[dict[str, Any]] = []
    for case_result in compare_payload["results"]:
        if case_result["case"] not in enabled_cases:
            continue
        for camera in visual_cases["cameras"]:
            results.append(
                compare_case(
                    case_result=case_result,
                    camera=camera,
                    image_meta=visual_cases["image"],
                    engine=str(compare_payload["target"]),
                    out_dir=out_dir,
                    label=args.label,
                )
            )

    report = {
        "schema": "fastdis.orientation_visual_projection_report.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "engine": compare_payload["target"],
        "label": args.label,
        "config_hash": compare_payload["config_hash"],
        "config": compare_payload.get("config"),
        "compare_source": display_path(Path(args.compare).resolve()),
        "visual_cases": display_path(Path(args.visual_cases).resolve()),
        "results": results,
        "summary": {
            "image_count": len(results),
            "pass_count": sum(1 for item in results if item["pass"]),
            "max_projection_error_px": max((item["visual_projection_error_px"] for item in results), default=0.0),
            "max_screen_angle_error_deg": max((item["visual_projection_angle_error_deg"] for item in results), default=0.0),
        },
    }

    json_path = out_dir / f"{compare_payload['target']}_{args.label}_projection_report.json"
    md_path = out_dir / f"{compare_payload['target']}_{args.label}_projection_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(md_path)}")
    return 0 if report["summary"]["pass_count"] == report["summary"]["image_count"] else 1


def main() -> int:
    return run_from_namespace(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
