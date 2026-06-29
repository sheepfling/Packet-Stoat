# FastDIS Unreal Dead Reckoning Runtime Scene

This runtime verification scene contract exercises FastDIS dead reckoning through
the shared native evaluator, not Unreal-specific math.

Fixture:

`tests/data/dead_reckoning_engine_cases.json`

Required runtime behavior:

- Load all 10 standard dead-reckoning algorithm cases.
- Build `fastdis_entity_transform_t` records from the fixture.
- Call `fastdis_extrapolate_entity_transform_dead_reckoning` for each case.
- Apply the resulting transform through the normal Unreal actor mapping path.
- Assert final actor position/orientation against the fixture expected values.
- Emit a JSON report with `schema=fastdis.unreal.dead_reckoning_runtime.v1`.

This file is intentionally part of the Alpha5 coverage surface: the Unreal lane
must use the shared FastDIS native evaluator for parity with C, C++, Python,
Godot, Unity, and Lattice.
