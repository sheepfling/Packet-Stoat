# Development Checks

FastDIS standardizes local orchestration around Python. Do not add a second
task-runner layer for ordinary repo verification.

## Default Green Check

Run this before committing:

```bash
python tools/dev_check.py
```

Equivalent installed-console command:

```bash
fastdis release check
```

This lane bootstraps ignored generated artifacts, checks generated freshness,
runs `ruff`, runs `pyright`, and runs the Python test suite.

## Full Local Non-Destructive Check

Run this before tagging or handing work to someone else:

```bash
python tools/dev_check.py --all
```

Equivalent installed-console command:

```bash
fastdis release check --all
```

This adds native build/CTest, Python package build, Unreal/Godot doctor checks,
and the Lattice SDK gap report. Engine doctor failures are warnings because
engine installs are host-specific.

## Credential-Free Release Gate

Run this before cutting the Alpha5 release candidate:

```bash
python tools/dev_check.py --release-ready
```

Equivalent installed-console command:

```bash
fastdis release check --release-ready
```

If you want the “everything except external credentials/licenses” gate, use:

```bash
python tools/dev_check.py --release-ready --allow-credential-blockers
```

This treats known credential/license blockers, such as an installed but
unactivated Unity Editor, as warnings while still writing the runtime report.

This adds the release-grade lanes:

- native build and CTest
- Python sdist/wheel build
- `twine check`, bootstrapped in a local `build/tool_venvs/twine` environment
  if needed
- Unreal/Godot/Unity doctors
- Unity scratch-project runtime verification through the FastDIS in-Editor
  executeMethod harness
- native + Python ctypes benchmark report generation
- Lattice SDK gap report
- local release artifact staging under `build/release_artifacts/alpha5/`
- install-from-artifact smoke for the staged wheel and ZIP integrity/checksums

Unity runtime verification may report `blocked_license` if the Unity Editor is
installed but not activated, or if a local Unity Personal install is forced down
the `-batchmode`/`-nographics` path that requires the separate headless
entitlement. On macOS the default verifier uses a login-shell-launched Editor
method so the signed-in Unity Hub license remains visible. Failure reports
include `diagnostic_code` and `remediation` fields in
`build/reports/unity_runtime_verification.json`.

## Focused Lanes

```bash
python tools/dev_check.py --native
python tools/dev_check.py --package
python tools/dev_check.py --engine-doctors
python tools/dev_check.py --unity-runtime
python tools/dev_check.py --benchmarks
python tools/dev_check.py --lattice
python tools/dev_check.py --release-artifacts
python tools/dev_check.py --pytest-args tests/test_packet_stoat_cli.py
```

## Built Deliverables

After running a check, list the built outputs with:

```bash
python tools/list_deliverables.py
```

Equivalent installed-console command:

```bash
fastdis release deliverables
```

## Cleaning Local Outputs

Preview what would be removed:

```bash
python tools/clean_artifacts.py
```

Delete local build products, legacy root artifacts, and caches:

```bash
python tools/clean_artifacts.py --apply
```

Equivalent installed-console command:

```bash
fastdis release clean --apply
```

See [Artifact Layout](ARTIFACT_LAYOUT.md) for the canonical output paths.

## Policy

- Python is the bootstrap requirement.
- Generated bootstrap includes catalog, normalized IR, generic message views,
  endpoint mapping, and shallow fuzz corpus artifacts.
- Generated reports, build outputs, release artifacts, and benchmark outputs
  stay uncommitted.
- Disposable outputs should land under `build/`; root-level `dist/`,
  `release_artifacts/`, `benchmark_results/`, `verification_reports/`, and
  `build-*` directories are legacy clutter and should be cleaned.
- `tools/dev_check.py` is the single local orchestration entry point.
- Engine-specific scripts remain lower-level implementation details wrapped by
  `fastdis engine ...`.
