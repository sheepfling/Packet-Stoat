# Lattice Live Sandbox Boundary

Packet Stoat can prepare and validate Lattice-shaped integration behavior
without credentials. It cannot prove real Lattice transport until a real
sandbox endpoint and credentials are available.

## No-Credential Evidence

- DIS Entity State to canonical entity conversion.
- Canonical entity to Lattice-shaped Entity payload conversion.
- Mock publish/store/stream behavior.
- Mock Objects and Tasks seams.
- Mock OAuth client-credentials route.
- Mock environment-token and sandbox-header validation.
- Offline/self-signed client configuration via `SKIP_TLS_VERIFY`.
- REST SDK import/dry-run checks when `anduril-lattice-sdk` is installed.
- Local gRPC-shaped publish/stream contract tests.
- Local gRPC metadata auth checks.

## Credential-Gated Evidence

- Real OAuth/session behavior against a vendor endpoint.
- Real REST endpoint behavior.
- Real gRPC endpoint behavior.
- Real vendor-side validation details.
- Real Objects and Tasks API behavior.

## Live Test Gate

Live tests must remain skipped unless explicitly enabled:

```bash
export LATTICE_LIVE_TESTS=1
export LATTICE_ENDPOINT=...
export LATTICE_CLIENT_ID=...
export LATTICE_CLIENT_SECRET=...
export ENVIRONMENT_TOKEN=...
export SANDBOXES_TOKEN=...
python -m pytest tests/test_lattice_live_endpoint_smoke.py
```

Mutating live tests require a separate explicit opt-in flag and should not run
as part of ordinary CI.

For offline/local Lattice environments with self-signed certificates, the
client-side compatibility switch is:

```bash
export SKIP_TLS_VERIFY=true
```

This is only for offline/local environments where certificate infrastructure is
not available; default clients should continue validating TLS certificates.
