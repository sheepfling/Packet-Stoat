# Cesium Fork Ledger

This note collects the Cesium-specific code changes and documentation trail that
matter for upstream-facing forks and PRs.

Use it as the branch-level index for the lane notes already captured elsewhere
in the repo.

## What Is Already Documented

- [Cesium proof strategy](./CESIUM_PROOF_STRATEGY.md)
- [Cesium source route](../extensions/cesium/docs/CESIUM_SOURCE_ROUTE.md)
- [Cesium example standard](../extensions/cesium/docs/CESIUM_EXAMPLE_STANDARD.md)
- [Unity 6000.5 findings](./CESIUM_UNITY_6000_5_FINDINGS.md)
- [Godot 4.7 Windows build notes](./CESIUM_GODOT_WINDOWS_4_7_BUILD_NOTES.md)

## Code Changes By Lane

### Shared Packet Stoat / Repo Boundary Work

Goal:

- keep generic orchestration in Packet Stoat
- keep product-specific Cesium work inside the Cesium tree
- keep FastDIS core free of Cesium-only policy and lane glue

The practical outputs of that boundary work are:

- the Cesium extension subtree for Cesium-specific workflow and example policy
- workspace-manifest route separation for vendor lanes versus example lanes
- report and artifact plumbing that records the exact lane, host, and proof shape

### Unreal

Documented Unreal work is split between host/toolchain handling and Cesium
plugin compatibility.

Known code changes and report updates:

- Unreal 5.7 and 5.8 lane detection and proof reporting
- Linux Docker proof wrapper and cache/report hygiene
- exact selected compiler/version recording for reproducible doctor output
- install-smoke and matrix reporting for Cesium Unreal

Where to look:

- `tools/unreal_vendor_workflow.py`
- `tools/run_cesium_plugin_lanes.py`
- `tools/build_cesium_engine_matrix.py`
- `tools/run_unreal_vendor_linux_docker.py`
- `docs/CESIUM_PROOF_STRATEGY.md`

Upstream fork target:

- `CesiumGS/cesium-unreal`

### Unity

Unity work currently has the clearest documented fix packet.

Known code changes and report updates:

- Reinterop staging no longer relies on the stub publish artifact
- source-route prep now stages the real compiled Reinterop assembly
- Unity 6000.5 editor API drift is captured as a distinct blocker
- import/compile smoke and failure reporting are normalized

Where to look:

- `tools/unity_vendor_workflow.py`
- `tools/run_unity_install_smoke.py`
- `docs/CESIUM_UNITY_6000_5_FINDINGS.md`
- `docs/CESIUM_SOURCE_ROUTE.md`

Upstream fork target:

- `CesiumGS/cesium-unity`

### Godot

Godot has both Windows and Linux proof notes now.

Known code changes and report updates:

- Windows 4.7 build lane fix in `SCsub`
- proof runner normalization for report tails and command capture
- Linux Docker proof wrapper for repeatable headless verification
- cache and path hygiene for SCons, CMake, and vcpkg retries

Where to look:

- `tools/godot_vendor_workflow.py`
- `tools/build_godot_linux_proof_image.py`
- `tools/run_godot_vendor_linux_docker.py`
- `docs/CESIUM_GODOT_WINDOWS_4_7_BUILD_NOTES.md`
- `docs/CESIUM_PROOF_STRATEGY.md`

Upstream fork target:

- `Battle-Road-Labs/3D-Tiles-For-Godot`

## What This Means For Forks

The repo is now organized enough to branch the upstream fixes separately:

- one fork/PR packet for Cesium Unreal
- one fork/PR packet for Cesium Unity
- one fork/PR packet for Battle Road Godot

The fork packets should preserve:

- exact engine version
- host and toolchain
- command used
- failure class or success proof
- log tail and artifact paths

## Remaining Gap

The documentation is now sufficient to start creating per-repo forks, but the
lane notes are still distributed across multiple files. This ledger is the
branch-level index; the detailed evidence still lives in the per-lane docs.
