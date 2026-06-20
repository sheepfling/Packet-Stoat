# Lattice Sample Parity

Alpha 4.1 adds a no-credential sample/SDK parity lane.

The goal is not to prove live Lattice transport. The goal is to prove that the
future real backend is shaped like the public SDK and sample material closely
enough that the remaining unknowns are genuinely credential- and endpoint-
dependent.

Current commands:

```bash
python tools/lattice_sample_parity_audit.py
python tools/run_alpha4_1_sdk_gap_report.py
```

Default outputs:

- `verification_reports/alpha4_1/lattice/lattice_sample_parity_report.json`
- `verification_reports/alpha4_1/lattice/lattice_sample_parity_report.md`
- `verification_reports/alpha4_1/lattice/lattice_sdk_gap_report.json`
- `verification_reports/alpha4_1/lattice/lattice_sdk_gap_report.md`

The parity lane checks:

- real-backend config names
- dry-run-safe backend construction
- adapter method surface
- optional public SDK import availability
- optional official REST SDK client construction against the local mock transport
- planned gRPC seam ownership and boundaries
- remaining credential-gated work

This is still not a claim of real sandbox verification. It is an access-ready
compatibility report.

The REST SDK compatibility target is:

- `packet_stoat_lattice.sdk_rest_compat.build_sdk_mock_transport`
- `packet_stoat_lattice.sdk_rest_compat.build_official_lattice_client`
- `tests/test_lattice_sdk_rest_compat.py`

When `anduril-lattice-sdk` is installed, the official `anduril.Lattice` client
can be constructed with a local `httpx.MockTransport` backed by the
Packet-Stoat compatibility harness. Without the SDK installed, route-level
transport tests still exercise the same HTTP paths.

The next scoped extension is the gRPC contract lane:

- Packet-Stoat-owned proto first
- local publish/stream behavior proof
- optional official stub import/serialization later
- no claim of full vendor wire compatibility in Alpha 4.1
