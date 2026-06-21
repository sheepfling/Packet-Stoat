# Orientation Assurance

FastDIS orientation support is verified through named physical axes, not raw
Euler passthrough. The closeout command is:

```bash
python tools/run_orientation_assurance.py --out build/verification_reports/orientation_current
```

This default run is safe for development machines and CI because it does not
launch Unreal or Godot. It still runs the canonical fixture contract, native
orientation report, SciPy/SymPy pytest oracle lanes, deterministic visual
projection artifacts, contact-sheet generation, and known-bad projection checks.

To include live engine runtime lanes:

```bash
python tools/run_orientation_assurance.py \
  --out build/verification_reports/orientation_current \
  --run-engine-runtimes \
  --engine-version 5.8
```

## Three-Engine Visual Summary

Run the positive Unreal/Godot/Unity projection checks and the known-bad negative
controls with:

```bash
python tools/run_engine_orientation_summary.py --refresh
```

Installed-console equivalent:

```bash
fastdis orient summary --refresh
```

The command writes:

- `build/reports/engine_orientation_summary/engine_orientation_summary.json`
- `build/reports/engine_orientation_summary/engine_orientation_summary.md`

The summary separates two percentages:

- `positive_pass_percent`: good Unreal/Godot/Unity numeric and projection
  cases. This must be 100%.
- `known_bad_detection_percent`: intentionally broken mappings. These must be
  detected as failures and do not count against positive pass percentage.

## Outputs

The command writes:

- `orientation_assurance_summary.json`
- `orientation_assurance_summary.md`
- `fixture_contract_report.json`
- `orientation_verification_report.json`
- `orientation_visual_report.json`
- `orientation_visual_review/index.html`
- raw logs for each executed lane

## Fixture Contract

The canonical fixture is `tests/data/orientation_engine_cases.json`.

It must carry, for every case:

- DIS `psi/theta/phi`
- body FRD basis in ECEF
- body FRU basis in ENU
- Unreal forward/right/up expectations
- Godot forward/right/up expectations
- numeric tolerances

The validator is:

```bash
python tools/check_orientation_fixture_contract.py
```

It checks schema, required keys, finite vectors, unit length, orthogonality, and
determinant sanity.

## Status Language

The summary uses explicit claims:

- `orientation_not_claimable`: a required lane failed.
- `position_verified_orientation_opt_in`: deterministic lanes passed, but live engine runtime lanes were skipped.
- `basis_and_visual_verified_for_requested_lanes`: all requested lanes passed.

This lets release notes distinguish position support, basis-vector support,
visual projection support, and full live in-engine verification without
overclaiming.
