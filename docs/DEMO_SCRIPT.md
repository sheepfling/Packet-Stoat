# Demo Script

This is the short Alpha5 demonstration path.

## 1. Python Fast Path

```bash
python tools/dev_check.py
fastdis doctor
fastdis net-smoke
fastdis send-entity --dst 127.0.0.1 --port 3001 --count 10
```

Explain: FastDIS scans DIS traffic without building a deep Python object
tree for every PDU.

## 2. Engine Path

```bash
fastdis engine unreal doctor --engine-version 5.8
fastdis engine godot doctor
```

Explain: Engines consume changed/stale snapshots once per tick instead of
applying transforms per network packet.

## 3. Lattice Lab

```bash
fastdis lattice doctor
fastdis lattice sdk-check
```

Explain: The Lattice Lab is public-docs-aligned and credential-gated. It proves
mock/shape compatibility, not official live Lattice behavior.

## 4. Boundary Statement

FastDIS is a native-first simulation interoperability lab: a fast DIS core,
engine-ready handoff paths, and a Lattice-shaped integration harness.
