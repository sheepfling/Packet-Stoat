# Cross-Engine Benchmark Program Blurb

FastDIS needs one benchmark program that proves the whole product, not just the
parser. The target is a shared cross-engine harness that runs the same DIS
traffic scenarios, truth fixtures, and report contract across native, C++,
Python, Godot, Unreal, and Unity, then publishes honest same-host head-to-head
evidence against GRILL in Unreal and Unity wherever GRILL actually installs and
runs. When that program is complete, FastDIS will have one claim-bounded
benchmark matrix covering ingest throughput, filtering cost, latest-state
correctness, replay outcomes, adapter runtime overhead, and cross-engine
equivalence, all tied to pinned reproducible artifacts. That is the point where
FastDIS stops looking like a promising architecture and starts reading as a
verified, benchmarked, and defensible cross-engine DIS runtime.
