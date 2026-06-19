# Orientation Conventions

Alpha 2 treats orientation as experimental until the full verification plan is
complete. Position-only integration remains the stable path.

Core rule:

```text
Never pass DIS psi/theta/phi directly into Unreal, Unity, Godot, or Cesium HPR.
```

fastdis orientation should flow through named physical axes:

```text
DIS psi/theta/phi
  -> body-FRD basis expressed in ECEF
  -> body-FRU basis expressed in local ENU
  -> target engine basis/quaternion
```

## Canonical Frames

ECEF / WGS84:

- `+X`: equator / prime meridian.
- `+Y`: equator / 90 degrees east.
- `+Z`: North Pole.
- Units: meters for positions, unitless for directions.

Aerospace body FRD:

- `+X`: forward / nose.
- `+Y`: right / starboard.
- `+Z`: down / belly.

Local ENU:

- `+X`: east.
- `+Y`: north.
- `+Z`: up.

fastdis defines:

```cpp
fastdis::orientation::BodyFrdBasisEcef
fastdis::orientation::BodyFruBasisEnu
```

The ECEF position path subtracts the georeference origin and rotates into ENU.
The ECEF direction path rotates only; it never subtracts the origin.

## DIS Orientation

DIS Entity State orientation is decoded as an ECEF-referenced body orientation:

1. Initial body axes coincide with ECEF `X/Y/Z`.
2. Rotate `psi` about ECEF `Z`.
3. Rotate `theta` about the rotated body `Y`.
4. Rotate `phi` about the latest body `X`.

The result is a body-FRD basis in ECEF:

```cpp
BodyFrdBasisEcef body =
    fastdis::orientation::dis_psi_theta_phi_to_body_frd_ecef(psi, theta, phi);
```

Do not write:

```cpp
Actor->SetActorRotation(FRotator(phi, theta, psi)); // wrong
```

## Target Frames

Alpha 2 names target frames explicitly:

- `StandaloneUnrealNorthEastUp`: north -> `+X`, east -> `+Y`, up -> `+Z`.
- `StandaloneUnityEastUpNorth`: east -> `+X`, up -> `+Y`, north -> `+Z`.
- `StandaloneGodotEastUpMinusNorth`: east -> `+X`, up -> `+Y`, north -> `-Z`.
- `CesiumJsEastNorthUp`: east -> local `+X`, north -> local `+Y`, up -> local `+Z`.
- `CesiumUnityEastUpNorth`: east -> `+X`, up -> `+Y`, north -> `+Z`.
- `CesiumUnrealEastSouthUp`: east -> `+X`, south -> `+Y`, up -> `+Z`.

Engine adapters should construct basis matrices/quaternions from mapped
forward/right/up vectors and then query the engine's forward/right/up axes in
tests. Euler output is diagnostic only.

## Alpha 2 Policy

Orientation remains disabled by default until:

- DIS golden fixtures pass.
- An independent oracle agrees.
- Engine basis tests pass.
- Cesium comparison tests pass.
- Visual axis scenes pass numeric dot-product checks.
