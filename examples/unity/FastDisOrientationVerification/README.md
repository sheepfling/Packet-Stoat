# FastDIS Unity Orientation Verification

This is an Alpha 2 Unity verification scaffold. It is not a native fastdis
Unity adapter yet. Its job is to prove the Unity-side target-frame and scene
semantics with the same shared orientation fixture contract used by the native,
Unreal, and Godot harnesses.

Honest current status:

- shared fixture staging is wired in
- a Unity scene and MonoBehaviour verifier are present
- the verifier uses Unity `Quaternion.LookRotation(forward, up)` and compares
  `transform.forward`, `transform.right`, and `transform.up` numerically
- there is still no native fastdis Unity plugin or packet-ingest path

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

## Next Step

The next Unity milestone is to replace the `Quaternion.LookRotation(...)`
scaffold path with a real fastdis native Unity adapter that consumes snapshots
and applies the verified target-frame output directly.
