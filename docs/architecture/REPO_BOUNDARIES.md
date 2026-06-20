# Repository Boundaries

Packet-Stoat is a native DIS core plus optional adapters. The core package should stay small enough that C, C++, Python, and engine consumers can trust it as a stable packet-processing dependency.

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
- Adapter-specific docs, tests, fixtures, reports, examples, and workflow CLIs.

## Current Adapter Packages

- `integrations/lattice` is the current `packet-stoat-lattice` adapter package. It should be promoted to `packages/lattice` when we do the larger directory migration.
- Unreal and Godot workflows still live under the root examples/tools layout. They should follow the same package boundary after the Lattice split is stable.

## Boundary Rules

- Core code must not import Lattice, Unreal, Godot, HLA, Unity, or vendor SDK modules.
- Core code may define vendor-neutral interop records under `fastdis.interop`.
- Adapter code may depend on `fastdis`, but `fastdis` must not depend on adapter packages.
- Generated reports, benchmark outputs, release artifacts, local build products, and verification run outputs should not be tracked.
- Root-level tools should be core development tools. Adapter workflows should live in their adapter package with short compatibility wrappers only when needed.

See `docs/architecture/LANGUAGE_BOUNDARIES.md` for the language-specific version of these rules.
