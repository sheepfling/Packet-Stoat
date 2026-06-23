# Zorn Backlog

This backlog tracks the improvements that would make `zorn` a better
non-cheating backend for FastDIS DIS ingress/egress verification.

The point is not to make `zorn` identical to a real Lattice deployment. The
point is to reduce backend-specific shortcuts so FastDIS can trust the same
workflow shape when switching from a mock route to a real route.

## Current FastDIS Cheats

These are the currently declared Zorn-specific cheat surfaces on the FastDIS
side:

- bounded local task/object verification instead of real backend behavior

The items below are written so each one can remove or shrink one of those
cheats.

## Resolved FastDIS-Side Cheats

These are no longer part of the default FastDIS Zorn route:

- invoking `zorn replay` as the primary bridge proof path
- accepting Zorn replay/report JSON as the primary proof surface

The default route now starts a local Zorn server and drives entity, task, and
object behavior through explicit REST endpoints.

## Zorn-01 Stream Lifecycle Semantics

Issue:
- FastDIS needs a stable, documented stream lifecycle contract that matches
  the backend proof path.

Improve Zorn by:
- emitting deterministic `CREATE`, `UPDATE`, and `DELETED` or non-live events
- documenting what counts as a create versus update versus no-op publish
- supporting explicit expiry or delete semantics over the public route
- supporting stable heartbeat behavior and preexisting/new stream controls

Acceptance criteria:
- publishing an entity, changing it, and ending it produces a stable event
  sequence with the declared backend routes
- event ordering is deterministic and documented
- stream heartbeat behavior is deterministic and documented

FastDIS cheat removed when:
- the stream lifecycle proof path is entirely backend-driven and documented

## Resolved FastDIS-Side Cheats

These are no longer part of the default FastDIS Zorn route:

- invoking `zorn replay` as the primary bridge proof path
- accepting Zorn replay/report JSON as the primary proof surface
- synthesizing extra create/update/non-live stream rows in the Zorn proof path
## Zorn-02 Verification Endpoints

Issue:
- FastDIS currently verifies Zorn state by observing endpoint responses and
  entity event polling. Richer backend verification state would reduce
  endpoint-specific assumptions further.

Improve Zorn by adding:
- `GET /healthz/details` as an explicit diagnostics surface, not part of the
  Lattice-compatibility contract
- `GET /api/v1/verification/state`
- stable event snapshot endpoints for entities and tasks
- versioned response schemas for verification payloads

Acceptance criteria:
- backend state and event verification can be performed through public API
  endpoints instead of CLI-only report files
- verification payloads are deterministic and documented

FastDIS cheat reduced when:
- FastDIS can validate lane results through backend state/event APIs with
  documented versioned response schemas, not only operation responses and
  entity event polling

## Zorn-03 Official REST SDK Conformance

Issue:
- FastDIS still needs to keep the official SDK route documented and probeable.

Improve Zorn by:
- adding conformance tests driven by `anduril-lattice-sdk-python`
- documenting which REST surfaces are supported, partial, or unsupported
- making the conformance suite runnable in one command

Acceptance criteria:
- official REST SDK calls can authenticate and perform supported entity, task,
  and object operations against Zorn
- conformance results are exported in machine-readable form

FastDIS cheat removed when:
- the official SDK route is the documented default proof path for REST
  interactions

## Zorn-04 gRPC Parity

Issue:
- Zorn is still strongest as a REST-side harness. That leaves transport parity
  underproven.

Improve Zorn by:
- implementing Buf-generated gRPC surfaces for Entities and Tasks
- aligning stream semantics between REST and gRPC
- adding parity tests across REST and gRPC publish/observe flows

Acceptance criteria:
- entity publish and observe flows work across both transports
- task stream flows work across both transports
- auth expectations are documented for both transports

FastDIS cheat removed when:
- FastDIS no longer has to treat Zorn as “mostly REST proof” and can use it as
  a real transport-parity harness

## Zorn-05 Auth And Session Realism

Issue:
- mock auth is still closer to public-docs shape than true session behavior.

Improve Zorn by:
- supporting short-lived OAuth token issuance with realistic expiry
- supporting environment-token mode
- enforcing sandbox headers consistently
- returning documented 401 versus 403 failures
- supporting configurable offline or self-signed mode behavior
- adding auth failure injection

Acceptance criteria:
- auth flows are deterministic and closer to the public Lattice behavior model
- token-expiry and auth-failure cases can be tested deliberately

FastDIS cheat removed when:
- FastDIS no longer needs to treat auth as largely shape-only compatibility on
  the Zorn route

## Zorn-06 Entity Payload Normalization

Issue:
- FastDIS still relies on some Zorn-specific JSON conventions rather than the
  leanest public-docs-aligned payload contract.

Improve Zorn by:
- documenting which payload fields are public-docs-aligned and which are
  Zorn-native
- accepting minimal public-docs-shaped entity payloads
- returning normalized payloads after publish
- versioning normalized payload schemas

Acceptance criteria:
- minimal entity publish payloads are accepted and normalized consistently
- normalized backend responses are documented and stable

FastDIS cheat removed when:
- FastDIS can publish a lean route-shaped payload and rely on Zorn to normalize
  it without backend-specific shaping assumptions

## Zorn-07 Object Lifecycle Realism

Issue:
- object verification is still bounded and mostly happy-path.

Improve Zorn by:
- supporting object `PUT`, `GET`, `HEAD`, and `DELETE` with stable metadata
- documenting path validation and duplicate behavior
- modeling media-linking behavior more explicitly
- adding failure injection for missing paths, duplicates, and auth failures

Acceptance criteria:
- object lifecycle behavior is deterministic and queryable
- object failure cases can be exercised deliberately

FastDIS cheat removed when:
- FastDIS object verification stops being merely bounded local seam checking and
  becomes lifecycle verification

## Zorn-08 Task Lifecycle Realism

Issue:
- task verification is still bounded and does not yet prove a realistic task
  state machine.

Improve Zorn by:
- supporting create, update, cancel, query, listen, and stream as a documented
  task lifecycle
- documenting duplicate ID behavior and invalid transitions
- exposing task mailbox state for verification
- adding failure injection for invalid transitions and auth failures

Acceptance criteria:
- task lifecycle behavior is deterministic and queryable
- duplicate, cancel, and invalid-transition cases are testable deliberately

FastDIS cheat removed when:
- FastDIS task verification stops being bounded local replay behavior and
  becomes a real lifecycle proof

## Zorn-09 Backend Capability Self-Description

Issue:
- the compatibility and cheat story is still declared on the FastDIS side.

Improve Zorn by adding:
- `GET /api/v1/backend/capabilities`
- `GET /api/v1/backend/compatibility`

Those endpoints should declare:
- supported surfaces
- unsupported surfaces
- mock shortcuts
- auth modes
- transport support
- stream guarantees

Acceptance criteria:
- backend compatibility and shortcuts are queryable from Zorn itself
- FastDIS can record backend capability data without hardcoding it in docs

FastDIS cheat removed when:
- the cheat list becomes backend-provided metadata rather than repo prose

## Recommended Order

1. Zorn-01 Stream Lifecycle Semantics
2. Zorn-02 Verification Endpoints
3. Zorn-03 Official REST SDK Conformance
4. Zorn-08 Task Lifecycle Realism
5. Zorn-07 Object Lifecycle Realism
6. Zorn-05 Auth And Session Realism
7. Zorn-04 gRPC Parity
8. Zorn-09 Backend Capability Self-Description
9. Zorn-06 Entity Payload Normalization

## Done Bar

Zorn is in a much better place for non-cheating DIS integration when:

- FastDIS does not need to synthesize extra lifecycle rows just to pass stream
  checks.
- FastDIS verifies backend state via API surfaces instead of replay report
  files.
- official REST client behavior passes against Zorn for the supported route
  set.
- object and task lanes behave like state machines rather than only happy-path
  seams.
- Zorn can describe its own compatibility gaps programmatically.
