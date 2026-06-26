# FastDIS Unity Orientation Verification

This example project is the explicit orientation-scene proof for the current
FastDIS Unity lane. It complements the UPM package runtime verifier by opening a
real Unity scene, loading the shared orientation fixtures, and checking the
configured scene component against the expected Unity basis vectors.

Current status:

- shared fixture staging is wired in
- a Unity scene and automated Editor runner are present
- the verifier uses Unity `Quaternion.LookRotation(forward, up)` and compares
  `transform.forward`, `transform.right`, and `transform.up` numerically
- the scene is exercised through `python tools/unity_workflow.py orientation-verify --unity-version 6000.5`

## Project Layout

Open this Unity project root:

```text
examples/unity/FastDisOrientationVerification/
```

Key files:

```text
Assets/Scenes/OrientationVerification.unity
Assets/Scripts/FastDisOrientationVerifier.cs
Assets/StreamingAssets/orientation_engine_cases.json
```

The staged fixture is refreshed from the repo root with:

```bash
python tools/sync_orientation_fixtures.py --target unity
```

## What It Verifies

The verifier loads `Assets/StreamingAssets/orientation_engine_cases.json` and
checks the Unity target-frame interpretation:

```text
transform.forward against Cesium/Unity-style forward
transform.right   against expected right
transform.up      against expected up
```

For standalone Unity the expected mapping is:

```text
east  -> +X
up    -> +Y
north -> +Z
```

The current scaffold uses the already-derived `CesiumUnityEastUpNorth` /
`StandaloneUnityEastUpNorth` target-frame output encoded in the shared fixture.
That keeps Unity on the same contract as the rest of the Alpha 2 orientation
work.

## Running It

Automated from the repo root:

```bash
python tools/unity_workflow.py orientation-verify --unity-version 6000.5
```

Manual visual check:

1. Open the project in Unity.
2. Open `Assets/Scenes/OrientationVerification.unity`.
3. Press Play.
4. Read the Console for `PASS` / `FAIL` output.

The scene also draws colored axes:

```text
red    actual forward
green  actual right
blue   actual up
white  expected forward
yellow expected right
cyan   expected up
```

## Role In The Lane

This project is intentionally narrower than the UPM package runtime verifier:
its job is scene-level orientation proof. Replay, UDP ingest, native library
load, and latest-state application are covered by the package workflow under
`tools/unity_workflow.py runtime-verify` and `full`.
