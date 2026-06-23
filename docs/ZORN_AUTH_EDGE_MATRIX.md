# Zorn Auth Edge Matrix

- backend: `external-zorn`
- transport: `mock`
- zorn_tag: `Alpha1.4`

## Policy

skip setup-heavy auth permutations; prefer environment-token and the minimal credential-gated route shape.

## Rows

| Surface | Lane | Expected | Status | Evidence | Note |
| --- | --- | --- | --- | --- | --- |
| `rest.static.x_api_key` | `zorn-only-auth-setup` | `accepted` | `passed` | {"_compat": {"eventType": "CREATE", "sequence": 2}, "entityId": "static-api-key-entity", "entity_id": "static-api-key-entity", "isLive": true, "is_live": true} | Keep this edge on Zorn; the live lane can stay bearer-only or environment-token only. |
| `rest.sandbox.required` | `zorn-only-auth-setup` | `accepted with sandbox header, rejected without it` | `passed` | {"detail": "Missing sandbox header"} | This is the setup-heavy path that should stay explicit in Zorn probes. |
| `rest.sandbox.bearer_only` | `zorn-only-auth-setup` | `rejected` | `passed` | {"detail": "Missing bearer token"} | Documents that sandbox headers do not replace bearer auth. |
| `rest.auth_mode.none` | `zorn-only-auth-setup` | `accepted without headers` | `passed` | {"_compat": {"eventType": "CREATE", "sequence": 1}, "entityId": "none-auth-entity", "entity_id": "none-auth-entity", "isLive": true, "is_live": true} | Useful for local probe scaffolding, not for live Lattice parity. |
| `rest.oauth.client_credentials` | `zorn-and-live` | `accepted` | `passed` | {"access_token": "zorn-oauth-dev.eyJleHAiOjE3ODIxODQ4NTQsImlhdCI6MTc4MjE4MTI1NCwianRpIjoiOTA2NGE2Y2YyNzhjMmUzZmJlNDY5MGJhIiwic2NvcGUiOiJlbnRpdGllcyBzdHJlYW1zIn0.1a2effd37548c297d6aa17edd84f48e0b3e0e12e14009d78aeb6aa3eb6e11ddc", "expires_in": 3600, "scope": "entities streams", "token_type": "Bearer"} | This remains the canonical setup for real routed auth. |
| `rest.oauth.issued_token` | `zorn-and-live` | `accepted` | `passed` | {"_compat": {"eventType": "CREATE", "sequence": 1}, "entityId": "oauth-auth-entity", "entity_id": "oauth-auth-entity", "isLive": true, "is_live": true} | Validates the token issued by Zorn's OAuth dev route. |
| `grpc.static.x_api_key` | `zorn-only-auth-setup` | `accepted` | `passed` | grpc-api-key-auth-entity | Keep for probe setup parity; the live lane should prefer official bearer flows. |
| `grpc.sandbox.authorization` | `zorn-only-auth-setup` | `accepted` | `passed` | grpc-sandbox-auth-entity | Zorn accepts sandbox auth metadata as bearer transport; live routes may not expose this shape. |
| `grpc.auth_mode.none` | `zorn-only-auth-setup` | `accepted without headers` | `passed` | grpc-none-auth-entity | Useful for local setup and fault injection only. |
| `grpc.oauth.issued_token` | `zorn-and-live` | `accepted` | `passed` | grpc-oauth-auth-entity | Keeps the official OAuth-backed gRPC route visible. |

## Gaps

- `auth_lifecycle`: OAuth refresh semantics are not exposed on either REST or gRPC.

## Summary

- passed: `10`
- gap: `0`
- total: `10`
