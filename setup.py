from __future__ import annotations

import os
from pathlib import Path
import sys

from setuptools import Extension, setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging_helpers import (
    bundled_native_filename,
    has_bundled_native_wheel,
    should_skip_cfast,
    validate_wheel_env,
    wheel_native_lib_from_env,
    wheel_plat_name_from_env,
)

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except Exception:  # pragma: no cover
    _bdist_wheel = None

# Keep the native layer tiny and optional. The pure-Python fallback in
# fastdis._fallback is always shipped. Platform wheels can be built with
# cibuildwheel once the native path grows.
ext_modules = []
if not should_skip_cfast():
    ext_modules.append(
        Extension(
            "fastdis._cfast",
            sources=["src/fastdis/_cfast.c"],
            optional=True,
        )
    )


class build_py(_build_py):
    def run(self) -> None:
        validate_wheel_env()
        super().run()
        native_lib = wheel_native_lib_from_env()
        if native_lib is None:
            return
        target_dir = Path(self.build_lib) / "fastdis"
        target_dir.mkdir(parents=True, exist_ok=True)
        for pattern in ("_cfast*.so", "_cfast*.pyd", "_cfast*.dylib", "libfastdis*.so", "libfastdis*.dylib", "fastdis.dll"):
            for existing in target_dir.glob(pattern):
                existing.unlink()
        self.copy_file(str(native_lib), str(target_dir / bundled_native_filename()))


if _bdist_wheel is not None:
    class bdist_wheel(_bdist_wheel):
        def finalize_options(self) -> None:
            super().finalize_options()
            if has_bundled_native_wheel():
                validate_wheel_env()
                self.root_is_pure = False
                self.plat_name_supplied = True
                self.plat_name = wheel_plat_name_from_env()

        def get_tag(self):
            if has_bundled_native_wheel():
                return (
                    os.environ.get("FASTDIS_WHEEL_PYTHON_TAG", "py3"),
                    os.environ.get("FASTDIS_WHEEL_ABI_TAG", "none"),
                    wheel_plat_name_from_env(),
                )
            return super().get_tag()
else:  # pragma: no cover
    bdist_wheel = None

cmdclass = {"build_py": build_py}
if bdist_wheel is not None:
    cmdclass["bdist_wheel"] = bdist_wheel

setup(
    ext_modules=ext_modules,
    include_package_data=True,
    package_data={"fastdis": ["*.dll", "*.dylib", "*.so", "*.so.*"]},
    cmdclass=cmdclass,
)
