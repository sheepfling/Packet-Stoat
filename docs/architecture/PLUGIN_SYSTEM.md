# Plugin System

The core package discovers optional adapters through Python entry points. This keeps `import fastdis` free of adapter imports while letting installed packages advertise packet sources, publishers, streams, consumers, workflows, and reporters.

## Entry Point Groups

- `fastdis.packet_sources`
- `fastdis.entity_publishers`
- `fastdis.entity_streams`
- `fastdis.consumers`
- `fastdis.workflows`
- `fastdis.reporters`

The registry lives in `fastdis.plugins.registry` and uses `importlib.metadata.entry_points`.

## Example

```toml
[project.entry-points."fastdis.entity_publishers"]
lattice-jsonl = "packet_stoat_lattice.plugins:jsonl_publisher"
lattice-mock = "packet_stoat_lattice.plugins:mock_publisher"
lattice-real = "packet_stoat_lattice.plugins:real_publisher"

[project.entry-points."fastdis.entity_streams"]
lattice-shim = "packet_stoat_lattice.plugins:shim_stream"

[project.entry-points."fastdis.workflows"]
lattice-full = "packet_stoat_lattice.plugins:full_workflow"
```

## Usage

```python
from fastdis.plugins import load_entry_points

publishers = load_entry_points("entity_publishers")
lattice_mock_factory = publishers["lattice-mock"]
publisher = lattice_mock_factory()
```

Entry points should return factories or small workflow modules. They should not make network calls or require credentials at import time.
