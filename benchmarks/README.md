# fastdis benchmarks

- `native_bench.cpp` builds as `fastdis_native_bench` through CMake and measures
  the C ABI/shared-library hot path directly.
- `bench_ctypes.py` measures Python `ctypes` wrapper overhead when driving the
  shared library from Python.

See `../docs/BENCHMARKING.md` for commands and interpretation notes.
