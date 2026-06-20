# Alpha 4.1 Goal

Objective:
Deliver a no-credential compatibility pass on top of Alpha 4 so the Lattice
bridge is public-doc-conformant, dry-run SDK-shaped, gRPC-contract-aware, and
explicit about the small set of remaining gaps that still require real sandbox
credentials.

Completion standard:

- Alpha 4.1 planning docs are on disk.
- Current emitted payloads can be contract-audited into a JSON/Markdown report.
- The real backend stub supports dry-run construction with SDK-like config
  names and no accidental network dependency.
- Sample/SDK parity can be audited into a machine-readable gap report.
- The high-rate publish/stream seam is planned as a Packet-Stoat-owned gRPC
  contract, not an overclaimed vendor API clone.
- Optional SDK import tests exist and do not fail the repo when the public
  package is absent.

Primary execution order:

1. Put the Alpha 4.1 plan and goal docs on disk.
2. Add the payload contract audit.
3. Tighten the real backend dry-run/config surface.
4. Add the sample/SKD parity audit and combined gap report.
5. Extend the plan with the no-credential gRPC publish/stream contract lane.
6. Add tests and run them locally.

Non-goals:

- Do not claim real sandbox verification.
- Do not grow the mock into a fake full Lattice platform.
- Do not weld vendor SDK types into the fastdis core parser/runtime.
- Do not start with a full official vendor gRPC service clone.
