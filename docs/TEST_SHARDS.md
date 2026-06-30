# Test Shards

FastDIS now names the main verification surfaces explicitly so a developer can
ask a narrower question than "is the whole repo green?"

## Discover

List the catalog:

```bash
python tools/test_shards.py list
```

Inspect the current host capability model:

```bash
fastdis workspace doctor
fastdis workspace doctor --format summary
python tools/test_shards.py host
```

Run one shard:

```bash
python tools/test_shards.py run python-green
```

Run the local aggregate:

```bash
python tools/test_shards.py run overall-green
```

Run the heavier credential-free release aggregate:

```bash
python tools/test_shards.py run release-ready
```

## Shards

- `python-green`: import, CLI doctor, and the main pytest suite.
- `quality-green`: generated freshness, source cleanliness, docs-link liveness,
  `ruff`, and `pyright`.
- `native-green`: native build plus CTest.
- `lattice-green`: focused Lattice tests, SDK gap report, and
  `packages/lattice` package build.
- `unreal-green`: Unreal doctor plus the current host-lane evidence summary.
- `unity-green`: Unity doctor, native-matrix doctor, and current workflow
  report.
- `godot-green`: Godot doctor.
- `evidence-green`: evidence-pack generation/check plus audit/report receipts.
- `overall-green`: aggregate local green across Python, quality, native,
  engines, Lattice, and evidence.
- `release-green`: release artifact staging/smoke/inspection.
- `release-ready`: `overall-green` plus `release-green`.

## Host Truth

The shards are intentionally tempered by what one host can honestly prove.

- macOS host:
  native runtime/evidence lanes should be treated as `macOS` plus
  `linux-docker` when Docker and staged Linux engine payloads are available.
- Windows host:
  native runtime/evidence lanes should be treated as `Windows` plus
  `linux-docker` when Docker and staged Linux engine payloads are available.
- Linux host:
  native runtime/evidence is local Linux. Cross-platform packaging may still be
  built separately, but native runtime claims should stay Linux-scoped.

That means "overall green" is not "every host and every engine route passed on
this one machine." It means this machine passed every shard it is expected to
own, and wrote honest receipts for the rest.

## Relationship To `dev_check.py`

`python tools/dev_check.py` remains the junior-friendly default entry point.
Use shards when you want a named surface:

- `python-green` for core Python work
- `lattice-green` for the plugin package
- `unreal-green`, `unity-green`, or `godot-green` for engine-specific work
- `overall-green` before a broader handoff
- `release-ready` before a release candidate
