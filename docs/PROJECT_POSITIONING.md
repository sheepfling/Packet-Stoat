# FastDIS Project Positioning

FastDIS is a native-first simulation interoperability toolkit. The
`fastdis` core handles high-rate DIS packet scanning, Entity State fast paths,
native table/snapshot handoff, and Python/C/C++ access. Optional workflow lanes
prove engine and Lattice-shaped integration behavior without turning the core
into an engine plugin or vendor SDK.

## Audience Stories

Python user:

I need to scan, filter, receive, replay, or summarize DIS traffic without
allocating a full generated Python object tree for every packet.

Engine user:

I need DIS Entity State traffic to drive Unreal actors or Godot `Node3D`
instances through a native latest-state table and frame-safe snapshot handoff.

Integration/simulation user:

I need a mockable bridge between DIS simulation state and Lattice-shaped
Entities, Objects, and Tasks workflows, while staying honest that real Lattice
transport requires sandbox credentials.

## What FastDIS Is

- A DIS 6/7 packet catalog and safe header/min-length handling surface.
- A production-focused Entity State fast path.
- A stable native C ABI with C++ and Python wrappers.
- A replay/UDP/tooling layer for local verification and demos.
- Unreal/Godot workflow scaffolding for build, staging, and verification.
- A Lattice Lab that uses public-docs-aligned payloads, mock transports, SDK
  seams, and credential-gated live checks.
- A separate FastDIS Symbols extension scaffold for tactical symbology policy,
  kept outside the core DIS parser/runtime.

## What FastDIS Is Not

- It is not yet a complete semantic parser for every DIS PDU body.
- It is not a full OpenDIS object-model replacement.
- It is not an official Anduril Lattice SDK or official integration.
- It does not claim real Lattice sandbox verification without credentials.
- It does not map raw DIS Euler angles directly into engine Euler rotations.
- It does not bundle MIL-STD-2525/App-6 rendering or SIDC policy into the core
  package; tactical symbology belongs in the sibling symbols extension.

## Naming

- Public project: FastDIS.
- Repository codename: Packet Stoat.
- Core Python import: `fastdis`.
- Native library: `libfastdis` / `fastdis.dll`.
- Operator CLI: `fastdis`.
- Compatibility CLI alias: `packet-stoat`.
