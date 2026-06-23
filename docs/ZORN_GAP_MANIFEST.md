# Zorn Gap Manifest

- backend: `external-zorn`
- transport: `mock`
- zorn_tag: `Alpha1.4`

## Surface Status

- `rest_sdk`: `proven`
  overall_status=ready
- `grpc`: `proven`
  overall_status=ready
- `entity_parity`: `proven`
  overall_status=ready
- `auth_lifecycle`: `gap`
  overall_status=ready-with-gaps

## Gaps

- `auth_lifecycle`:
  - OAuth refresh semantics are not exposed on either REST or gRPC.
  - Request-time scope enforcement is not exposed on REST or gRPC; locked scope only affects token issuance.
  - There is no refresh or revocation route to exercise as part of the Zorn auth lifecycle.
- `backend_cheat_surface`:
  - Task and object verification is bounded to local Zorn endpoint behavior and does not prove real vendor-side auth, storage, or task execution behavior.

## Real Lattice Unknowns

- Real Lattice auth expiry, refresh, and scope semantics remain unknown until a live credential-gated route is exercised.
- Vendor-only stream timing, routing, and backend side effects remain unknown where Zorn does not expose them.
- Objects and tasks are proven only against Zorn's local state machines, not a live vendor backend.
