# Alpha 4 Audit Checklist

Alpha 4 is only ready when current evidence proves all of this from the current
tree:

- The native `fastdis` core remains generic and Lattice-specific behavior lives
  in adapter/app layers.
- Canonical entity bridging is documented and implemented.
- Local mock and shim seams exist for entities first, with bounded objects/tasks
  support.
- The operator workflow is runnable without real credentials.
- DIS -> canonical -> publish/stream -> canonical -> DIS is proven through
  generated local artifacts.
- Loop suppression is explicit and tested.
- DIS Entity State egress is valid and replay-friendly.
- Unreal, Godot, and Open-DIS-friendly verification artifacts are present and
  honestly scoped as replay/UDP-friendly outputs, not as a claim of live
  in-engine Lattice runtime integration.
- Real sandbox requirements are called out explicitly and not overstated.

Current operator closeout commands:

```bash
python tools/lattice_workflow.py full
python tools/lattice_workflow.py verify
```

Expected generated outputs under `verification_reports/alpha4/lattice/`:

- `dis_to_shim/dis_to_shim_report.json`
- `shim_to_dis/shim_to_dis_report.json`
- `shim_to_dis/shim_to_dis.fastdispkt`
- `shim_to_dis/canonical_entities.json`
- `lab_state/lab_state_report.json`
- `alpha4_lattice_report.json`
- `alpha4_release_audit_report.json`

Non-goals that must remain explicit:

- official Anduril SDK parity
- real sandbox auth/session integration
- live inbound Lattice -> DIS flow
- live Lattice runtime embedded inside Unreal or Godot
