# Alpha5 Release Checklist

Alpha5 is a polish and credibility release. It should make the existing Python,
engine, and Lattice Lab lanes feel like one coherent project.

## Required Proof

- `python -m pip install -e '.[dev]'` works.
- `python tools/dev_check.py` passes.
- `python tools/test_shards.py run overall-green` passes on the current host
  for the routes that host is expected to prove.
- `python -m pytest` passes.
- `fastdis doctor` works.
- `fastdis release check --quick` works.
- `fastdis net-smoke` passes when the native library is available.
- `fastdis engine unreal doctor --engine-version 5.8` reports a clear
  pass/skip/fix state.
- `fastdis engine godot doctor` reports a clear pass/skip/fix state.
- `fastdis engine unity doctor --unity-version 6000.5` reports separate
  `unity_workflow_status`, `unity_native_status`, `unity_runtime_status`,
  `unity_runtime_launcher`, and `unity_demo_status`.
- `fastdis engine unity runtime-verify --unity-version 6000.5` runs the FastDIS
  in-Editor runtime verification harness in a scratch project, or reports a
  clear `blocked_license` state with `diagnostic_code` and `remediation` when
  the local Unity install is not activated or is forced into a headless path.
- `fastdis engine unity full --unity-version 6000.5` validates the UPM package,
  stages the host native library when available, and runs runtime verification
  unless `--skip-runtime` is passed.
- `fastdis lattice sdk-check` produces the SDK gap report.
- `python tools/test_shards.py run lattice-green` passes and builds from
  `packages/lattice`.
- README clearly separates proven behavior, mock-compatible behavior, and
  deferred live/vendor behavior.
- `fastdis release check --release-ready` runs the credential-free release
  gate: native build/tests, package build, `twine check`, engine doctors, Unity
  runtime verification, benchmarks, Lattice gap report, local release artifact
  staging, and install-from-artifact smoke.
- `fastdis release check --release-ready --allow-credential-blockers` is the
  practical pre-publishing gate when marketplace/vendor/Unity-license access is
  not yet available. It must still produce explicit warning reports for blocked
  credential lanes.

## Release Artifacts

Generated release artifacts should not be committed. If produced for a release
candidate, stage them under `build/release_artifacts/` locally and publish
them as external artifacts with checksums.

Alpha5 should use one release tag with multiple product artifacts:

- Python package/CLI: `fastdis` distribution, `fastdis` import package, `fastdis`
  primary CLI.
- Native C/C++ SDK: headers, shared library, CMake package metadata, smoke
  executable.
- Unreal plugin zip: installable under `Project/Plugins/FastDIS`.
- Godot addon/GDExtension zip: installable under `addons/fastdis`.
- Unity UPM package scaffold: installable by Git URL for research and Alpha6
  preview work.
- Lattice Lab package: mock-first Python plugin package and SDK-gap reports.
- Verification bundle: reports, release manifest, checksums, and SBOM when
  available.

See [Release Artifacts](RELEASE_ARTIFACTS.md) for the product matrix and target
asset names.

## Packaging Checks

- `python tools/dev_check.py --package` builds the root `fastdis` wheel and
  sdist.
- [Publishing Bootstrap](PUBLISHING_BOOTSTRAP.md) is complete enough for
  TestPyPI/PyPI ownership: accounts exist, 2FA is enabled, Trusted Publishing is
  planned/configured, and the `fastdis` distribution name has been verified or
  a fallback distribution name has been chosen.
- `python -m build packages/lattice` builds the `packet_stoat_lattice`
  plugin wheel and sdist.
- `python tools/list_deliverables.py` reports all product groups as present or
  explicitly not built.
- Unity workflow/package/native-staging parity is a PASS for Alpha5.
- Unity Editor runtime verification is Alpha5 scope. On macOS/Unity Personal the
  supported local path is the default login-shell Editor-method launcher. A
  `blocked_license` result means the package runner is wired but the local Unity
  license/entitlement path must be fixed before claiming runtime pass.
- Benchmark artifacts exist under `build/benchmark_results/alpha5/summary.md`,
  `build/benchmark_results/alpha5/qualification.json`, and
  `build/benchmark_results/alpha5/current.json`.
- Local release artifacts stage under `build/release_artifacts/alpha5/` and
  smoke through `tools/smoke_alpha5_release_artifacts.py`.
- `python tools/clean_artifacts.py --apply` returns the repo to a source-only
  local state without deleting tracked source files.
- Native/engine/plugin artifacts are published externally, not committed.

## Stop Criteria

Do not expand Alpha5 into new feature lanes. If a task adds substantial new DIS
PDU semantics, new real vendor transport, or new engine runtime behavior, move
it to Alpha6 or a dedicated follow-up release.
