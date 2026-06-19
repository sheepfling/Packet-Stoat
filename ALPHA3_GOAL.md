# Alpha 3 Goal

Objective:
Deliver `fastdis v0.13.0-alpha3` as a confidence release that proves exactly
what the SDK covers, hardens every exposed parser path against malformed input,
verifies orientation with independent numeric and in-engine oracles, and ships
qualified benchmark evidence.

Completion standard:

- Message-surface truth is generated, not hand-waved.
- Every cataloged PDU has shallow fuzz coverage.
- Every typed parser path has deep fuzz and sanitizer coverage.
- Orientation is proven by native, Python, SciPy, SymPy, golden fixtures, and
  in-engine Unreal/Godot verification.
- Benchmark and release artifacts state what is fast, what is verified, and
  what is still intentionally out of scope.

Primary execution order:

1. Generate the message coverage manifest.
2. Wire shallow fuzz coverage across the full catalog.
3. Deepen fuzz/sanitizer coverage for typed and engine-facing paths.
4. Finish the multi-oracle orientation proof lane.
5. Expand benchmark qualification and only then extend typed PDU coverage.

Non-goals:

- Do not claim full typed support for all DIS PDUs.
- Do not expose raw DIS Euler passthrough as an engine API.
- Do not add broad new typed PDU families before the coverage/fuzz framework is
  in place.

Operator note:

Use this file as the goal blurb for execution tracking. Use
`ALPHA3_PLAN.md` as the detailed work breakdown and definition of done.
