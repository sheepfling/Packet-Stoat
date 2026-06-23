# Zorn Short Matrix

- backend: `external-zorn`
- transport: `mock`
- zorn_tag: `Alpha1.4`

## Legend

- proven: Probe-backed public surface is ready.
- gap: Probe-backed shortfall remains inside Zorn scope.
- unknown: Live Lattice behavior still unknown.
- live-Lattice-skip: Validated locally, but intentionally skipped for live-Lattice claims.

## Matrix

| Surface | Proven | Gap | Unknown | Live-Lattice-skip | Evidence | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `rest_sdk` | ✓ |  |  |  | ready | Public Lattice surface proven by probe report. |
| `grpc` | ✓ |  |  |  | ready | Public Lattice surface proven by probe report. |
| `entity_parity` | ✓ |  |  |  | ready | Public Lattice surface proven by probe report. |
| `rest.static.x_api_key` |  |  |  | ✓ | {"_compat": {"eventType": "CREATE", "sequence": 2}, "entityId": "static-api-key-entity", "entity_id": "static-api-key-entity", "isLive": true, "is_live": true} | Keep this edge on Zorn; the live lane can stay bearer-only or environment-token only. |
| `rest.sandbox.required` |  |  |  | ✓ | {"detail": "Missing sandbox header"} | This is the setup-heavy path that should stay explicit in Zorn probes. |
| `rest.sandbox.bearer_only` |  |  |  | ✓ | {"detail": "Missing bearer token"} | Documents that sandbox headers do not replace bearer auth. |
| `rest.auth_mode.none` |  |  |  | ✓ | {"_compat": {"eventType": "CREATE", "sequence": 1}, "entityId": "none-auth-entity", "entity_id": "none-auth-entity", "isLive": true, "is_live": true} | Useful for local probe scaffolding, not for live Lattice parity. |
| `rest.oauth.client_credentials` | ✓ |  |  |  | {"access_token": "zorn-oauth-dev.eyJleHAiOjE3ODIxODQ4NTQsImlhdCI6MTc4MjE4MTI1NCwianRpIjoiOTA2NGE2Y2YyNzhjMmUzZmJlNDY5MGJhIiwic2NvcGUiOiJlbnRpdGllcyBzdHJlYW1zIn0.1a2effd37548c297d6aa17edd84f48e0b3e0e12e14009d78aeb6aa3eb6e11ddc", "expires_in": 3600, "scope": "entities streams", "token_type": "Bearer"} | This remains the canonical setup for real routed auth. |
| `rest.oauth.issued_token` | ✓ |  |  |  | {"_compat": {"eventType": "CREATE", "sequence": 1}, "entityId": "oauth-auth-entity", "entity_id": "oauth-auth-entity", "isLive": true, "is_live": true} | Validates the token issued by Zorn's OAuth dev route. |
| `grpc.static.x_api_key` |  |  |  | ✓ | grpc-api-key-auth-entity | Keep for probe setup parity; the live lane should prefer official bearer flows. |
| `grpc.sandbox.authorization` |  |  |  | ✓ | grpc-sandbox-auth-entity | Zorn accepts sandbox auth metadata as bearer transport; live routes may not expose this shape. |
| `grpc.auth_mode.none` |  |  |  | ✓ | grpc-none-auth-entity | Useful for local setup and fault injection only. |
| `grpc.oauth.issued_token` | ✓ |  |  |  | grpc-oauth-auth-entity | Keeps the official OAuth-backed gRPC route visible. |
| `auth_lifecycle.1` |  | ✓ |  |  | OAuth refresh semantics are not exposed on either REST or gRPC. | Backend shortfall that still needs narrowing under the existing boundary. |
| `backend_cheat_surface.2` |  | ✓ |  |  | Task and object verification is bounded to local Zorn endpoint behavior and does not prove real vendor-side auth, storage, or task execution behavior. | Backend shortfall that still needs narrowing under the existing boundary. |
| `real_lattice_unknown.1` |  |  | ✓ |  | Real Lattice auth expiry, refresh, and scope semantics remain unknown until a live credential-gated route is exercised. | Unknown until exercised against live vendor evidence. |
| `real_lattice_unknown.2` |  |  | ✓ |  | Vendor-only stream timing, routing, and backend side effects remain unknown where Zorn does not expose them. | Unknown until exercised against live vendor evidence. |
| `real_lattice_unknown.3` |  |  | ✓ |  | Objects and tasks are proven only against Zorn's local state machines, not a live vendor backend. | Unknown until exercised against live vendor evidence. |

## Summary

- proven: `6`
- gap: `2`
- unknown: `3`
- live-Lattice-skip: `7`
- total: `18`
