# Shared Example Helpers

This directory holds optional helpers used by examples and benchmarks without
expanding the core `fastdis` C ABI.

- `replay_reader.hpp`: dependency-free `.fastdispkt` reader shared by the C++
  snapshot example and the native benchmark.
- `udp_receiver.hpp`: lightweight non-`libpcap` UDP burst receiver helper used
  by `examples/cpp/udp_burst.cpp`.

These helpers are intentionally outside `src/` so engine or host integrations
can reuse them or replace them without coupling the parser library to sockets or
capture formats.

For the Alpha 3 networking/replay boundary and planned replay v2 format, see:

- `docs/NETWORKING.md`
- `docs/REPLAY_FORMAT.md`
