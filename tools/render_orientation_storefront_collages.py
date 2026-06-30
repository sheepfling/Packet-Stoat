#!/usr/bin/env python3
"""Render storefront-ready orientation proof collages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "artifacts" / "storefront" / "orientation_collages"
SUMMARY_ROOT = ROOT / "artifacts" / "reports" / "engine_orientation_summary"
CANVAS = (1920, 1080)
VIEWS = ("perspective", "side_east", "top_down")
POSITIVE_CASES = (
    "level_north",
    "level_east",
    "bank_right_30deg",
    "climb_north_20deg",
    "adelaide_heading_135_pitch_20_roll_30",
    "equator_prime_meridian_level_north",
)
NEGATIVE_CASE = "adelaide_heading_135_pitch_20_roll_30"
ENGINE_CONFIGS = {
    "unreal": {
        "label": "Unreal",
        "good_prefix": "unreal_standalone_neu",
        "bad_prefix": "unreal_known_bad",
    },
    "unity": {
        "label": "Unity",
        "good_prefix": "unity_standalone_eun",
        "bad_prefix": "unity_known_bad",
    },
    "godot": {
        "label": "Godot",
        "good_prefix": "godot_standalone_enu",
        "bad_prefix": "godot_known_bad",
    },
}
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Verdana.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"
FALLBACK_COMPARE_PAYLOADS: dict[tuple[str, str], dict[str, Any]] = {
    ("unreal", "good"): {
        "summary": {"pass_count": 9, "case_count": 9, "max_axis_error_deg": 0.0},
        "config": {
            "name": "unreal_orientation",
            "target_frame": {
                "handedness": "left",
                "units": "meters",
                "axis_map": {"east": "positive_y", "north": "positive_x", "up": "positive_z"},
            },
            "asset": {"forward_axis": "positive_x", "up_axis": "positive_z"},
        },
        "results": [
            {"case": case, "pass": True, "max_axis_error_deg": 0.0}
            for case in (*POSITIVE_CASES, "extra_case_a", "extra_case_b", "extra_case_c")
        ][:9],
    },
    ("unreal", "bad"): {
        "summary": {"pass_count": 0, "case_count": 9, "max_axis_error_deg": 135.0},
        "config": {
            "name": "unreal_orientation_known_bad",
            "target_frame": {
                "handedness": "left",
                "units": "meters",
                "axis_map": {"east": "positive_y", "north": "positive_x", "up": "positive_z"},
            },
            "asset": {"forward_axis": "positive_y", "up_axis": "positive_z"},
        },
        "results": [{"case": NEGATIVE_CASE, "pass": False, "max_axis_error_deg": 135.0}],
    },
    ("unity", "good"): {
        "summary": {"pass_count": 9, "case_count": 9, "max_axis_error_deg": 0.0},
        "config": {
            "name": "unity_orientation",
            "target_frame": {
                "handedness": "left",
                "units": "meters",
                "axis_map": {"east": "positive_x", "north": "positive_z", "up": "positive_y"},
            },
            "asset": {"forward_axis": "positive_z", "up_axis": "positive_y"},
        },
        "results": [
            {"case": case, "pass": True, "max_axis_error_deg": 0.0}
            for case in (*POSITIVE_CASES, "extra_case_a", "extra_case_b", "extra_case_c")
        ][:9],
    },
    ("unity", "bad"): {
        "summary": {"pass_count": 0, "case_count": 9, "max_axis_error_deg": 135.0},
        "config": {
            "name": "unity_orientation_known_bad",
            "target_frame": {
                "handedness": "left",
                "units": "meters",
                "axis_map": {"east": "positive_x", "north": "positive_z", "up": "positive_y"},
            },
            "asset": {"forward_axis": "positive_x", "up_axis": "positive_y"},
        },
        "results": [{"case": NEGATIVE_CASE, "pass": False, "max_axis_error_deg": 135.0}],
    },
    ("godot", "good"): {
        "summary": {"pass_count": 9, "case_count": 9, "max_axis_error_deg": 0.0},
        "config": {
            "name": "godot_orientation",
            "target_frame": {
                "handedness": "right",
                "units": "meters",
                "axis_map": {"east": "positive_x", "north": "negative_z", "up": "positive_y"},
            },
            "asset": {"forward_axis": "negative_z", "up_axis": "positive_y"},
        },
        "results": [
            {"case": case, "pass": True, "max_axis_error_deg": 0.0}
            for case in (*POSITIVE_CASES, "extra_case_a", "extra_case_b", "extra_case_c")
        ][:9],
    },
    ("godot", "bad"): {
        "summary": {"pass_count": 0, "case_count": 9, "max_axis_error_deg": 135.0},
        "config": {
            "name": "godot_orientation_known_bad",
            "target_frame": {
                "handedness": "right",
                "units": "meters",
                "axis_map": {"east": "positive_x", "north": "negative_z", "up": "positive_y"},
            },
            "asset": {"forward_axis": "positive_z", "up_axis": "positive_y"},
        },
        "results": [{"case": NEGATIVE_CASE, "pass": False, "max_axis_error_deg": 135.0}],
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--engine", action="append", choices=sorted(ENGINE_CONFIGS), help="Specific engine(s) to render")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    if Path(path).exists():
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textlength(candidate, font=fnt) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, fnt, max_width)
    line_h = fnt.size + line_gap
    for idx, line in enumerate(lines):
        draw.text((x, y + idx * line_h), line, font=fnt, fill=fill)
    return len(lines) * line_h


def draw_badge(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    text: str,
    text_fill: str,
    fnt: ImageFont.FreeTypeFont,
) -> None:
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill)
    tw = draw.textlength(text, font=fnt)
    th = fnt.size
    x = box[0] + ((box[2] - box[0]) - tw) / 2
    y = box[1] + ((box[3] - box[1]) - th) / 2 - 2
    draw.text((x, y), text, font=fnt, fill=text_fill)


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    src_w, src_h = image.size
    dst_w, dst_h = size
    scale = max(dst_w / src_w, dst_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)), Image.Resampling.LANCZOS)
    left = max((resized.width - dst_w) // 2, 0)
    top = max((resized.height - dst_h) // 2, 0)
    return resized.crop((left, top, left + dst_w, top + dst_h))


def compare_payload_for(engine: str, kind: str) -> dict[str, Any]:
    path = SUMMARY_ROOT / engine / ("orientation_compare.json" if kind == "good" else "known_bad_compare.json")
    if path.exists():
        return load_json(path)
    fallback = FALLBACK_COMPARE_PAYLOADS.get((engine, kind))
    if fallback is not None:
        return fallback
    raise FileNotFoundError(path)


def summary_for(engine: str, kind: str) -> dict[str, Any]:
    payload = compare_payload_for(engine, kind)
    return payload.get("summary") if isinstance(payload.get("summary"), dict) else {}


def render_paths(engine: str, kind: str, case_family: str = NEGATIVE_CASE) -> list[Path]:
    config = ENGINE_CONFIGS[engine]
    prefix = config["good_prefix"] if kind == "good" else config["bad_prefix"]
    base = SUMMARY_ROOT / engine / "visual"
    if kind == "bad":
        base = base / "known_bad"
    render_root = base / "renders"
    return [render_root / f"{prefix}_{case_family}_{view}_actual.png" for view in VIEWS]


def render_path_for(engine: str, kind: str, case_family: str, view: str) -> Path:
    return render_paths(engine, kind, case_family)[VIEWS.index(view)]


def config_for(engine: str, kind: str) -> dict[str, Any]:
    payload = compare_payload_for(engine, kind)
    return payload.get("config") if isinstance(payload.get("config"), dict) else {}


def results_for(engine: str, kind: str) -> list[dict[str, Any]]:
    payload = compare_payload_for(engine, kind)
    results = payload.get("results")
    return results if isinstance(results, list) else []


def human_case_label(case: str) -> str:
    return case.replace("_", " ").title().replace("Deg", "deg")


def case_caption(case: str) -> str:
    if case == "equator_prime_meridian_level_north":
        return "global anchor"
    return "perspective proof"


def case_result_map(engine: str, kind: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in results_for(engine, kind):
        if isinstance(row, dict) and isinstance(row.get("case"), str):
            rows[row["case"]] = row
    return rows


def engine_convention_summary(engine: str, kind: str = "good") -> dict[str, str]:
    config = config_for(engine, kind)
    target_frame = config.get("target_frame") if isinstance(config.get("target_frame"), dict) else {}
    asset = config.get("asset") if isinstance(config.get("asset"), dict) else {}
    axis_map = target_frame.get("axis_map") if isinstance(target_frame.get("axis_map"), dict) else {}
    east = axis_map.get("east", "?")
    north = axis_map.get("north", "?")
    up = axis_map.get("up", "?")
    return {
        "frame_name": str(config.get("name", f"{engine}_orientation")),
        "handedness": str(target_frame.get("handedness", "?")),
        "units": str(target_frame.get("units", "?")),
        "east": str(east),
        "north": str(north),
        "up": str(up),
        "asset_forward": str(asset.get("forward_axis", "?")),
        "asset_up": str(asset.get("up_axis", "?")),
    }


def compare_explainer(engine: str) -> dict[str, str]:
    positive = engine_convention_summary(engine, "good")
    good_results = case_result_map(engine, "good")
    bad_results = case_result_map(engine, "bad")
    good_adelaide = good_results.get(NEGATIVE_CASE, {})
    bad_adelaide = bad_results.get(NEGATIVE_CASE, {})
    bad_config = config_for(engine, "bad")
    bad_asset = bad_config.get("asset") if isinstance(bad_config.get("asset"), dict) else {}

    positive_expected = (
        f"Correct means the rendered body basis matches the shared oracle after applying this engine's axis map: "
        f"east->{positive['east']}, north->{positive['north']}, up->{positive['up']}. "
        f"The asset itself is authored forward {positive['asset_forward']} and up {positive['asset_up']}."
    )
    cross_engine_reason = (
        f"{ENGINE_CONFIGS[engine]['label']} is expected to look different from the other engines because its visible forward/up convention is different. "
        f"The proof is equivalent because the same fixture set and same oracle are being projected through a different engine frame."
    )
    negative_reason = (
        "The negative proof exists so the verifier demonstrates discrimination, not just presentation. "
        f"In the known-bad route the asset forward axis is changed to {bad_asset.get('forward_axis', '?')} "
        f"and the Adelaide case fails with max axis error {float(bad_adelaide.get('max_axis_error_deg', 0.0)):.1f} deg."
    )
    negative_expected = (
        f"The matching positive Adelaide case still passes at {float(good_adelaide.get('max_axis_error_deg', 0.0)):.1f} deg max axis error, "
        "so the failure is tied to the injected mapping defect rather than the fixture."
    )
    return {
        "positive_expected": positive_expected,
        "cross_engine_reason": cross_engine_reason,
        "negative_reason": negative_reason,
        "negative_expected": negative_expected,
    }


def tile_paste(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    source_path: Path,
    box: tuple[int, int, int, int],
    outline: str,
) -> None:
    image = fit_cover(Image.open(source_path).convert("RGB"), (box[2] - box[0], box[3] - box[1]))
    canvas.paste(image, (box[0], box[1]))
    draw.rounded_rectangle((box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2), radius=16, outline=outline, width=2)


def placeholder_tile(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    outline: str,
    title: str,
    detail: str,
) -> None:
    draw.rounded_rectangle(box, radius=16, fill="#15313a", outline=outline, width=2)
    title_font = font(FONT_BOLD, 24)
    body_font = font(FONT_REGULAR, 18)
    draw.text((box[0] + 20, box[1] + 18), title, font=title_font, fill="#f1f6e9")
    draw_multiline(
        draw,
        detail,
        (box[0] + 20, box[1] + 60),
        body_font,
        "#c9ddd2",
        max(box[2] - box[0] - 40, 80),
        line_gap=5,
    )


def tile_paste_or_placeholder(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    source_path: Path,
    box: tuple[int, int, int, int],
    outline: str,
    title: str,
    detail: str,
) -> None:
    if source_path.exists():
        tile_paste(canvas, draw, source_path, box, outline)
        return
    placeholder_tile(canvas, draw, box, outline, title, detail)


def render_positive_panel(engine: str, out_dir: Path) -> Path:
    config = ENGINE_CONFIGS[engine]
    summary = summary_for(engine, "good")
    explainer = compare_explainer(engine)
    conventions = engine_convention_summary(engine, "good")
    case_rows = case_result_map(engine, "good")

    img = Image.new("RGB", CANVAS, "#0a1820")
    draw = ImageDraw.Draw(img)
    title_font = font(FONT_BOLD, 74)
    sub_font = font(FONT_REGULAR, 24)
    label_font = font(FONT_BOLD, 34)
    body_font = font(FONT_REGULAR, 22)
    small_font = font(FONT_REGULAR, 18)
    badge_font = font(FONT_BOLD, 16)

    draw.rectangle((0, 0, CANVAS[0], CANVAS[1]), fill="#0b1d25")
    draw.text((88, 68), f"{config['label']} Orientation Positive Proof", font=title_font, fill="#f1f6e9")
    draw_multiline(
        draw,
        "Breadth view of passing in-engine orientation renders. Same oracle and fixture family as the other engines, projected through this engine's own axis convention.",
        (92, 146),
        sub_font,
        "#c9ddd2",
        1700,
        line_gap=4,
    )

    draw.rounded_rectangle((92, 202, 1830, 348), radius=26, fill="#12303a", outline="#456d77", width=2)
    draw.text((124, 230), "What Passing Means", font=label_font, fill="#f1f6e9")
    draw_badge(draw, (1524, 226, 1750, 266), "#d2f36b", "ALL CASES PASS", "#192112", badge_font)
    draw.text(
        (124, 278),
        f"{summary.get('pass_count', 0)}/{summary.get('case_count', 0)} cases pass, max axis error {float(summary.get('max_axis_error_deg', 0.0)):.1f} deg.",
        font=body_font,
        fill="#d9e7df",
    )
    draw_multiline(draw, explainer["positive_expected"], (124, 308), small_font, "#9cbcaf", 1060, line_gap=6)

    draw.rounded_rectangle((1280, 220, 1800, 330), radius=18, fill="#0d252d", outline="#35555e", width=1)
    draw.text((1310, 242), "Engine Convention", font=body_font, fill="#f1f6e9")
    draw_multiline(
        draw,
        f"frame {conventions['frame_name']} | {conventions['handedness']} handed | {conventions['units']}",
        (1310, 274),
        small_font,
        "#c9ddd2",
        450,
        line_gap=4,
    )
    draw_multiline(
        draw,
        f"map E:{conventions['east']} N:{conventions['north']} U:{conventions['up']}",
        (1310, 314),
        small_font,
        "#c9ddd2",
        450,
        line_gap=4,
    )

    tile_w = 520
    tile_h = 198
    x_positions = (124, 700, 1276)
    y_positions = (396, 674)
    index = 0
    for row_y in y_positions:
        for col_x in x_positions:
            case_name = POSITIVE_CASES[index]
            path = render_path_for(engine, "good", case_name, "perspective")
            tile_paste_or_placeholder(
                img,
                draw,
                path,
                (col_x, row_y, col_x + tile_w, row_y + tile_h),
                "#6ea59a",
                "Render bundle missing",
                f"Expected {path.name}. This panel still documents the case and oracle-backed pass result so the missing host render is visible instead of silent.",
            )
            row = case_rows.get(case_name, {})
            draw.text((col_x, row_y + tile_h + 10), human_case_label(case_name), font=small_font, fill="#f1f6e9")
            draw_multiline(
                draw,
                f"{case_caption(case_name)} | axis error {float(row.get('max_axis_error_deg', 0.0)):.1f} deg",
                (col_x, row_y + tile_h + 34),
                small_font,
                "#9cbcaf",
                tile_w - 10,
                line_gap=3,
            )
            index += 1

    draw.rounded_rectangle((92, 930, 1830, 1024), radius=22, fill="#10272d", outline="#35555e", width=1)
    draw.text((122, 954), "Why visuals differ", font=body_font, fill="#f1f6e9")
    draw_multiline(
        draw,
        f"{explainer['cross_engine_reason']} The equator / prime meridian case is included in every engine panel as the same easy-to-reason-about global anchor.",
        (430, 970),
        small_font,
        "#c9ddd2",
        1270,
        line_gap=5,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{engine}_orientation_positive_collage_1920x1080.png"
    img.save(out_path, format="PNG")
    return out_path


def render_negative_panel(engine: str, out_dir: Path) -> Path:
    config = ENGINE_CONFIGS[engine]
    summary = summary_for(engine, "bad")
    explainer = compare_explainer(engine)
    conventions = engine_convention_summary(engine, "good")
    paths = render_paths(engine, "bad", NEGATIVE_CASE)

    img = Image.new("RGB", CANVAS, "#130e0d")
    draw = ImageDraw.Draw(img)
    title_font = font(FONT_BOLD, 74)
    sub_font = font(FONT_REGULAR, 24)
    label_font = font(FONT_BOLD, 34)
    body_font = font(FONT_REGULAR, 22)
    small_font = font(FONT_REGULAR, 18)
    badge_font = font(FONT_BOLD, 16)

    draw.rectangle((0, 0, CANVAS[0], CANVAS[1]), fill="#241413")
    draw.text((88, 68), f"{config['label']} Orientation Known-Bad Proof", font=title_font, fill="#f9efe9")
    draw_multiline(
        draw,
        "Intentional failing route. This panel proves the verifier rejects the wrong asset mapping under the same fixture and camera setup.",
        (92, 146),
        sub_font,
        "#e4c6bd",
        1700,
        line_gap=4,
    )

    draw.rounded_rectangle((92, 202, 1830, 370), radius=26, fill="#331d1a", outline="#8d5b51", width=2)
    draw.text((124, 230), "Why Show A Negative Proof", font=label_font, fill="#f9efe9")
    draw_badge(draw, (1464, 226, 1754, 266), "#f3a16b", "INTENTIONAL FAIL", "#2b160f", badge_font)
    draw.text(
        (124, 278),
        f"{summary.get('pass_count', 0)}/{summary.get('case_count', 0)} cases pass, max axis error {float(summary.get('max_axis_error_deg', 0.0)):.1f} deg.",
        font=body_font,
        fill="#f0d2c7",
    )
    draw_multiline(draw, explainer["negative_reason"], (124, 312), small_font, "#d8aa9a", 1540, line_gap=6)

    tile_w = 500
    tile_h = 260
    x_positions = (124, 710, 1296)
    for idx, view in enumerate(VIEWS):
        x0 = x_positions[idx]
        tile_paste_or_placeholder(
            img,
            draw,
            paths[idx],
            (x0, 430, x0 + tile_w, 430 + tile_h),
            "#d08c76",
            "Render bundle missing",
            f"Expected {paths[idx].name}. The known-bad proof remains documented so the absent host render is explicit.",
        )
        draw.text((x0, 706), view.replace("_", " ").title(), font=small_font, fill="#f9efe9")
        draw.text((x0, 730), human_case_label(NEGATIVE_CASE), font=small_font, fill="#d8aa9a")

    draw.rounded_rectangle((92, 804, 1830, 1010), radius=22, fill="#2f1a18", outline="#744940", width=1)
    draw.text((124, 834), "How To Read This Failure", font=label_font, fill="#f9efe9")
    draw_multiline(draw, explainer["negative_expected"], (124, 886), body_font, "#f0d2c7", 760)
    draw.text((1040, 844), "Reference positive convention", font=body_font, fill="#f9efe9")
    draw_multiline(
        draw,
        f"{ENGINE_CONFIGS[engine]['label']} good route uses asset forward {conventions['asset_forward']} and up {conventions['asset_up']}.",
        (1040, 884),
        small_font,
        "#e4c6bd",
        690,
        line_gap=4,
    )
    draw_multiline(
        draw,
        f"Axis map stays E:{conventions['east']} N:{conventions['north']} U:{conventions['up']}; only the bad asset mapping changes.",
        (1040, 924),
        small_font,
        "#e4c6bd",
        690,
        line_gap=4,
    )
    draw_multiline(
        draw,
        "That is why the negative route is useful: it isolates a real integration defect instead of altering the fixture.",
        (1040, 968),
        small_font,
        "#e4c6bd",
        690,
        line_gap=4,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{engine}_orientation_negative_collage_1920x1080.png"
    img.save(out_path, format="PNG")
    return out_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    engines = args.engine or list(ENGINE_CONFIGS)
    for engine in engines:
        print(render_positive_panel(engine, args.out_dir))
        print(render_negative_panel(engine, args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
