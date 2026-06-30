# Unity Cross-Engine Equivalence

This note defines the current Unity-facing equivalence proof lane.

Current source inputs:

- `docs/message_cross_language_set.json`
- `generated/pdu_log_catalog.json`
- `generated/lattice_dis_mapping_plan.json`
- `artifacts/reports/unity_csharp_bridge_probe.json`

Current report command:

```bash
python tools/build_unity_cross_engine_equivalence_report.py
```

Current report outputs:

- `artifacts/reports/unity_cross_engine_equivalence.json`
- `artifacts/reports/unity_cross_engine_equivalence.md`

The report is allowed to claim cross-engine equivalence only when the audit
evidence shows complete deep-row coverage across C, C++, Python, Unreal,
Godot, and Unity, plus a passing Unity bridge probe.
