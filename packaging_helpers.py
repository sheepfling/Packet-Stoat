from __future__ import annotations

import os
from pathlib import Path


def wheel_native_lib_from_env() -> Path | None:
    raw = os.environ.get("FASTDIS_WHEEL_NATIVE_LIB", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def wheel_plat_name_from_env() -> str | None:
    raw = os.environ.get("FASTDIS_WHEEL_PLAT_NAME", "").strip()
    return raw or None


def should_skip_cfast() -> bool:
    return os.environ.get("FASTDIS_SKIP_CFAST", "").strip() == "1"


def has_bundled_native_wheel() -> bool:
    return wheel_native_lib_from_env() is not None


def validate_wheel_env() -> None:
    native_lib = wheel_native_lib_from_env()
    plat_name = wheel_plat_name_from_env()
    if native_lib is None:
        return
    if not native_lib.is_file():
        raise FileNotFoundError(
            f"FASTDIS_WHEEL_NATIVE_LIB points to a missing file: {native_lib}"
        )
    if plat_name is None:
        raise ValueError(
            "FASTDIS_WHEEL_PLAT_NAME is required when FASTDIS_WHEEL_NATIVE_LIB is set"
        )


def bundled_native_filename() -> str | None:
    native_lib = wheel_native_lib_from_env()
    if native_lib is None:
        return None
    if native_lib.suffix.lower() == ".dll":
        return "fastdis.dll"
    return native_lib.name
