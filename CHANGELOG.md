# Changelog

All notable changes to fastdis are tracked here.

## v0.12.0-alpha2 - Unreleased

Theme: engine integration + correctness hardening.

Planned:

- Validate ECEF -> ENU -> Unreal/Godot frame transforms with fixed fixtures.
- Harden snapshot-buffer handoff semantics for delayed engine readers.
- Add snapshot pressure stats and/or triple-buffer support.
- Improve C++ RAII configuration builders and scoped snapshot views.
- Make Unreal and Godot samples buildable runnable previews.
- Expand replay and benchmark workloads with regression checks.
- Add malformed packet tests, fuzz targets, and sanitizer jobs.
- Ship a source-only Alpha 2 bundle with checksums and benchmark report.

## v0.11.0-alpha1

- Added stable C ABI shared-library path.
- Added header-only C++ RAII wrapper.
- Added Entity State fast path and compact transform output.
- Added batch scanning APIs.
- Added latest-state entity table and double-buffer snapshots.
- Added Unreal and Godot scaffolds.
- Added frame transform helpers.
- Added native and Python benchmark tooling.
