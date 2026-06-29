# Built Deliverables

Use this when double-checking what Packet Stoat built and where the outputs
landed.

## One Command

```bash
python tools/list_deliverables.py
```

Installed-console equivalent:

```bash
fastdis release deliverables
```

The command writes:

- `build/reports/deliverables_report.json`
- `build/reports/deliverables_report.md`

## Main Deliverable Groups

- `build/dist/`: root `fastdis` Python source distribution and wheel artifacts
  exposing the `fastdis` import package and primary `fastdis` CLI.
- `build/cmake/host/libfastdis*` or `build/cmake/host/fastdis.dll`: native C
  ABI shared library.
- `build/cmake/host/fastdis_*`: native tests, examples, and benchmark
  executable.
- `packages/unreal/FastDis/`: Unreal plugin source plus staged ThirdParty
  headers/libs when the Unreal build workflow has run.
- `packages/godot/*/addons/fastdis/`: Godot `.gdextension` descriptors and
  staged native libraries when the Godot build workflow has run.
- `packages/unity/com.sheepfling.fastdis/`: Unity UPM package preview,
  runtime/editor C# sources, tests, docs, samples, and generated logging table.
- `packages/lattice/`: mock-first Anduril Lattice-shaped Python plugin
  package, including package metadata, source modules, fixtures, configs, and
  plugin-entrypoint tests.
- `packages/lattice/dist/`: `packet-stoat-lattice` plugin wheel/sdist when
  the Lattice package build has run.
- `build/benchmark_results/`: local benchmark reports.
- `build/release_artifacts/`: locally staged release assets.
- `build/reports/`: local verification reports.

## Rebuild Commands

Default green check:

```bash
python tools/dev_check.py
```

Full non-destructive local check:

```bash
python tools/dev_check.py --all
```

Focused rebuilds:

```bash
python tools/dev_check.py --package
python tools/dev_check.py --native
python tools/dev_check.py --engine-doctors
python tools/dev_check.py --lattice
python tools/inspect_alpha5_release_artifacts.py
```

Clean local outputs:

```bash
python tools/clean_artifacts.py --apply
```

Build only the Lattice plugin package:

```bash
python -m build packages/lattice
```

## Notes

Generated outputs and built deliverables are intentionally not committed. The
report is for local verification and release staging, not source control.

See [Artifact Layout](ARTIFACT_LAYOUT.md) for the full build-output policy.

The Lattice package is intentionally separate from the `fastdis` parser/runtime
core. It is a public-docs-aligned, mock-first adapter harness; live Anduril
Lattice endpoint behavior still requires real credentials and must be verified
through explicit live checks.

For the target Alpha5 release asset matrix, see
[Release Artifacts](RELEASE_ARTIFACTS.md).
