# Language Boundaries

Packet-Stoat should keep language choices tied to ownership and performance requirements. The native core owns DIS packet work; adapter packages own vendor and workflow behavior.

## Policy

- Core native code owns DIS parsing, DIS encoding, entity tables, snapshot buffers, frame transforms, orientation transforms, and the stable C ABI.
- Core Python owns thin bindings, replay helpers, generic canonical interop records, plugin discovery, and developer workflow glue.
- Lattice-specific behavior belongs in `packet-stoat-lattice`, not in `libfastdis`.
- Real Lattice SDK imports, auth, entity JSON/protobuf names, Objects, Tasks, stream behavior, and mock/shim servers must not be required to build or import the fastdis core.
- C/C++ may be used for a future Lattice sidecar only after real credentials and measurements show the Python adapter path cannot satisfy a concrete throughput or latency requirement.

## Current Split

| Component | Primary language | Reason |
| --- | --- | --- |
| DIS header scanning | C/C++ | Hot-path packet handling. |
| Entity State parse/encode | C/C++ | Shared by engines, Python, replay, and future adapters. |
| Entity table and snapshot buffer | C/C++ | Runtime state handoff and engine frame timing. |
| C ABI | C | Stable cross-language boundary. |
| C++ RAII wrapper | C++ | Native ergonomics without changing the ABI. |
| Canonical entity records | Python now, C ABI later if needed | Vendor-neutral bridge surface. |
| Lattice payload builders | Python | Schema and contract iteration. |
| Lattice mock/shim servers | Python | Test/control-plane behavior, not core packet throughput. |
| Lattice object/task harness | Python | Workflow-heavy and credential-gated. |
| Lattice gRPC contract tests | Python first | Local proof without sandbox credentials. |
| Future real high-rate Lattice bridge | Go/Rust/Python first, C++ optional | Decide from real measurements, not speculation. |
| Unreal/Godot runtime plugins | C++/C ABI | Engine-native integration. |

## Dependency Rules

- `import fastdis` must not import Lattice, Unreal, Godot, HLA, Unity, gRPC, protobuf, or Anduril SDK modules.
- Adapter packages may depend on `fastdis`.
- `fastdis` must not depend on adapter packages.
- Optional adapter dependencies belong in adapter package metadata.
- Dry-run and mock adapter paths must run without credentials.
- Live adapter paths must fail with clear configuration errors when credentials or endpoints are missing.

## Acceptable Future Native Lattice Work

The only Lattice-adjacent native work that belongs near core is vendor-neutral:

- A canonical entity snapshot ABI.
- A generic DIS Entity State writer ABI.
- Generic source/provenance fields that can feed Lattice, HLA, engines, JSONL, or custom consumers.

Avoid native APIs named after Lattice unless they live in a separate adapter or sidecar package.
