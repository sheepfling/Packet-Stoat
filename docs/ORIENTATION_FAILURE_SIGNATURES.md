# Orientation Failure Signatures

Alpha 3 comparison tooling should not stop at "failed." It should classify the
 most likely failure signature.

The point is to accelerate debugging when the mapping is almost right but wrong
in one very specific way.

## Common Signatures

### Forward and Right are both 180 degrees wrong, Up is correct

Likely causes:

- yaw 180 degrees off
- forward axis reversed around up
- asset front/back inverted

### Forward and Right are both about 90 degrees wrong, Up is correct

Likely causes:

- north/east swap
- wrong engine axis-map profile

### Forward is correct, Right and Up rotate together around Forward

Likely causes:

- roll sign error
- asset up-axis error
- post-engine rotation around forward

### Right is correct, Forward and Up are both wrong

Likely causes:

- pitch sign error
- forward/up convention mismatch

### Determinant is about -1

Likely causes:

- reflection / mirror instead of rotation
- handedness mistake
- one axis sign flipped without compensating basis construction

### Debug triad looks correct, mesh nose looks backwards

Likely causes:

- asset authored front does not match assumed forward axis
- Godot `MODEL_FRONT` vs node `FORWARD` mismatch
- Unreal asset local `+X` is not actually the nose

### Unreal actor basis correct, rendered mesh wrong

Likely causes:

- asset basis config wrong
- imported mesh local frame wrong

### Godot basis correct, rendered model wrong

Likely causes:

- `MODEL_FRONT` vs `FORWARD` mismatch
- asset front is `+Z` while config assumes `-Z`

## Tooling Expectations

Future Alpha 3 compare/diagnose tooling should:

- compute axis-angle errors
- inspect determinant / handedness
- inspect marker-point consistency
- emit a likely issue summary
- suggest a config patch when the problem looks like an adapter/asset issue

Example diagnostic:

```text
Most likely issue:
  Godot asset forward axis is positive_z, but config assumes negative_z.
Suggested patch:
  asset.forward_axis: positive_z
```

## Known-Bad Regression Fixtures

Every real orientation bug should become a preserved known-bad fixture.

Suggested directory:

```text
tests/orientation_known_bad/
```

Examples:

- `godot_forward_inverted.yaml`
- `unreal_yaw_180_wrong.yaml`
- `dis_euler_as_local_ypr.yaml`
- `asset_plus_z_front_wrong.yaml`

These fixtures should be expected to fail, with an expected signature such as:

- `forward_error_180`
- `north_east_swap`
- `determinant_negative`
- `asset_front_mismatch`

If a known-bad case starts passing unexpectedly, the verifier likely got weaker
or the failure signature classifier regressed.
