# Cross-Engine Benchmark Program Blurb

FastDIS needs one benchmark program that proves the whole product, not just the
parser. The target is a shared cross-engine and cross-platform harness that
runs the same DIS traffic scenarios, truth fixtures, and report contract across
macOS, Windows, and Linux for native, C++, Python, Godot, Unreal, and Unity,
then publishes honest same-host head-to-head evidence against GRILL in Unreal
and Unity wherever GRILL actually installs and runs. When that program is
complete, FastDIS will have one claim-bounded benchmark matrix covering ingest
throughput, filtering cost, latest-state correctness, replay outcomes, adapter
runtime overhead, cross-engine equivalence, and platform-specific proof
boundaries, all tied to pinned reproducible artifacts. That is the point where
FastDIS stops looking like a promising architecture and starts reading as a
verified, benchmarked, and defensible cross-engine DIS runtime.

The comparison scaffold for presenting those results coherently across language,
platform, engine, and competitor lanes lives in:

- `docs/research/BENCHMARK_COMPARISON_SCAFFOLD.md`
- `tests/data/engine_benchmark_scenarios/comparison_axes.v1.json`
- `docs/research/ALL_PLATFORM_HARNESS_GOAL.md`
