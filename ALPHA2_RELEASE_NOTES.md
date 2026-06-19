# fastdis v0.12.0-alpha2 Release Notes

Status: draft.

Theme: engine integration + correctness hardening.

## Headline

fastdis Alpha 2 is the first buildable engine preview with validated
georeferenced transforms, C++ RAII ergonomics, robust snapshot handoff, and
repeatable benchmarks.

## Highlights

- TODO: Frame transform validation summary.
- TODO: Snapshot buffer handoff behavior and stats.
- TODO: C++ RAII builder and view ergonomics.
- TODO: Unreal runnable sample status.
- TODO: Godot runnable sample status.
- TODO: Benchmark report summary.
- TODO: Fuzzing and malformed packet hardening status.

## ABI

- Current Alpha 1 ABI: `FASTDIS_ABI_VERSION == 8`.
- Alpha 2 target: preserve ABI v8 unless snapshot buffer slot-count support
  requires a justified ABI v9.
- Any ABI change must pass the checklist in `docs/API_STABILITY.md`.

## Known Limitations

- Entity State remains the only body fast path.
- Orientation application remains opt-in until validated DIS body-frame traces
  are available.
- Native ingress helpers are example utilities, not part of the core C ABI.

## Build Verification

Fill this before release:

```text
python -m pytest
ctest --test-dir build --build-config Release --output-on-failure
python tools/check_exports.py build/libfastdis.dylib
python tools/build_unreal_plugin.py --verify-only
```

## Benchmark Summary

TODO: Link Alpha 2 benchmark JSON and Markdown report.

## Bundle Contents

The source bundle must include:

- `ALPHA2_RELEASE_NOTES.md`
- `RELEASE_MANIFEST.md`
- `CHECKSUMS.sha256`
- `include/`
- `src/`
- `tests/`
- `benchmarks/`
- `tools/`
- `docs/`
- `examples/`
- benchmark reports

The bundle must exclude build trees, compiled shared libraries, temporary
engine artifacts, virtual environments, and caches.
