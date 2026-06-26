# Unity DIS Scan

## Current Read

Unity is a direct competition lane, not whitespace. GRILL DIS is the baseline to
compare against before making any Unity product claims.

Known public references:

- GRILL DIS Unity repository: `https://github.com/AF-GRILL/DISPluginForUnity`
- Unity native plug-ins: `https://docs.unity3d.com/Manual/plug-ins-native.html`
- Unity UPM package layout: `https://docs.unity3d.com/Manual/cus-layout.html`

## GRILL DIS Baseline

The GRILL DIS Unity repository documents an existing Unity DIS package with
Entity State handling and several additional PDU paths. FastDIS should not
pitch Unity as an empty space.

Comparison frame:

| Area | GRILL DIS Unity | FastDIS opportunity |
|---|---|---|
| Maturity | Existing Unity package | Needs runnable preview |
| PDU breadth | Broader documented PDU set | Start honest with Entity State |
| Core style | Open-DIS lineage | Flat native C ABI, batch scan, snapshots |
| Install path | Unity package / Asset Store path | UPM Git package first |
| Performance proof | Needs independent review | Publish native + Unity apply benchmarks |
| Orientation proof | Needs research | Use FastDIS basis/quaternion verification |
| Cross-engine story | Unity-focused | Same core across Python, Unreal, Godot, Unity |

## Unity Architecture

Use a UPM package and C# P/Invoke over the stable C ABI:

```text
integrations/unity/com.sheepfling.fastdis/
  package.json
  Runtime/
  Editor/
  Samples~/
  Plugins/
```

Unity supports native plug-ins as platform-specific native libraries that C#
scripts can call. The package should bind only to the C ABI, not the C++ RAII
wrapper.

Target components:

- `FastDisWorld`
- `FastDisNative`
- `FastDisEntityId`
- `FastDisEntityBehaviour`
- `FastDisEntityMap`
- `FastDisReplaySource`
- `FastDisUdpReceiver`
- `FastDisSnapshotApplier`
- `FastDisFrameTransform`
- `FastDisDiagnosticsWindow`

## Frame And Orientation Policy

Unity mapping:

```text
local ENU -> Unity
east  -> +X
up    -> +Y
north -> +Z
```

Orientation must use mapped basis vectors and quaternions:

```csharp
transform.rotation = Quaternion.LookRotation(forward, up);
```

Do not pass raw DIS `psi/theta/phi` into Unity Euler APIs.

## Current FastDIS Read

FastDIS has moved past the original package scaffold:

- UPM package structure exists and follows the normal Unity package layout.
- Native payload staging exists for macOS, Windows, and Linux.
- The Unity runtime lane now includes scanner -> latest-state table ->
  snapshot bridge -> replay player -> UDP receiver -> entity mapping ->
  diagnostics window.
- `tools/unity_workflow.py` provides `doctor`, `build`, `bridge-probe`,
  `startup-probe`, `install-smoke`, `runtime-verify`, `report`, and `full`.
- The workflow report now separates the macOS install proof from optional
  cross-host portability evidence so the Mac exit is not implied away by later
  Windows/Linux work.
- The new startup probe makes host-health failures explicit: if Unity never
  creates `Library/` for a scratch project, that machine is not valid install
  evidence yet.
- The remaining host-specific gap is local host health on macOS until the
  startup probe can create/import a scratch project and install-smoke can run.

## Honest Claim

FastDIS for Unity should not claim broader PDU behavior than it proves. The
credible near-term claim is stronger than scaffold status, though: native-speed
Entity State ingest, verified transforms, replay/UDP demos, and cross-engine
consistency over a shared C ABI.
