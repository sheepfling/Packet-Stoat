# Lattice Lab Quickstart

The FastDIS Lattice Lab maps DIS/native simulation state into
public-docs-aligned, Lattice-shaped Entities, Objects, and Tasks workflows. It
is not an official Anduril integration and does not claim live sandbox behavior
without credentials.

FastDIS now treats the mock backend as an external dependency. The preferred
backend is a pinned checkout of `zorn`, described in
[`LATTICE_BACKEND.md`](LATTICE_BACKEND.md).

## Modes

external mock:

No Anduril SDK or credentials required. Uses local JSON fixtures, JSONL reports,
and the configured external backend checkout.

sdk-dryrun:

Imports the official REST SDK if installed and checks that Packet Stoat's
configuration and mock transport seams are compatible. No real endpoint is
called.

live:

Skipped unless explicit environment variables and opt-in flags are present.
This is reserved for future sandbox credentials.

To swap the workflow from `zorn` to a future live backend contract, point:

```bash
export FASTDIS_LATTICE_BACKEND_CONFIG=configs/lattice_backend.real.example.json
```

The example file is only a contract template today, but it shows the route
shape FastDIS expects to keep stable when credentials eventually exist. The
credential-gated command surface behind that example is:

```bash
python tools/lattice_live_bridge.py doctor
```

## Commands

```bash
python tools/lattice_backend.py doctor
fastdis lattice doctor
fastdis lattice dis-to-shim
fastdis lattice shim-to-dis
fastdis lattice lab-state
fastdis lattice report
fastdis lattice sdk-check
fastdis lattice full
```

The `sdk-check` command writes the Alpha 4.1 SDK gap report and records what is
mock-compatible, shape-compatible, and still credential-gated.

To see the current Zorn-only shortcut surfaces, run:

```bash
python tools/lattice_backend.py doctor
```

That output includes the declared cheat surfaces so the migration edges stay
visible.

## Demo Flow

```text
DIS replay / UDP
  -> fastdis Entity State decode
  -> canonical entity bridge
  -> Lattice-shaped Entity payload
  -> mock stream / JSONL / optional SDK seam
```

Reverse flow:

```text
Lattice-shaped fixture
  -> canonical entity
  -> DIS Entity State egress
  -> fastdis recv / engine demo
```
