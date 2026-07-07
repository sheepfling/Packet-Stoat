# Cesium Proof Strategy

Cesium is the terrain and 3D Tiles dependency that makes the FastDIS engine examples credible. The final goal is a cross-engine, cross-host Cesium proof stack that lets FastDIS examples rely on Cesium without guessing about plugin compatibility.

The proof order is strict:

1. Plugin proofs
2. Minimal example proofs
3. Showcase proof

## Plugin Proofs

Plugin proof comes first because every example project inherits its risk. A lane is green only when the plugin can be built or imported on the target engine and the report captures the exact process used to get there.

Current required plugin lanes:

- Unreal 5.7: Cesium for Unreal build plus install smoke.
- Unreal 5.8: Cesium for Unreal build plus install smoke.
- Unity 6000.5: Cesium Unity package import and script compile smoke.
- Godot 4.7: Battle-Road-Labs 3D-Tiles-For-Godot native plugin build.

Valid plugin outcomes are either a passing proof or an upstream-ready fix packet. A failing lane is still useful if it records the exact engine version, host, command, toolchain, failure class, log tail, and process quirks.

The normalized plugin matrix is:

- `artifacts/reports/cesium_engine_matrix/cesium_engine_matrix.json`
- `artifacts/reports/cesium_engine_matrix/cesium_engine_matrix.md`

For reruns, prefer the lane runner instead of hand-assembling long command lines:

```powershell
python tools/run_cesium_plugin_lanes.py --dry-run --lanes all
```

That emits the exact commands, per-lane log destinations, and the lane report under `artifacts/reports/cesium_lane_runner/`.

Useful launcher examples:

```powershell
python tools/run_cesium_plugin_lanes.py --lanes unreal-vendor unity-vendor --parallel --refresh-matrix
python tools/run_cesium_plugin_lanes.py --lanes godot-linux-docker
python tools/run_cesium_plugin_lanes.py --lanes all --parallel --refresh-matrix
```

Parallel execution is lane-aware rather than naive. Lanes with distinct artifact namespaces can overlap, while overlapping lanes such as `godot-vendor` and `godot-linux-docker` are kept serial so they do not stomp the same report/log paths.

## Host Proofs

Windows proof does not imply Linux or macOS proof. Host proof is a second dimension over the plugin lanes.

Target host coverage:

- Windows local host proof for all practical editor lanes.
- Linux Docker proof where the engine/vendor route can run headlessly.
- macOS host bundle proof imported from a macOS machine.

The repo already has host-bundle patterns for Unity and Alpha signoff, plus Docker routes for Linux native and Unreal harness work. Cesium should reuse those patterns instead of inventing a separate reporting style.

Godot now has a Linux Docker proof wrapper:

- `python tools/build_godot_linux_proof_image.py`
- `python tools/run_godot_vendor_linux_docker.py`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker.json`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker.md`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker_stdout.log`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker_build.log`

This route uses `fastdis-godot-linux-proof:godot4.7-ubuntu24.04`, which installs the pinned Godot 4.7 Linux binary, SCons, CMake, Ninja, and the native C++ toolchain. The Docker wrapper mounts `fastdis-godot-linux-proof-cache` at the container cache root so vcpkg/ezvcpkg dependency state survives retries.

Default proof runs are intentionally quiet but not blind:

```powershell
python tools/run_godot_vendor_linux_docker.py
```

The default mode captures outer Docker output and inner SCons/vcpkg/CMake output to log files, then records bounded tails in the JSON and Markdown reports. Use this for CI-like proof runs where the report packet is the source of truth.

For an expensive interactive run where progress matters, tee both layers:

```powershell
python tools/run_godot_vendor_linux_docker.py --docker-log-mode tee --inner-log-mode tee --log-tail-lines 120
```

The main verbosity and cost knobs are:

- `--docker-log-mode capture|tee`: capture Docker output quietly, or stream it live while still persisting `cesium-godot_linux_docker_stdout.log`.
- `--inner-log-mode capture|tee`: forward the same quiet/live choice to `tools/godot_vendor_workflow.py handoff`.
- `--log-tail-lines N`: control how much output is embedded in JSON/Markdown reports without changing the full log files.
- `--timeout-seconds N`: bound the outer Docker run; timeout attempts to remove the named proof container.
- `--scons-jobs N`: control upstream SCons parallelism.
- `--vcpkg-max-concurrency N`: control native dependency package build parallelism.
- `--cmake-build-parallel-level N`: control CMake build parallelism.
- `--cache-volume NAME`: choose the Docker volume used for native dependency cache reuse.
- `--no-clean-native-cache`: keep generated native CMake cache files when intentionally debugging cache behavior.

Expensive successful outputs can be parked semi-persistently under the ignored local vault `artifacts/preserved/`. This is for binaries, logs, and reports that should survive testing another engine version without being committed to git.

To preserve a Godot Linux Docker run as it completes:

```powershell
python tools/run_godot_vendor_linux_docker.py --preserve --preserve-label godot-4.7-green
```

To preserve an already-written report:

```powershell
python tools/preserve_artifact_snapshot.py --report artifacts/reports/godot_vendor_plugin/cesium-godot_linux_docker.json --lane cesium-godot-linux-docker --label godot-4.7-green
```

Each snapshot writes a `SNAPSHOT_MANIFEST.json` with original paths, copied snapshot paths, sizes, and SHA-256 hashes. `tools/clean_artifacts.py --apply` preserves `artifacts/preserved/` by default and only removes other transient artifact children.

Known Linux Docker process quirks:

- The mounted vendor checkout may contain a host-specific `cesium_godot/native/CMakeCache.txt`; the Docker wrapper removes generated CMake cache files before the Linux build.
- vcpkg/GitHub downloads may fail through Docker Desktop proxying with HTTP/2 stream cancellation; the wrapper writes a curl config forcing HTTP/1.1 inside the proof home.
- Docker Desktop memory is part of the proof environment. On the current Windows host Docker reports about 7.7 GiB RAM, so `VCPKG_MAX_CONCURRENCY`, `CMAKE_BUILD_PARALLEL_LEVEL`, and SCons jobs are intentionally bounded.

## Example Proofs

Example proof starts only after plugin proof is stable or the blocked plugin lanes have explicit accepted fix packets.

Minimal examples come before the showcase:

- Cesium-backed Unreal minimal example.
- Cesium-backed Unity minimal example.
- Cesium-backed Godot minimal example.

Each minimal example should prove that Cesium loads in-engine and can coexist with the FastDIS integration path without requiring the full showcase scenario.

## Showcase Proof

The showcase is the last gate. Its job is to demonstrate why Cesium matters: mesh and tileset quality, terrain context, and a persuasive out-of-the-box experience similar to the GRILL DIS example project.

The showcase should not become the place where plugin compatibility is debugged. If a showcase build fails because of Cesium plugin compatibility, the work moves back to the plugin proof lane.

## Current Posture

As of the current Cesium engine matrix:

- Unreal 5.7 is passing on the Windows lane.
- Unreal 5.8 is passing on the Windows lane.
- Unity 6000.5 has a real compile/import fix packet.
- Godot 4.7 has a real Draco native dependency compile/fix packet.
- Godot Linux Docker now passes the Battle Road plugin build with Godot 4.7 and emits `libGodot3DTiles.linux.template_release.x86_64.so`.

The next phase is to fix or upstream the Unity and Godot plugin lanes, then expand host proof for Linux Docker and macOS bundles.
