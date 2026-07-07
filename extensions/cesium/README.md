# Cesium Extension

This subtree owns Packet-Stoat's Cesium-specific integration work.

It exists to keep Cesium source-route prep, vendor compatibility work, and
pure-Cesium example-project planning separate from the `fastdis` core while
still reusing the shared proof architecture.

Current ownership:

- `tools/`: Cesium-specific workflow wrappers and source-route prep
- `docs/`: Cesium-specific route, parity, and example standards
- `examples/`: repo-owned pure-Cesium example-project roots and placeholders

Key entry points:

- [Cesium source-route note](./docs/CESIUM_SOURCE_ROUTE.md)
- [Cesium fork ledger](../../docs/CESIUM_FORK_LEDGER.md)
- [Cesium example standard](./docs/CESIUM_EXAMPLE_STANDARD.md)
- [Cesium Unreal example root](./examples/unreal/README.md)
- [Cesium Unity example root](./examples/unity/README.md)
- [Cesium Godot example root](./examples/godot/README.md)

Boundary:

- `fastdis` owns the generic proof architecture and engine-agnostic helpers
- `extensions/cesium` owns Cesium-specific workflow policy, docs, and example
  planning

Thin compatibility wrappers may remain under the repo-root `tools/` and `docs/`
paths when helpful, but new Cesium work should prefer this subtree directly.
