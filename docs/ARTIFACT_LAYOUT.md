# Artifact Layout

FastDIS keeps source files at the repo top level, transient compiler/build
state under `build/`, and human-inspectable local outputs under `artifacts/`.

## Policy

- `build/` is scratch space: compiler outputs, extracted dependencies, staging
  trees, throwaway work products, and tool-only environments. Nothing under
  `build/` should be treated as persistent evidence.
- `artifacts/` is for regenerable local outputs that humans inspect:
  benchmark receipts, verification reports, smoke logs, release bundles, and
  comparison summaries. These are intentionally ignored by git.
- Checked-in examples that tests or docs need must live outside `build/` and
  `artifacts/`, typically under `tests/data/` or a docs/examples location.
- `generated/` is reserved for maintained generated source inputs, not current
  runtime reports.

## Default Output Roots

- `build/cmake/host/`: host CMake build tree for native library/tests/tools.
- `build/cmake/mingw-win64/`: MinGW Windows cross-build tree.
- `build/cmake/linux-x86_64/`: Linux Docker cross-build tree.
- `artifacts/dist/`: Python wheels and source distributions.
- `artifacts/benchmark_results/`: benchmark JSON, Markdown summaries, and payloads.
- `artifacts/release_artifacts/`: locally staged release zips, manifests, and checksums.
- `artifacts/reports/`: verification, doctor, smoke, deliverables, and
  benchmark/comparison reports.
- `artifacts/verification_reports/`: historical or lane-specific verification
  reports that are useful locally but should not sit at repo root.
- `build/tool_venvs/`: tool-only virtual environments, such as fallback `twine`.

## What Not To Do

- Do not treat `build/reports/` as a canonical location for current reports.
- Do not make tests depend on whatever happens to exist in a developer's local
  `artifacts/` tree unless that test is explicitly an operator/workflow test.
- Do not check in "current" benchmark outputs. Check in only small deterministic
  fixtures or examples.

## Controlled Generated Files

`generated/` is not a generic dumping ground. It is reserved for generated
project inputs that are checked by freshness tests, such as DIS IR/catalog
manifests and shallow fuzz corpus metadata. Temporary generator output belongs
under `build/` when it is compiler-style scratch state, or under `artifacts/`
when it is meant to be inspected by humans and regenerated locally.

## Cleaning

Dry-run cleanup:

```bash
python tools/clean_artifacts.py
```

Delete local artifacts and caches:

```bash
python tools/clean_artifacts.py --apply
```

This removes `build/`, legacy root artifact folders such as `dist/` and
`release_artifacts/`, Python/test caches, and Windows-mangled staging folders
such as drive-root engine scratch folders.

## Rebuild

Run the standard local green check:

```bash
python tools/dev_check.py --quick
```

Run credential-free release gates:

```bash
python tools/dev_check.py --release-ready --allow-credential-blockers
```

The release-ready path stages local artifacts, smoke-tests them, and then runs
artifact inspection for:

- forbidden local paths such as `.venv/`, `.git/`, `build/`, `dist/`, and
  cache folders
- secret-like payloads such as private keys, PyPI tokens, GitHub tokens, and
  OpenAI keys
- unexpected artifact names or stale version tags
- invalid zip/checksum/manifest relationships
- binaries accidentally included in source archives
