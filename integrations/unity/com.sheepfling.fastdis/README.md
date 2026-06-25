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
- runnable Unity ingest loop: scanner, latest-state table, snapshots, replay, UDP receiver, entity mapping
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
python tools/unity_workflow.py orientation-verify --unity-version 6000.5
python tools/unity_workflow.py startup-probe --unity-version 6000.5
python tools/unity_workflow.py install-smoke --unity-version 6000.5
python tools/unity_workflow.py runtime-verify --unity-version 6000.5
python tools/unity_workflow.py full --unity-version 6000.5
```

Current verification posture:

- `doctor`, `build`, `verify`, and `bridge-probe` are credential-free.
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
