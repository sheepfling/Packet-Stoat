# Verify Install

Use these checks after installing or downloading a FastDIS product.

## Python / CLI

```bash
fastdis doctor
fastdis release check --quick
```

## Native SDK

```bash
python tools/dev_check.py --native
```

## Unreal

```bash
fastdis engine unreal doctor --engine-version 5.8
fastdis engine unreal install-smoke --engine-version 5.8
fastdis engine unreal verify --engine-version 5.8
```

## Godot

```bash
fastdis engine godot doctor
fastdis engine godot verify
```

## Lattice Lab

```bash
fastdis lattice sdk-check
```

## Deliverables / Proof

```bash
python tools/list_deliverables.py
```

This writes machine-readable and Markdown reports under `build/reports/`.
