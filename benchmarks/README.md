# fastdis benchmarks

- `native_bench.cpp` builds as `fastdis_native_bench` through CMake and measures
  the C ABI/shared-library hot path directly.
- `bench_ctypes.py` measures Python `ctypes` wrapper overhead when driving the
  shared library from Python.
- `../examples/common/replay_reader.hpp` is the shared `.fastdispkt` reader used
  by the C++ example and the native benchmark.
- `../examples/common/udp_receiver.hpp` is the optional no-`libpcap` UDP burst
  helper used by `examples/cpp/udp_burst.cpp`.

See `../docs/BENCHMARKING.md` for commands and interpretation notes.
