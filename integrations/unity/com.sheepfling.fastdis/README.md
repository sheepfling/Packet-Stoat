# FastDIS for Unity

FastDIS for Unity is a Unity Package Manager package that wraps the native
`libfastdis` C ABI through C# P/Invoke and exposes Unity-friendly scanning,
snapshot, network, replay, and transform helpers.

Install from Git during alpha:

```text
https://github.com/sheepfling/Packet-Stoat.git?path=integrations/unity/com.sheepfling.fastdis
```

Alpha scope:

- desktop native plug-in layout for Windows, macOS, and Linux
- C# wrapper over the stable FastDIS C ABI
- Unity ENU mapping profile: East -> +X, Up -> +Y, North -> +Z
- runnable Unity ingest loop: scanner, latest-state table, snapshots, replay,
  UDP receiver with unicast and multicast receive, UDP sender with raw and
  Entity State send, entity mapping, stale-timeout lifecycle removal, and
  native dead-reckoning plus smoothing application
- Unity runtime event surfaces for Fire, Detonation, Start/Resume, and
  Stop/Freeze PDUs through `FastDisWorld`
- Unity runtime event surfaces for Designator, Signal, and Electronic
  Emissions PDUs through `FastDisWorld`
- heartbeat and threshold-based Entity State publishing through
  `FastDisEntityPublisher`
- policy-driven ground clamp and distance-culling controls in `FastDisWorld`
- sender mode coverage for unicast, multicast, and broadcast destinations
- wildcard and priority-aware entity mapping rules in `FastDisEntityMapping`
- beta1 parser-backed event surfaces for Transmitter, Receiver, IFF, Attribute,
  Directed Energy Fire, and Entity Damage Status
- beta1 collision and collision-elastic event surfaces through the same Unity
  runtime path
- cross-engine equivalence report generation for the shared Unity/Unreal/Godot
  deep-row surface
- head-to-head benchmark readiness report generation that stays incomplete
  until a GRILL Unity baseline payload is present
- package doctor, bridge probe, runtime verification, and diagnostics window
- samples for receiver, UDP loopback, orientation verification, and Lattice Lab bridge

The package does not claim Unity Asset Store readiness yet. Git/UPM install and
GitHub Release `.tgz` packages are the first target.

## Workflow

From the repository root:

```bash
python tools/unity_workflow.py doctor --unity-version 6000.5
python tools/unity_workflow.py build --all-native
python tools/unity_workflow.py bridge-probe
python tools/unity_workflow.py parity-check --milestone alpha6
python tools/unity_workflow.py orientation-verify --unity-version 6000.5
python tools/unity_workflow.py startup-probe --unity-version 6000.5
python tools/unity_workflow.py install-smoke --unity-version 6000.5
python tools/unity_workflow.py runtime-verify --unity-version 6000.5
python tools/unity_workflow.py grill-import-smoke --unity-version 6000.5
python tools/unity_workflow.py grill-baseline-init --unity-version 6000.5.0f1 --scene LoopbackBench --traffic-mix "100% Entity State" --overwrite
python tools/unity_workflow.py cross-engine-equivalence
python tools/unity_workflow.py head-to-head-benchmark
python tools/unity_workflow.py full --unity-version 6000.5
```

Current verification posture:

- `doctor`, `build`, `verify`, and `bridge-probe` are credential-free.
- `parity-check` turns the Unity-vs-GRILL milestone plan into a machine-readable
  gate backed by `docs/research/unity_grill_parity.yaml`.
- `build --all-native` is the single Mac-native payload lane: it builds the
  cross-target matrix, stages the Unity plug-ins, and writes
  `build/reports/unity_native_matrix.json` plus `.md`.
- `orientation-verify` runs the example Unity orientation scene and writes
  `build/reports/unity_orientation_verification.json` and `.md`.
- `startup-probe` launches the smallest possible scratch Unity project and
  verifies that the host can begin project import before the slower install
  smoke lane runs.
- `install-smoke` installs the package from a temporary git repo into a clean
  Unity project and writes `build/reports/unity_install_smoke.json` plus
  `unity_install_smoke_<host>.json` and matching Markdown.
- If `startup-probe` or `install-smoke` reports `failure_stage=host-startup`
  or `failure_reason=project-import-never-started`, Unity never began importing
  the scratch project on that host. Repair the Unity/OS host first.
- `install-matrix` is optional follow-on evidence that aggregates host
  install-smoke reports into `build/reports/unity_install_matrix.json` and
  `.md`.
- `adopt-install-smoke` normalizes a Windows or Linux host report into the
  local `build/reports/` bundle when you want optional portability evidence.
- `capture-host-report`, `stage-host-report`, `export-host-report`,
  `import-host-report`, `sync-host-reports`, `host-matrix`, and `signoff`
  provide the optional cross-host bundle flow for macOS/Windows/Linux install
  proof.
- `cross-engine-equivalence` writes the Unity-facing summary of the shared
  Python/Unity/Unreal/Godot evidence to
  `build/reports/unity_cross_engine_equivalence.json` and `.md`.
- `head-to-head-benchmark` writes the benchmark readiness summary to
  `build/reports/unity_head_to_head_benchmark.json` and `.md`, and stays
  intentionally incomplete until a GRILL Unity baseline payload is present.
  Use `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.template.json`
  as the capture contract for that external baseline.
- `grill-baseline-init` scaffolds
  `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json`
  from the tracked template and pre-populates `results[]` from the current
  FastDIS native benchmark case list so the external GRILL run starts from a
  concrete comparison matrix.
- `grill-import-smoke` builds a scratch Unity project, copies the GRILL plugin
  into `Assets/`, and records whether the current host can even begin importing
  it before benchmark capture work starts.
- `runtime-verify` launches a scratch Unity project and writes human-readable
  reports under `build/reports/`.
- `unity_workflow_report.md` distinguishes the macOS install proof from the
  optional cross-host install matrix. A single green macOS host run is enough
  for the Mac proof lane.
- On Unity Personal hosts, runtime verification can be blocked by local editor
  entitlement state. When that happens, inspect
  `build/reports/unity_runtime_verification.md` and
  `build/reports/unity_editor_method.log`.

To aggregate optional cross-host install proof from a remote machine, prefer a
staged host bundle over copying just the raw install-smoke JSON:

```bash
python tools/unity_workflow.py capture-host-report --host-label windows-lab-a --host-platform windows --unity-version 6000.5
python tools/unity_workflow.py import-host-report dist/unity_host_reports/windows-lab-a.zip
python tools/unity_workflow.py import-host-report dist/unity_host_reports/linux-lab-a.zip
python tools/unity_workflow.py sync-host-reports
python tools/unity_workflow.py host-matrix
python tools/unity_workflow.py signoff
python tools/unity_workflow.py report --out-dir build/reports
```

See `docs/UNITY_CROSS_HOST_SIGNOFF.md` for the full external-host handoff flow.

## Native Payload Matrix

From the repository root:

```bash
python tools/build_unity_native_matrix.py doctor
python tools/build_unity_native_matrix.py build --targets macos windows linux --keep-going
```

The matrix uses:

- macOS: host CMake build.
- Windows: MinGW-w64 cross compile.
- Linux: Docker `linux/amd64` build.

Successful staging produces:

- `Runtime/Plugins/macOS/libfastdis.dylib`
- `Runtime/Plugins/Windows/x86_64/fastdis.dll`
- `Runtime/Plugins/Linux/x86_64/libfastdis.so`

These native payloads are generated artifacts and are not committed.

## Package Documents

- [Changelog](CHANGELOG.md)
- [License](LICENSE.md)
- [Third Party Notices](Third%20Party%20Notices.md)
