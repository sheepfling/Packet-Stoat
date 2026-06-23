# Lattice Contract Audit

Alpha 4.1 adds a machine-readable contract audit for the emitted
Lattice-shaped bridge payloads.

Purpose:

- make public-doc alignment explicit
- make current bridge-sidecar fields explicit
- turn missing public-style fields into a reportable gap instead of a vague note

The contract audit is intentionally honest:

- `pass`
  the emitted payload carries the expected field directly
- `bridge-sidecar`
  the data exists, but only in a Packet-Stoat-specific sidecar or mock shape
- `missing`
  the field is not emitted today

Current command:

```bash
python tools/lattice_contract_audit.py
```

Default outputs:

- `verification_reports/alpha4_1/lattice/lattice_contract_audit_report.json`
- `verification_reports/alpha4_1/lattice/lattice_contract_audit_report.md`

This audit is not a claim of endpoint or protobuf parity. It is a field- and
semantics-level evidence artifact for the current bridge payload shape.

The compatibility harness report adds service-behavior evidence:

```bash
python tools/lattice_compatibility_harness_report.py
```

Default outputs:

- `verification_reports/alpha4_1/lattice/compatibility_harness_report.json`
- `verification_reports/alpha4_1/lattice/compatibility_harness_report.md`

It exercises auth/session checks, the REST OAuth token route, sandbox-header
rejection, offline-client configuration, entity publish/get/stream, object
upload/media linking, and task lifecycle behavior against the local
no-credential harness.
