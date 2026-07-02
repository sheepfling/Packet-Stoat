# Repository Boundaries

Packet-Stoat is the umbrella workspace and orchestration repo. It contains
three distinct product trees that share infrastructure but should stay clearly
segregated in ownership and claims:

- `FastDIS`: the primary work product.
- `GRILL DIS`: the competitor parity/comparison tree.
- `Cesium`: the vendor dependency and example-project tree.

The FastDIS core package should stay small enough that C, C++, Python, and
engine consumers can trust it as a stable packet-processing dependency.

## Product Trees

### FastDIS Owns

- Native DIS parsing, validation, filtering, entity snapshots, transforms, and
  the stable C ABI.
- Python bindings, C/C++ surfaces, engine-consumable build outputs, DLLs,
  wheels, release bundles, and measurement/orientation proofs.
- FastDIS-owned example projects, showcase assets, and verification flows that
  demonstrate FastDIS itself.

### GRILL DIS Owns

- Competitor baseline captures, head-to-head measurement proofs, parity
  summaries, and blocked-lane reports.
- Engine-focused compatibility tracking against current GRILL DIS behavior.
- Upstream-facing evidence packets and PR-ready artifacts prepared for the
  GRILL DIS maintainers.

### Cesium Owns

- Vendor plugin/source-route preparation, installability checks, and
  compatibility matrices for Cesium-backed engine work.
- The killer-app showcase layer when the example depends on Cesium for its
  value proposition, especially mesh-heavy scene quality.
- Upstream-facing fixes and evidence bundles prepared for Cesium maintainers.

## Core Owns

- DIS packet header scanning, validation, filtering, and catalog dispatch.
- Entity State fast-path parsing and generic entity snapshots.
- The native C ABI and the header-only C++ convenience wrapper.
- Python wrappers for the core library.
- Generic replay, packet, frame-transform, orientation, and canonical interop types.
- Core tests, ABI checks, parser fuzzing, and source-package checks.

## Adapters Own

- Vendor payload shapes and SDK imports.
- Engine-specific build scripts, plugin packaging, scenes, and verification flows.
- Transport behavior such as Lattice mock HTTP, local gRPC shims, real SDK backends, HLA RTI, or future service clients.
- Visualization policy such as MIL-STD-2525/App-6 SIDC mapping, symbol
  descriptors, renderer/baker dependencies, texture atlases, and engine display
  wrappers.
- Adapter-specific docs, tests, fixtures, reports, examples, and workflow CLIs.

## Current Adapter Packages

- `packages/lattice` is the current `packet-stoat-lattice` adapter package.
- Unreal and Godot workflows still live under the root examples/tools layout. They should follow the same package boundary after the Lattice split is stable.
- `extensions/cesium` is the Cesium-specific extension-owned subtree for source
  route prep, Cesium example standards, and future FastDIS-owned Cesium example
  projects.
- `extensions/fastdis-symbols` is the current tactical-symbology sibling
  extension scaffold. It may depend on FastDIS core identity records, but the
  core must not depend on symbol rules, SIDC policy, renderers, or atlases.

## Working Rules By Tree

- FastDIS routes may produce proofs, artifacts, native binaries, wheels,
  release bundles, and owned example outputs across Python and engine surfaces.
- GRILL DIS routes are comparison-only. They should not be described as FastDIS
  deliverables even when they reuse the same measurement/proof machinery.
- Cesium routes should be split between vendor installability work and
  FastDIS-owned example-project work. Do not blur those into generic engine
  proofs.
- Packet-Stoat infrastructure may orchestrate all three trees, but repo-level
  docs and artifacts should name which tree a route belongs to.

## Boundary Rules

- Core code must not import Lattice, Unreal, Godot, HLA, Unity, or vendor SDK modules.
- Core code must not import FastDIS Symbols, MIL-STD-2525/App-6 renderer
  dependencies, symbol atlases, or SIDC mapping policy.
- Core code may define vendor-neutral interop records under `fastdis.interop`.
- Adapter code may depend on `fastdis`, but `fastdis` must not depend on adapter packages.
- Generated reports, benchmark outputs, release artifacts, local build products, and verification run outputs should not be tracked.
- Root-level tools should be core development tools. Adapter workflows should live in their adapter package with short compatibility wrappers only when needed.
- When a workflow exists only to compare against GRILL DIS or validate Cesium,
  keep that naming explicit in commands, docs, and artifacts rather than
  presenting it as generic FastDIS core behavior.

See `docs/architecture/LANGUAGE_BOUNDARIES.md` for the language-specific version of these rules.
