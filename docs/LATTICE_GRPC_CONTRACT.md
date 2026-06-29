# Lattice gRPC Contract

Alpha 4.1 should check gRPC next, but it should check the right thing.

The goal is not:

- implement the full vendor gRPC surface
- clone every official protobuf service
- build a fake vendor auth/session stack

The goal is:

```text
Prove Packet-Stoat's mock/shim can exercise the same high-rate publish and
stream behaviors that a real Lattice integration would rely on.
```

## Scope

Three levels are useful:

1. Packet-Stoat shim gRPC
   - Packet-Stoat-owned proto
   - local gRPC server/client
   - high-rate publish/stream tests
2. Official shape audit
   - compare the local seam against public publish/stream concepts
   - validate field/method naming and behavior boundaries
3. Optional official-stub check
   - import public/generated stubs if available
   - construct request objects
   - serialize/deserialize locally

Alpha 4.1 requires level 1, records level 2 in the generated report, and probes
level 3 when Buf-generated Python modules are installed.

Public setup reference:

- [Anduril Lattice SDK setup](https://developer.anduril.com/guides/getting-started/set-up)
- [Buf Python gRPC artifacts](https://buf.build/anduril/lattice-sdk/sdks/main:grpc/python)

## First useful proto

Start with a Packet-Stoat-owned proto:

- `PublishEntities`
  - client-streaming
  - summary response
- `StreamEntityComponents`
  - server-streaming
  - event types:
    - `PREEXISTING`
    - `UPDATE`
    - `DELETED`
    - `HEARTBEAT`

The first proto does not need to model every vendor entity component directly.
JSON payload carriage is acceptable for the first useful pass if it keeps the
contract easy to evolve and inspect.

## Publish semantics

The local gRPC publish lane should prove:

- snapshot batches can stream into the shim
- the shim can coalesce latest state by entity
- overload does not break per-entity ordering
- summary counts are explicit:
  - received
  - accepted
  - rejected
  - coalesced
  - dropped

The mock server can also run in `require_auth=True` mode. In that mode the
client must send:

- `authorization: Bearer <access-token-or-environment-token>`
- `anduril-sandbox-authorization: Bearer <sandbox-token>`

This mirrors the documented Lattice gRPC client-credential/sandbox metadata
shape without claiming a real OAuth/session implementation.

Suggested acceptance:

- `50 entities x 10 Hz x 60 seconds`
- `500 entities x 20 Hz` short soak

## Stream semantics

The local gRPC stream lane should prove:

- preexisting entities arrive first
- updates arrive after publish
- delete/stale events are explicit
- heartbeats continue while idle
- component filtering strips unrequested parts
- per-entity rate limiting prevents flooding

Minimum request surface:

- `components_to_include`
- `include_all_components`
- `heartbeat_period_millis`
- `preexisting_only`
- `update_per_entity_limit_ms`

## Retry and reconnect policy

Retry/backoff is an integration concern in this lane, not a magical SDK
guarantee.

Plan explicit chaos cases:

- `UNAVAILABLE`
- `DEADLINE_EXCEEDED`
- `RESOURCE_EXHAUSTED`
- `INVALID_ARGUMENT`
- `CANCELLED`
- `UNAUTHENTICATED`

Expected behaviors:

- retry/backoff for transient availability failures
- stronger coalescing or rate reduction for resource exhaustion
- terminal logging for invalid payloads
- explicit credential-gated terminal behavior for unauthenticated calls

## What is out of scope

- full official vendor API emulation
- full taskmanager emulation
- objects over gRPC
- auth/token lifecycle cloning
- all entity components

Objects stay REST-oriented in this plan.

## Planned work packet

Suggested artifact group:

```text
alpha4_1_grpc_contract/
  proto
  local server/client
  publish soak tests
  stream/heartbeat tests
  retry/reconnect chaos tests
  grpc_contract_report.json
  optional official stub import/serialization test
```

Suggested files:

- `packages/lattice/proto/packetstoat/lattice_shim/v1/lattice_shim.proto`
- `packages/lattice/src/packet_stoat_lattice/grpc_shim_server.py`
- `packages/lattice/src/packet_stoat_lattice/grpc_publish_client.py`
- `packages/lattice/src/packet_stoat_lattice/grpc_stream_client.py`
- `packages/lattice/src/packet_stoat_lattice/grpc_backends.py`
- `packages/lattice/src/packet_stoat_lattice/grpc_chaos.py`
- `tests/test_lattice_grpc_publish_stream.py`
- `tests/test_lattice_grpc_stream_entities.py`
- `tests/test_lattice_grpc_backpressure.py`
- `tests/test_lattice_grpc_retry_policy.py`
- `tests/test_lattice_grpc_auth_and_official_surface.py`
- `verification_reports/alpha4_1/lattice/grpc_contract_report.json`

## Definition of useful

This lane is useful when Packet-Stoat can honestly say:

- the local bridge is proven over a gRPC-shaped high-rate publish seam
- the local bridge is proven over a gRPC-shaped entity stream seam
- bearer/sandbox metadata checks are proven against the mock harness
- retry/reconnect semantics are explicit and tested
- official Buf Python stub availability is probed and reported
- the remaining unknowns are real vendor auth/transport and vendor-side
  validation details

If official Buf Python modules are not installed, the report records
`official_buf_stub_import: skipped`. That is not a failure of the mock harness;
it means the next compatibility step is installing the generated Buf artifacts
and validating exact module names plus request serialization.
