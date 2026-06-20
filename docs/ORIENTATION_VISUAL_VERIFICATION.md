# Orientation Visual Verification

Alpha 3 should treat visual orientation verification as a first-class assurance
lane, not a cosmetic add-on.

The rule is:

```text
numeric engine assertions are the release gate
visual scenes prove the rendered result matches user expectation
screenshot/image tooling makes regressions obvious and reviewable
```

This visual lane depends on the orientation pipeline remaining decomposed and
traceable. See:

```text
docs/ORIENTATION_PIPELINE.md
docs/ORIENTATION_TWEAKING.md
docs/ORIENTATION_FAILURE_SIGNATURES.md
```

Screenshots do not replace basis-vector checks. A mirrored or asset-misaligned
object can look "close enough" from one camera. The numeric basis checks catch
the math. The rendered scenes catch handedness, asset-front, import-axis, and
"looks wrong in the engine" failures.

## Assurance Stack

Use five layers:

1. offline math oracles
2. engine transform assertions
3. deterministic render fixtures
4. automated screenshot/image checks
5. human review contact sheets

Layer 1 remains:

- native C++ fastdis orientation math
- independent Python oracle
- SciPy rotation checks
- SymPy derivation fixtures

Layer 2 remains the release gate:

- apply a fastdis pose to an Unreal actor or Godot node
- read actual forward/right/up from the engine
- compare against expected mapped basis vectors

Layers 3 through 5 raise confidence and make failures legible.

## Canonical Probe Asset

Do not start with realistic aircraft or tank meshes. Start with a canonical
axis probe whose authored local axes are unmistakable.

Suggested probe:

- long red cone/cylinder = forward / nose
- green wing bar = right / starboard
- blue fin/spike = up
- orange belly spike = down
- translucent white ghost triad = expected orientation

Marker points should exist at known local coordinates:

- nose marker = `+forward`
- right marker = `+right`
- top marker = `+up`
- belly marker = `-up`

This lets the verification assert both:

- actor/node basis vectors are correct
- authored mesh markers land in the expected world directions

That catches the common failure where the transform math is right but the mesh
is authored facing the wrong axis.

## Unreal Visual Lane

Unreal baseline assumptions:

- `+X` = forward
- `+Y` = right
- `+Z` = up
- left-handed / Z-up

Required scene contents:

- canonical probe actor
- solid red actual forward arrow
- solid green actual right arrow
- solid blue actual up arrow
- orange actual down arrow
- translucent/dashed expected forward-right-up triad
- local ENU compass triad
- case text: heading/pitch/roll, DIS `psi/theta/phi`, max angle error

Recommended fixed cameras:

- top-down
- north-looking side
- east-looking side
- trailing perspective
- free perspective review shot

Screenshot mode should minimize nondeterministic noise:

- disable motion blur
- disable eye adaptation
- disable contact shadows where possible
- disable anti-aliasing if it harms reproducibility
- use fixed resolution and exposure
- prefer unlit probe materials

Required numerical checks:

- `GetActorForwardVector()` matches expected forward
- `GetActorRightVector()` matches expected right
- `GetActorUpVector()` matches expected up
- marker world directions match the same expectations after asset-basis
  correction

Required output shape:

```text
FASTDIS_ORIENTATION_PASS case=<name> axis=<axis> angle_deg=<value> dot=<value>
FASTDIS_VISUAL_PASS case=<name> camera=<name> screenshot=<path>
```

## Godot Visual Lane

Godot baseline assumptions:

- node forward = `-Z`
- right = `+X`
- up = `+Y`
- imported model front can be `+Z`

Required scene contents match the Unreal probe scene in purpose:

- canonical probe mesh
- actual RGB basis arrows
- expected ghost basis arrows
- local frame triad
- case text and max-angle readout

Numerical checks remain:

- `basis.x` = actual right
- `basis.y` = actual up
- `-basis.z` = actual forward
- determinant near `+1`
- orthogonality and unit-length checks
- marker-position checks for node-forward and model-front modes separately

Screenshot capture must wait until the frame is actually drawn. The runner
should wait for `RenderingServer.frame_post_draw` before saving PNG output.

## Deterministic Visual Cases

The visual lane should cover at least:

- level north
- level east
- level south
- level west
- climb `+20`
- dive `-20`
- bank right `+30`
- bank left `-30`
- heading `135`, pitch `20`, roll `30`
- equator origin north
- near-pole north

These cases should live in:

```text
tests/data/orientation_visual_cases.json
```

They may extend `orientation_engine_cases.json`, but the visual lane should
also include camera and screenshot-specific expectations.

## Automated Image Checks

Golden screenshots alone are useful but insufficient. Add a second semantic
image lane that understands the colored axis overlays.

### Golden image comparison

Use deterministic golden baselines per engine/camera/case.

Artifacts:

- Unreal screenshot baselines and comparison output
- Godot screenshot baselines and comparison output

### Color-axis extraction

Design scenes so computer vision is simple:

- red only = actual forward
- green only = actual right
- blue only = actual up
- white/dashed = expected axes
- gray/black quiet background
- unlit materials

Tools should detect:

- red line direction
- green line direction
- blue line direction

Then compare those against expected screen-space projections.

Known-bad visual cases should not be reported as generic PASS. The review lane
should record them as an expected negative result, for example
`expected-fail-observed`, so a reader can distinguish "the verifier worked" from
"the mapping was correct."

### Screen-space sidecar JSON

Each render should also emit a sidecar JSON, for example:

```json
{
  "case": "climb_north_20",
  "camera": "side_east",
  "expected": {
    "forward_screen": [[512, 384], [690, 318]],
    "right_screen": [[512, 384], [512, 500]],
    "up_screen": [[512, 384], [480, 210]]
  },
  "actual_engine_basis": {
    "forward": [0.9397, 0.0, 0.3420],
    "right": [0.0, 1.0, 0.0],
    "up": [-0.3420, 0.0, 0.9397]
  },
  "max_angle_error_deg": 0.003
}
```

The image checker then compares detected projected axis lines against expected
projected lines.

## Human Review Pack

Generate a visual review pack:

```text
verification_reports/alpha3/orientation_visual_review/index.html
verification_reports/alpha3/orientation_contact_sheet.html
verification_reports/alpha3/orientation_visual_summary.md
```

Recommended contact-sheet layout:

- row = test case
- columns = expected diagram, Unreal render, Godot render, diff/mask

Each case should display:

- case name
- heading/pitch/roll
- DIS `psi/theta/phi`
- expected basis
- actual basis
- max angular error
- PASS / FAIL

## Known-Bad Negative Cases

The verification framework should prove it can fail when a mapping is wrong.

Required negative mappings:

- swap east/north
- invert Godot forward
- treat DIS `psi/theta/phi` as local yaw/pitch/roll
- use Unreal Euler rotator directly
- ignore FRD down/up conversion
- use Godot `MODEL_FRONT` as node forward
- mirror right axis
- flip roll sign
- flip pitch sign

Every negative case should fail via at least one of:

- numeric basis assertions
- screenshot baseline comparison
- color-axis extraction

If a known-bad mapping passes, the visual-verification lane is too weak.

The failure-signature vocabulary should match
`docs/ORIENTATION_FAILURE_SIGNATURES.md` so numeric and visual diagnostics use
the same language.

## Deliverables

Planning and tools:

- `docs/ORIENTATION_VISUAL_VERIFICATION.md`
- `tests/data/orientation_visual_cases.json`
- `tools/compare_orientation_screenshots.py`
- `tools/extract_axis_lines.py`
- `tools/generate_orientation_contact_sheet.py`

Unreal:

- extend `examples/unreal/FastDisOrientationVerification/`
- add screenshot functional tests
- add deterministic screenshot baselines and sidecar metadata

Godot:

- extend `examples/godot/fastdis_orientation_verification/`
- add screenshot save runner
- add sidecar metadata emission

Reports:

- `verification_reports/alpha3/orientation_numeric_unreal.json`
- `verification_reports/alpha3/orientation_numeric_godot.json`
- `verification_reports/alpha3/orientation_visual_unreal/`
- `verification_reports/alpha3/orientation_visual_godot/`
- `verification_reports/alpha3/orientation_contact_sheet.html`
- `verification_reports/alpha3/orientation_visual_summary.md`

## Release Gate

Do not claim fully verified orientation support until all of these are true:

- native orientation oracle passes
- SciPy oracle passes
- SymPy/generated formula checks pass
- Unreal numeric actor-axis checks pass
- Godot numeric basis checks pass
- Unreal screenshots match baseline within policy
- Godot screenshots match baseline within policy
- color-axis extraction agrees with expected projected axes
- human review contact sheet exists
- known-bad mappings fail

When those are true, the project can say:

```text
orientation support is verified through offline math oracles,
in-engine actor/node basis checks, deterministic screenshot baselines,
and visual axis-overlay review for Unreal and Godot
```

For the current repo, the operator-friendly regeneration path is:

```bash
python tools/run_alpha3_verification_closeout.py
```

That wrapper reruns the orientation core, pipeline, visual, and network proof
lanes and then stages the refreshed host bundle.
