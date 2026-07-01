from __future__ import annotations

import importlib.util
from pathlib import Path
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_paths_match_expected_case_family() -> None:
    module = _load_module("render_orientation_storefront_collages", ROOT / "tools" / "render_orientation_storefront_collages.py")

    unreal_good = module.render_paths("unreal", "good")
    unity_bad = module.render_paths("unity", "bad")
    godot_good = module.render_paths("godot", "good")

    assert unreal_good[0].name == "unreal_standalone_neu_adelaide_heading_135_pitch_20_roll_30_perspective_actual.png"
    assert unity_bad[-1].name == "unity_known_bad_adelaide_heading_135_pitch_20_roll_30_top_down_actual.png"
    assert godot_good[1].name == "godot_standalone_enu_adelaide_heading_135_pitch_20_roll_30_side_east_actual.png"


def test_summary_for_reads_engine_orientation_summary() -> None:
    module = _load_module("render_orientation_storefront_collages", ROOT / "tools" / "render_orientation_storefront_collages.py")

    good = module.summary_for("godot", "good")
    bad = module.summary_for("godot", "bad")

    assert good["pass_count"] == good["case_count"] == 9
    assert bad["pass_count"] == 0
    assert float(bad["max_axis_error_deg"]) >= 100.0


def test_engine_convention_summary_reads_real_axis_mapping() -> None:
    module = _load_module("render_orientation_storefront_collages", ROOT / "tools" / "render_orientation_storefront_collages.py")

    unreal = module.engine_convention_summary("unreal")
    unity = module.engine_convention_summary("unity")
    godot = module.engine_convention_summary("godot")

    assert unreal["asset_forward"] == "positive_x"
    assert unity["asset_forward"] == "positive_z"
    assert godot["asset_forward"] == "negative_z"
    assert unreal["north"] == "positive_x"
    assert unity["north"] == "positive_z"
    assert godot["north"] == "negative_z"


def test_render_positive_panel_uses_placeholder_when_renders_missing(tmp_path: Path) -> None:
    module = _load_module("render_orientation_storefront_collages", ROOT / "tools" / "render_orientation_storefront_collages.py")
    module.SUMMARY_ROOT = tmp_path

    out_path = module.render_positive_panel("unreal", tmp_path / "out")

    assert out_path.exists()
    with Image.open(out_path) as rendered:
        assert rendered.size == module.CANVAS


def test_render_negative_panel_uses_placeholder_when_renders_missing(tmp_path: Path) -> None:
    module = _load_module("render_orientation_storefront_collages", ROOT / "tools" / "render_orientation_storefront_collages.py")
    module.SUMMARY_ROOT = tmp_path

    out_path = module.render_negative_panel("unity", tmp_path / "out")

    assert out_path.exists()
    with Image.open(out_path) as rendered:
        assert rendered.size == module.CANVAS
