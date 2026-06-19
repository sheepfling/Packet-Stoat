from __future__ import annotations

from setuptools import Extension, setup

# Keep the native layer tiny and optional. The pure-Python fallback in
# fastdis._fallback is always shipped. Platform wheels can be built with
# cibuildwheel once the native path grows.
ext_modules = [
    Extension(
        "fastdis._cfast",
        sources=["src/fastdis/_cfast.c"],
        optional=True,
    )
]

setup(ext_modules=ext_modules)
