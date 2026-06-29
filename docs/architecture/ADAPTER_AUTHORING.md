# Adapter Authoring

Adapters are separately installable packages that consume the fastdis core and expose a product, transport, engine, or workflow surface.

## Package Shape

An adapter package should own its docs, tests, fixtures, configs, examples, and workflow command. During alpha these packages may live in the monorepo.

```text
packages/<adapter>/
  pyproject.toml
  README.md
  src/
    packet_stoat_<adapter>/
      plugins.py
      workflow.py
      ...
  tests/
  docs/
  examples/
  configs/
```

`packages/lattice` now follows this model and is the canonical home for the
Lattice adapter package.

## Dependency Rules

- Depend on `fastdis`.
- Keep adapter-only dependencies in the adapter package.
- Do not add vendor SDKs, gRPC stacks, game engine tooling, or heavy workflow dependencies to the core package.
- Real backends must fail clearly when credentials or external tools are missing.
- Dry-run and mock backends must be usable in CI without external credentials.

## Interop

Use `fastdis.interop.CanonicalEntity` for vendor-neutral entity exchange. Put vendor-specific payload construction in the adapter package.

For compatibility, `fastdis.lattice` still re-exports canonical entity helpers, but new generic code should import from `fastdis.interop`.
