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

## Unity

```bash
fastdis engine unity doctor --unity-version 6000.5
fastdis engine unity runtime-verify --unity-version 6000.5
fastdis engine unity orientation-verify --unity-version 6000.5
fastdis engine unity startup-probe --unity-version 6000.5
fastdis engine unity install-smoke --unity-version 6000.5
fastdis engine unity signoff
```

Run `startup-probe` before trusting a failed Unity install smoke on a new host.
If Unity never creates the scratch project `Library/` directory, treat that as
host startup failure rather than package regression.

The `signoff` report now treats the macOS install-smoke lane as the gating
proof. Cross-host install matrices remain available as optional follow-on
evidence, but they do not block the macOS proof lane.

## Lattice Lab

```bash
fastdis lattice sdk-check
```

## Deliverables / Proof

```bash
python tools/list_deliverables.py
```

This writes machine-readable and Markdown reports under `artifacts/reports/`.
