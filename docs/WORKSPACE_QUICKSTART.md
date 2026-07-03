# Workspace Quickstart

Start here on any host.

FastDIS can light up different routes depending on:

- your host platform
- what engines are installed
- what toolchains are installed
- which routes are intentionally supported on that host

The workspace reports routes across three product trees:

- `fastdis`: the primary product and its owned proofs/artifacts
- `grill-dis`: competitor comparison and parity lanes
- `cesium`: vendor compatibility and Cesium-dependent example lanes

Helpful Cesium references:

- [Cesium extension overview](../extensions/cesium/README.md)
- [Cesium example standard](./CESIUM_EXAMPLE_STANDARD.md)
- [Cesium source-route note](./research/CESIUM_SOURCE_ROUTE.md)

The fastest honest preview is:

```bash
fastdis workspace doctor
```

For CI logs or a quick onboarding screenshot, use the compact summary:

```bash
fastdis workspace doctor --format summary
```

For automation or machine-readable handoff:

```bash
fastdis workspace routes --format json
```

For manifest-driven CI planning:

```bash
fastdis workspace ci --host-class windows --include-compat --format summary
fastdis workspace ci-print --section workspace_ci_declared_engine --format summary
fastdis workspace ci-sync
fastdis workspace ci-check
python tools/generate_workspace_ci_matrix.py check --path .github/workflows/generated/workspace-ci-matrix.json
```

What this tells you:

- which routes are `ready-now`
- which routes are `ready-after-install`
- which routes are `ready-after-setup`
- which routes are unsupported on the current host
- what command to run next for each route
- which CI rows should exist for a given host/version policy
- which product tree a route belongs to

Common examples:

```bash
fastdis workspace doctor
python extensions/cesium/tools/prepare_cesium_source_route.py
python extensions/cesium/tools/cesium_example_workflow.py doctor --engine unreal
python extensions/cesium/tools/cesium_example_workflow.py doctor --engine unity
python extensions/cesium/tools/cesium_example_workflow.py doctor --engine godot
fastdis-engine godot doctor
python tools/godot_vendor_workflow.py doctor --vendor cesium-godot
fastdis-engine unity doctor --unity-version 6000.5
fastdis-engine unreal doctor --engine-version 5.7
python tools/unreal_vendor_workflow.py doctor --vendor cesium
python tools/unreal_vendor_workflow.py install-smoke --vendor cesium --engine-version 5.7
python tools/unreal_vendor_workflow.py full --vendor cesium
python tools/windows_wheel_workflow.py doctor
```

Example project scaffolds:

- [Cesium Unreal example root](../extensions/cesium/examples/unreal/README.md)
- [Cesium Unity example root](../extensions/cesium/examples/unity/README.md)
- [Cesium Godot example root](../extensions/cesium/examples/godot/README.md)

On the current Windows flow, the typical pattern is:

- Godot native on Windows
- Unity native on Windows
- Unreal native on Windows
- Linux cross-build routes from Windows when Zig or Docker is available
- Windows wheel setup via the MinGW/CMake path

Use `fastdis bootstrap doctor` after `workspace doctor` when you specifically
want the host-smart Godot and Unreal bootstrap preview.

For upstream-facing Cesium compatibility work, treat the public source route as
the first step. Prepare the local Cesium checkouts, then run the selective
vendor lanes so Cesium becomes an early installability gate rather than a late
sample-project surprise.

The FastDIS-owned Cesium example-project layer is separate from those vendor
lanes. Use `python extensions/cesium/tools/cesium_example_workflow.py doctor --engine ...`
to track whether Unreal, Unity, and Godot are ready for matched-quality example
projects before the full demo/runtime automation exists.

For GRILL DIS work, treat the outputs as comparison evidence rather than
FastDIS deliverables. Reuse the shared proof/reporting infrastructure, but keep
the route family and artifact naming explicit so parity work never reads like
primary-product ownership.
