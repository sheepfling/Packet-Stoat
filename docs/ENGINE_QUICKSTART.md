# Engine Quickstart

FastDIS proves this engine flow:

```text
DIS UDP/replay packets
  -> native fastdis scanner
  -> Entity State transform decode
  -> latest-state entity table
  -> snapshot buffer
  -> Unreal actors / Godot Node3D / Unity GameObject updates
```

## Unreal

```bash
fastdis engine unreal doctor --engine-version 5.8
fastdis engine unreal build --engine-version 5.8
fastdis engine unreal verify --engine-version 5.8
fastdis engine unreal demo --engine-version 5.8
```

Use `fastdis engine unreal matrix` when multiple Unreal installs are
available. See `docs/UNREAL_VERSION_MATRIX.md` for install discovery and known
quirks.

Unreal workflow state is redirected under a writable no-space work root. Override
it when needed:

```bash
export FASTDIS_UNREAL_WORK_ROOT=build/work/unreal
```

The workflow can redirect FastDIS project outputs, home/cache paths, and temp
paths. UnrealBuildTool may still write engine intermediates under the Unreal
install tree.
If doctor reports `permission:engine_intermediate` as a warning/failure, run the
Unreal lane from a user/shell allowed to write that install, or prebuild/cache
the target once outside a restrictive sandbox.

## Godot

```bash
fastdis engine godot doctor
fastdis engine godot build
fastdis engine godot verify
fastdis engine godot demo
```

The Godot workflow stages host-specific `.dll`, `.so`, or `.dylib` artifacts
under the demo and orientation verification projects. See
`docs/GODOT_WORKFLOW.md` for the full build/stage policy.

Godot uses `FASTDIS_GODOT_WORK_ROOT` for no-space scratch state and redirects
home/cache/temp paths for SCons and headless Godot:

```bash
export FASTDIS_GODOT_WORK_ROOT=build/work/godot
```

## Unity

```bash
fastdis engine unity discover
fastdis engine unity doctor --unity-version 6000.5
fastdis engine unity build --unity-version 6000.5
fastdis engine unity build --all-native
fastdis engine unity verify
fastdis engine unity runtime-verify --unity-version 6000.5
fastdis engine unity report --unity-version 6000.5
```

FastDIS for Unity is a Unity Package Manager package at
`integrations/unity/com.sheepfling.fastdis`.

Install from Git during alpha:

```text
https://github.com/sheepfling/Packet-Stoat.git?path=integrations/unity/com.sheepfling.fastdis
```

Unity status flags are intentionally split:

- `unity_workflow_status`: package/workflow/report parity.
- `unity_native_status`: current-platform native library staged into the UPM
  package.
- `unity_runtime_status`: Unity Editor runtime verification status.
- `unity_demo_status`: higher-level demo/federate scene verification status.

Use `fastdis engine unity build --all-native` for the release payload matrix:

- macOS: host CMake build stages `Runtime/Plugins/macOS/libfastdis.dylib`.
- Windows: MinGW-w64 cross compile stages `Runtime/Plugins/Windows/x86_64/fastdis.dll`.
- Linux: Docker `linux/amd64` build stages `Runtime/Plugins/Linux/x86_64/libfastdis.so`.

The lower-level check is:

```bash
python tools/build_unity_native_matrix.py doctor
python tools/build_unity_native_matrix.py build --targets macos windows linux --keep-going
```

Generated native binaries and Unity `.meta` files under `Runtime/Plugins/` are
build artifacts and are intentionally ignored by git. Unity Editor runtime
verification is available through `runtime-verify`; full federated headless and
desktop demo scenes remain a later engine-demo gate.

Unity uses `FASTDIS_UNITY_WORK_ROOT` for scratch state and redirected
home/cache/temp paths:

```bash
export FASTDIS_UNITY_WORK_ROOT=build/work/unity
```

## Sim Regression Harness

Use `fastdis simtest` for metadata-first regression checks across Unreal, Godot,
and Unity runtime scenes. Engine scenes should emit deterministic
`meta_*.json` files and optional `crops/*.png` image crops under `build/`, then
compare them against small committed baselines:

```bash
fastdis simtest inspect build/simtest/runs/latest
fastdis simtest compare \
  build/simtest/runs/latest \
  tests/simtest/baselines/dis_replay_airtrack/golden \
  --scenario tests/simtest/scenarios/dis_replay_airtrack.json \
  --report build/reports/simtest_dis_replay_airtrack
```

See `docs/SIMTEST.md` for the run directory contract, tolerances, crop checks,
and baseline/bless policy.

## Orientation Policy

Position mapping is the supported baseline. Orientation is opt-in through named
profiles, fixtures, and engine verification. Raw DIS `psi/theta/phi` values
must not be passed directly into engine Euler APIs.

Run the closeout assurance bundle with:

```bash
python tools/run_orientation_assurance.py --out build/verification_reports/orientation_current
```

Use `--run-engine-runtimes` when the local Unreal/Godot installs should be
launched as part of the same report. See `docs/ORIENTATION_ASSURANCE.md`.
