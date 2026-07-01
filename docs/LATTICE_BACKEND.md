# Lattice Backend Contract

FastDIS should not own the long-lived Lattice mock implementation.

The preferred model is:

```text
FastDIS
  -> canonical entity / DIS bridge logic
  -> Lattice-shaped payload mapping
  -> workflow wrappers and reports
  -> pinned external mock backend
       = zorn
```

## Default backend

The backend contract is stored in:

- `configs/lattice_backend.json`

Current defaults:

- backend: `external-zorn`
- transport: `mock`
- repo: `https://github.com/sheepfling/zorn.git`
- tag: `Alpha1.4`
- checkout dir: `build/external/zorn`

Inspect it with:

```bash
python tools/lattice_backend.py doctor
```

Swap to the credential-gated live Lattice backend by pointing
`FASTDIS_LATTICE_BACKEND_CONFIG` at an alternate contract file. A starter
example is checked in at:

- `configs/lattice_backend.real.example.json`

That file targets the checked-in live route surface in
`tools/lattice_live_bridge.py`. It exists to keep the route shape stable:

- `doctor`
- `dis_to_shim`
- `shim_to_dis`
- `lab_state`

FastDIS should remain able to switch those lanes from a mock backend to a live
backend without changing the operator-facing workflow commands.

## Why this split exists

FastDIS should keep ownership of:

- DIS ingress/egress
- canonical entity mapping
- Lattice-shaped payload conversion
- loop suppression
- replay/UDP/operator workflows

`zorn` should own:

- mock REST behavior
- mock gRPC behavior
- auth/session emulation
- object/task mock state machines
- backend-specific sandbox simulation

## Contract surfaces

The backend contract is intentionally route-shaped rather than implementation-
shaped. The checked-in config declares the surfaces FastDIS expects a backend
to satisfy:

- auth client-credentials shape
- environment-token shape
- REST SDK import or explicit missing-SDK gap
- REST SDK-compatible auth/connect/publish/subscribe route
- entity publish/events/stream
- entity gRPC publish/get
- official Buf proto contract loading
- task gRPC create/update/cancel/stream/listen
- task create/status/cancel
- object put/delete
- DIS to entity bridge seam
- entity to DIS bridge seam

The entity event/stream paths are configurable in the backend contract so the
FastDIS bridge can pin one route for proof without inventing a new surface:

- `entity_events_route` defaults to `POST /api/v1/entities/events`
- `entity_stream_route` defaults to `POST /api/v1/entities/stream`

That list is exposed by `python tools/lattice_backend.py doctor` and should stay
stable as the backend swaps from `zorn` to a real Lattice route.

## Current cheats

The checked-in `zorn` backend also declares its current cheat surfaces in
`configs/lattice_backend.json`. These are deliberate shortcuts that should be
removed or reduced if real Lattice access becomes available.

Today those cheats include:

- bounded local task/object verification instead of real backend behavior

FastDIS no longer uses `zorn replay` report files as its primary proof path.
The default mock route starts a local Zorn server and drives the declared
entity, task, and object surfaces through explicit REST endpoints. The entity
event route is configurable in the backend manifest so one route can be chosen
as the canonical bounce-off point when the standard does not distinguish
between equivalent public shapes.

The gRPC route is probed separately so REST and gRPC failures stay distinct:

```bash
python tools/lattice_zorn_grpc_probe.py --out-dir artifacts/verification_reports/alpha5/lattice_zorn_grpc
```

That probe starts Zorn's gRPC server, loads the pinned official Buf-generated
Python modules from Zorn's environment, audits the proto contract, and
exercises EntityManager publish/get plus TaskManager create, update-status,
cancel, StreamTasks, and ListenAsAgent.

The REST SDK-compatible route is also probed separately:

```bash
python -m pip install -e '.[lattice]'
python tools/lattice_zorn_rest_sdk_probe.py --out-dir artifacts/verification_reports/alpha5/lattice_zorn_rest_sdk
```

That probe starts Zorn's REST server, performs OAuth client-credentials auth,
publishes an entity, gets it back, polls entity events, and opens the
preexisting entity stream. Transport readiness is treated separately from the
Lattice-shaped proof surface, so this probe does not rely on backend-only
`/healthz` helpers. If `anduril-lattice-sdk-python` is not installed, the
report is `ready-with-gaps` and records the missing `anduril` import explicitly.
Use `--require-official-sdk` when the official SDK must be present for a
release gate.

The Zorn auth lifecycle probe intentionally exercises setup-heavy edges:

- `x-api-key` acceptance
- sandbox-header-only rejection
- `auth_mode=none`
- OAuth dev token issuance and reuse
- gRPC bearer metadata variants

Those permutations are part of the Zorn scaffolding and should stay
explicitly out of the simpler live-Lattice route unless the vendor surface
demands them.

Generate the current auth edge matrix with:

```bash
python tools/generate_zorn_auth_edge_matrix.py
```

That matrix is the lightweight report surface for tracking the setup-heavy
auth edges separately from the core parity and lifecycle probes.

## Workflow behavior

`tools/lattice_workflow.py` resolves lattice lane commands only through the
backend contract. FastDIS no longer falls back to the embedded shim when a
backend command template is missing.

That keeps backend ownership explicit:

- `zorn` owns the mock route today
- `lattice_live_bridge.py` owns the credential-gated path when real endpoint
  environment variables are present

## Proof layers

Keep the proof surfaces separate:

- local shim proof:
  - [`LATTICE_LOCAL_SHIM_PROOF.md`](LATTICE_LOCAL_SHIM_PROOF.md)
- Zorn-backed proof:
  - [`LATTICE_ZORN_PROOF.md`](LATTICE_ZORN_PROOF.md)
- real credential-gated route proof:
  - [`LATTICE_REAL_LATTICE_PROOF.md`](LATTICE_REAL_LATTICE_PROOF.md)

The current Zorn gap summary is generated at:

- [`ZORN_GAP_MANIFEST.md`](ZORN_GAP_MANIFEST.md)
- `generated/zorn_gap_manifest.json`

For a single operator-facing report that combines DIS row classification with
the current ingress/egress lanes, run the showcase command:

- [`LATTICE_DIS_SHOWCASE.md`](LATTICE_DIS_SHOWCASE.md)
- `python tools/lattice_workflow.py showcase`

Additional Zorn-backed probes:

```bash
python tools/lattice_zorn_entity_parity_probe.py --out-dir artifacts/verification_reports/alpha5/lattice_zorn_entity_parity
python tools/lattice_zorn_auth_lifecycle_probe.py --out-dir artifacts/verification_reports/alpha5/lattice_zorn_auth_lifecycle
python tools/generate_zorn_gap_manifest.py
```
