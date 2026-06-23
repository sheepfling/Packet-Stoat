# FastDIS Simtest

`fastdis simtest` is the engine-agnostic regression harness for Unreal, Godot,
and Unity runtime scenes. It avoids full-frame pixel diffs by comparing
deterministic metadata first and small image crops only where a visual feature
must be checked.

## Contract

An engine runtime verification scene should write a run directory:

```text
build/simtest/runs/<run-id>/
  meta_000000.json
  meta_000330.json
  crops/
    reticle_000330.png
```

Each `meta_*.json` file should contain:

```json
{
  "entities": [
    {
      "id": "100/1/42",
      "type": "airtrack",
      "position": {"x": 1.0, "y": 2.0, "z": 3.0},
      "velocity": [10.0, 0.0, 0.0],
      "orientation": [0.0, 0.0, 0.0, 1.0],
      "status": "live"
    }
  ],
  "camera": {"name": "main"}
}
```

Supported vector field aliases:

- Position: `pos`, `position`, `position_m`
- Velocity: `vel`, `velocity`, `velocity_mps`
- Orientation: `rot`, `rotation`, `orientation`, `orientation_quat`

Orientation quaternions are compared by angular delta in degrees. Three-value
orientation vectors are compared by max absolute component delta.

## Scenario File

The scenario file is JSON so it has no runtime YAML dependency:

```json
{
  "name": "dis_replay_airtrack",
  "seed": 1234,
  "tolerances": {
    "position_m": 0.01,
    "orientation_deg": 0.05,
    "velocity_mps": 0.02
  },
  "crops": {
    "reticle": {
      "metric": "l1",
      "max": 2.0
    }
  }
}
```

Crop files are matched by `<crop-name>_*.png` under each run's `crops/`
directory. Alpha5 implements mean absolute channel error (`l1`) first because it
is deterministic and cheap. SSIM/PSNR can be added later without changing the
metadata contract.

## Commands

Inspect a run:

```bash
fastdis simtest inspect build/simtest/runs/latest
```

Compare a run to a golden baseline:

```bash
fastdis simtest compare \
  build/simtest/runs/latest \
  tests/simtest/baselines/dis_replay_airtrack/golden \
  --scenario tests/simtest/scenarios/dis_replay_airtrack.json \
  --report build/reports/simtest_dis_replay_airtrack
```

Bless an intentional change:

```bash
fastdis simtest bless \
  build/simtest/runs/latest \
  tests/simtest/baselines/dis_replay_airtrack/golden
```

## Source Control Policy

Commit:

- Scenario specs under `tests/simtest/scenarios/`
- Small golden baselines that are required test inputs
- JSON schemas and docs

Do not commit:

- `build/simtest/runs/`
- generated reports under `build/reports/`
- transient full-frame screenshots
- large visual captures that are not explicit golden fixtures

## Engine Integration

Runtime scenes should use a deterministic timeline:

- Fixed seed
- Fixed timestep
- Stable camera
- Motion blur/TAA/eye adaptation disabled where possible
- Metadata emitted from authoritative engine state, not screen scraping

The pass/fail priority is:

1. Entity IDs/types/counts
2. Position, orientation, and velocity tolerances
3. Screen-space crop checks for critical markers/UI
4. Whole-frame images only as manual evidence, not primary gates
