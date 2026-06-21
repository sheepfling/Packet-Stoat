# Lattice Live Sandbox Boundary

Packet Stoat can prepare and validate Lattice-shaped integration behavior
without credentials. It cannot prove real Lattice transport until a real
sandbox endpoint and credentials are available.

## No-Credential Evidence

- DIS Entity State to canonical entity conversion.
- Canonical entity to Lattice-shaped Entity payload conversion.
- Mock publish/store/stream behavior.
- Mock Objects and Tasks seams.
- REST SDK import/dry-run checks when `anduril-lattice-sdk` is installed.
- Local gRPC-shaped publish/stream contract tests.

## Credential-Gated Evidence

- Real OAuth/session behavior.
- Real REST endpoint behavior.
- Real gRPC endpoint behavior.
- Real vendor-side validation details.
- Real Objects and Tasks API behavior.

## Live Test Gate

Live tests must remain skipped unless explicitly enabled:

```bash
export LATTICE_LIVE_TESTS=1
export LATTICE_ENDPOINT=...
export LATTICE_TOKEN=...
export LATTICE_SANDBOX_TOKEN=...
python -m pytest tests/test_lattice_live_endpoint_smoke.py
```

Mutating live tests require a separate explicit opt-in flag and should not run
as part of ordinary CI.

