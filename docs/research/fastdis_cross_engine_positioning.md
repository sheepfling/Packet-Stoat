# FastDIS Cross-Engine Positioning

FastDIS is a cross-engine native DIS ingestion SDK with first-class adapters.
It should not be positioned as only a Python library or only a Unity plugin.

## Engine Lanes

Unreal:

Defense/simulation credibility lane. Keep focus on native plugin packaging,
engine verification, and orientation/georeference proof.

Godot:

Whitespace lane. Aim to be the first polished native Godot DIS plugin with
GDExtension, replay/UDP tooling, and verified transforms.

Unity:

Direct competitor lane. Compare against GRILL DIS and enter with a native-core,
snapshot-driven UPM package after the verification story is strong.

Python:

Tooling and proof lane. Provide packet generation, replay, benchmark, and
inspection workflows that support every engine package.

Lattice Lab:

Integration-simulation lane. Stay mock-first and public-docs-aligned until live
credentials exist.

## Product Priority

1. Python/core/native SDK
2. Unreal
3. Godot
4. Unity
5. Lattice Lab polish in parallel

## Unity Bar

FastDIS should not try to beat GRILL DIS first on PDU breadth. The stronger
Unity differentiators are:

- native C ABI speed
- batch scan and latest-state snapshots
- Python replay/traffic tooling
- cross-engine consistency
- formal frame/orientation verification
- clean UPM install path

PDU breadth can catch up after the pipeline and verification reports are
credible.
