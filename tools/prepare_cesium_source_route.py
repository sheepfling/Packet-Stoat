#!/usr/bin/env python3
"""Compatibility wrapper for the Cesium source-route prep workflow."""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "extensions" / "cesium" / "tools" / "prepare_cesium_source_route.py"


if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
