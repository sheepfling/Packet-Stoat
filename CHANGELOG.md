# Changelog

All notable changes to fastdis are tracked here.

## v0.12.0-alpha2

Theme: engine integration + correctness hardening.

Highlights:

- Added DIS 6/7 package-header and message-catalog coverage across the native C
  ABI, header-only C++ wrapper, and Python helpers.
- Added fixed-fixture frame transform validation, orientation convention tests,
  and in-engine Unreal/Godot verification scaffolds with shared JSON cases.
- Added snapshot buffer pressure stats and N-slot snapshot buffers with
  double-slot and triple-slot support.
- Added `ScannerBuilder`, `EntityTableConfig`, `SnapshotBufferConfig`,
  span-friendly C++ APIs, and richer scoped snapshot view helpers.
- Promoted the Unreal and Godot adapter scaffolds into replay-driven sample
  plugin/demo paths with shared native ingress helpers.
- Expanded benchmark workloads, generated Alpha 2 sample reports, and added a
  regression-check script.
- Added malformed packet coverage, fuzz harnesses, and repeatable ASAN/UBSAN
  build automation.
- Added repeatable Alpha 2 source-bundle packaging with checksums and zip
  verification.

## v0.11.0-alpha1

- Added stable C ABI shared-library path.
- Added header-only C++ RAII wrapper.
- Added Entity State fast path and compact transform output.
- Added batch scanning APIs.
- Added latest-state entity table and double-buffer snapshots.
- Added Unreal and Godot scaffolds.
- Added frame transform helpers.
- Added native and Python benchmark tooling.
