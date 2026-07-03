#!/usr/bin/env python3
"""Compatibility wrapper for the Cesium example workflow."""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "extensions" / "cesium" / "tools" / "cesium_example_workflow.py"


if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
