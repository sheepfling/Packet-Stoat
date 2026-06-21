# Unity DIS Scan

## Current Read

Unity is a direct competition lane, not whitespace. GRILL DIS is the baseline to
compare against before making any Unity product claims.

Known public references:

- GRILL DIS Unity repository: `https://github.com/IVCTool/GRILL-DIS-Unity`
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

## Alpha5 / Alpha6 Split

Alpha5:

- research and positioning docs
- UPM package scaffold
- P/Invoke design surface
- frame-transform helper scaffold
- no Asset Store submission

Alpha6:

- native library loads in Unity
- replay demo moves GameObjects
- UDP demo receives packets
- orientation verification scene runs
- Unity benchmark/report lane

## Honest Claim

FastDIS for Unity is not a GRILL DIS replacement yet. The first credible Unity
claim should be native speed, verified transforms, and cross-engine consistency.
