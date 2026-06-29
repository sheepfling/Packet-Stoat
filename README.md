# FastDIS

FastDIS is a native-first simulation ingress/egress toolkit for DIS traffic,
game engines, and Lattice-shaped integration workflows. `Packet-Stoat` remains
the repository codename; the published Python package, CLI, and native SDK
surface are `fastdis`.

It is built around three lanes:

- **Python / fastdis core**: a NumPy-free DIS scanner, Entity State fast path,
  replay/UDP tooling, and stable C ABI.
- **Engine workflows**: Unreal and Godot build/stage/verify paths for native
  packet ingest, latest-state tables, and frame-safe snapshot handoff.
- **Lattice Lab**: a public-docs-aligned bridge from DIS/native simulation
  state into Lattice-shaped Entities, Objects, and Tasks workflows, with the
  preferred mock backend owned externally by `zorn`.

## Install

```bash
python -m pip install -e '.[dev]'
fastdis doctor
```

The editable `.[dev]` install also brings in the local Godot build toolchain
helper `scons`, which the Godot GDExtension route uses on Windows.

## Three Quickstarts

Python:

```bash
fastdis recv --bind 127.0.0.1 --port 3001 --max-packets 10 --surface python
fastdis send-entity --dst 127.0.0.1 --port 3001 --count 10 --rate-hz 30
```

Engines:

```bash
fastdis engine unreal doctor --engine-version 5.8
fastdis engine godot doctor
```

On Windows, Godot is the intended engine path here. You still need a Godot
executable on `PATH` or pointed to by `FASTDIS_GODOT`. If
`examples/godot/fastdis_gdextension/godot-cpp` is missing, the new bootstrap
lane will fetch it automatically before the wrapper builds.

Lattice Lab:

```bash
python tools/lattice_backend.py doctor
fastdis lattice doctor
fastdis lattice sdk-check
```

Verification shards:

```bash
python tools/test_shards.py list
python tools/test_shards.py run python-green
python tools/test_shards.py run overall-green
```

## What Works Today

- DIS 6/7 header scanning and generated PDU catalog metadata.
- High-quality Entity State fast path, compact transforms, latest-state table,
  and snapshot buffers.
- C ABI shared library, header-only C++ wrapper, and Python convenience API.
- UDP send/receive/capture/replay utilities for local verification.
- Unreal and Godot workflow scripts for discovery, build/staging, demos, and
  orientation verification scaffolds.
- Lattice-shaped payload mapping, workflow wrappers, and an external-backend
  contract for no-credential Lattice mock verification.
  The mock/live backend route is designed to be swappable through config rather
  than by changing FastDIS workflow commands.

## What Is Intentionally Not Claimed

- FastDIS is not yet a complete semantic parser for every DIS PDU body.
- FastDIS is not a full OpenDIS object-model replacement.
- FastDIS is not an official Anduril Lattice SDK or official integration.
- Lattice live sandbox behavior is not proven until real credentials and a real
  endpoint are available.
- Orientation is not raw DIS Euler passthrough; engine orientation must go
  through named basis/quaternion profiles and verification.

## Operator CLI

```bash
fastdis doctor
fastdis recv --help
fastdis send-entity --help
fastdis replay-send --help
fastdis bench --help
fastdis engine unreal doctor --engine-version 5.8
fastdis engine godot doctor
fastdis lattice sdk-check
fastdis release alpha4-1-gap
```

The CLI is a thin stable wrapper over the lower-level Python modules and
workflow scripts in `tools/`.

## Core Architecture

```text
DIS UDP/replay bytes
  -> fastdis native scanner
  -> Entity State fast path
  -> latest-state entity table
  -> snapshot buffers / canonical entities
  -> Python tools, Unreal, Godot, or Lattice bridge adapters
```

The stable native boundary is the C ABI in `include/fastdis/fastdis.h`. The C++
API is a header-only RAII convenience wrapper, and Python can use either the
pure Python scanner, optional CPython accelerator, or shared-library C ABI.

## Docs

- [Documentation index](docs/README.md)
- [Project positioning](docs/PROJECT_POSITIONING.md)
- [Python quickstart](docs/PYTHON_QUICKSTART.md)
- [OpenDIS compatibility](docs/OPENDIS_COMPATIBILITY.md)
- [DIS full coverage plan](docs/DIS_FULL_COVERAGE_PLAN.md)
- [PDU standard backbone](docs/PDU_STANDARD_BACKBONE.md)
- [PDU coverage](docs/PDU_COVERAGE.md)
- [SISO enum coverage](docs/ENUM_COVERAGE.md)
- [Typed PDU coverage](docs/TYPED_PDU_COVERAGE.md)
- [Semantic PDU coverage](docs/SEMANTIC_PDU_COVERAGE.md)
- [DIS 6/7 version translation](docs/DIS_VERSION_TRANSLATION.md)
- [DIS 6/7 translation matrix](docs/DIS6_DIS7_TRANSLATION_MATRIX.md)
- [Generated message views](docs/GENERATED_MESSAGE_VIEWS.md)
- [Endpoint coverage](docs/ENDPOINT_COVERAGE.md)
- [Engine quickstart](docs/ENGINE_QUICKSTART.md)
- [FastDIS Symbols extension](docs/FASTDIS_SYMBOLS.md)
- [Sim regression harness](docs/SIMTEST.md)
- [Unreal version matrix](docs/UNREAL_VERSION_MATRIX.md)
- [Godot workflow](docs/GODOT_WORKFLOW.md)
- [Unity competitive scan](docs/research/unity_dis_scan.md)
- [Godot competitive scan](docs/research/godot_dis_scan.md)
- [Cross-engine positioning](docs/research/fastdis_cross_engine_positioning.md)
- [Orientation conventions](docs/ORIENTATION_CONVENTIONS.md)
- [Orientation verification](docs/ORIENTATION_VERIFICATION.md)
- [Lattice Lab quickstart](docs/LATTICE_LAB_QUICKSTART.md)
- [Lattice backend contract](docs/LATTICE_BACKEND.md)
- [Lattice live sandbox boundary](docs/LATTICE_LIVE_SANDBOX_BOUNDARY.md)
- [Repo boundaries](docs/architecture/REPO_BOUNDARIES.md)
- [Plugin system](docs/architecture/PLUGIN_SYSTEM.md)
- [Development checks](docs/DEVELOPMENT_CHECKS.md)
- [Test shards](docs/TEST_SHARDS.md)
- [Artifact layout](docs/ARTIFACT_LAYOUT.md)
- [Built deliverables](docs/DELIVERABLES.md)
- [Release artifacts](docs/RELEASE_ARTIFACTS.md)
- [Storefront visuals](docs/STOREFRONT_VISUALS.md)
- [Publishing bootstrap](docs/PUBLISHING_BOOTSTRAP.md)
- [Publishing references](docs/PUBLISHING_REFERENCES.md)
- [Install guide](docs/INSTALL.md)
- [Verify install](docs/VERIFY_INSTALL.md)
- [Alpha5 release checklist](docs/ALPHA5_RELEASE_CHECKLIST.md)

## Development

```bash
python tools/dev_check.py
python tools/list_deliverables.py
python tools/clean_artifacts.py
fastdis release check --quick
```

Disposable reports, benchmark outputs, release bundles, build products, and
verification artifacts live under `build/` by default and should not be
committed.

For the full local non-destructive matrix, run:

```bash
python tools/dev_check.py --all
fastdis release check --all
```

This runs the fast Python lane, generated freshness checks, native build/CTest,
package build checks, engine doctors, and the Lattice SDK gap report. Engine
doctor failures are reported as warnings because Unreal/Godot installs are
host-specific.
