# Contributing

## Local Baseline

Use Python as the bootstrap/orchestration requirement.

```bash
python -m pip install -e '.[dev]'
python tools/dev_check.py
```

## Before Opening A Change

- keep generated artifacts, reports, wheels, zips, and release bundles out of
  git
- prefer `rg` / `rg --files` for repo search
- use `python tools/dev_check.py` for local green checks
- use `python tools/list_deliverables.py` to inspect built outputs

## Scope Rules

- `fastdis` core stays vendor-neutral
- Unreal, Godot, and Lattice workflows are integration layers
- do not add new task-runner systems when Python orchestration already exists

## Release Discipline

If a change affects installability, packaging, or publish surfaces, update:

- `docs/INSTALL.md`
- `docs/VERIFY_INSTALL.md`
- `docs/RELEASE_ARTIFACTS.md`
- `docs/PUBLISHING_REFERENCES.md`
