# Python Quickstart

FastDIS exposes the Python package as `fastdis`. It has no required runtime
dependencies and is optimized for scanning/filtering packets before creating
higher-level objects.

## Install For Development

```bash
python -m pip install -e '.[dev]'
fastdis doctor
```

## Scan Packets In Memory

```python
import fastdis

seen, accepted, emitted = fastdis.scan_many(
    packets,
    callback=None,
    versions={6, 7},
    pdu_types={1},
    strict=False,
)
print(seen, accepted, emitted)
```

## Send And Receive Local Entity State Traffic

Terminal 1:

```bash
fastdis recv --bind 127.0.0.1 --port 3001 --max-packets 10 --surface python
```

Terminal 2:

```bash
fastdis send-entity --dst 127.0.0.1 --port 3001 --count 10 --rate-hz 30
```

## Replay Tools

```bash
fastdis capture --bind 127.0.0.1 --port 3001 --out session.fastdispkt
fastdis replay-send session.fastdispkt --dst 127.0.0.1 --port 3001
fastdis net-smoke
```

## Native Library Path

The optional native shared library is the same C ABI surface used by engine
hosts. Load it explicitly when you need to test that path:

```python
import fastdis.native as native

lib = native.load_native()
print(lib.abi_version(), lib.version_string())
```
