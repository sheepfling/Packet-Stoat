# Adapter Authoring

Adapters are separately installable packages that consume the fastdis core and expose a product, transport, engine, or workflow surface.

Inside Packet-Stoat, that separation now also applies at the product-tree
level:

- FastDIS adapter code extends the primary product.
- GRILL DIS adapter/workflow code exists for parity and evidence generation.
- Cesium adapter/workflow code exists for vendor compatibility and
  Cesium-dependent showcase projects.

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

`extensions/cesium` is the current extension-style home for Cesium-specific
workflow and example ownership inside this monorepo.

## Dependency Rules

- Depend on `fastdis`.
- Keep adapter-only dependencies in the adapter package.
- Do not add vendor SDKs, gRPC stacks, game engine tooling, or heavy workflow dependencies to the core package.
- Do not hide GRILL DIS comparison behavior or Cesium vendor behavior behind
  generic FastDIS naming when the ownership is product-tree specific.
- Real backends must fail clearly when credentials or external tools are missing.
- Dry-run and mock backends must be usable in CI without external credentials.

## Interop

Use `fastdis.interop.CanonicalEntity` for vendor-neutral entity exchange. Put vendor-specific payload construction in the adapter package.

For compatibility, `fastdis.lattice` still re-exports canonical entity helpers, but new generic code should import from `fastdis.interop`.
