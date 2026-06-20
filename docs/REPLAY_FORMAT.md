# Replay Format

`fastdis` currently uses a simple dependency-free `.fastdispkt` replay format
for examples and benchmarks. Alpha 3 should keep that format readable while
planning a richer replay v2 for network capture, timing replay, and engine
verification.

## Current v1 Format

Current simple format:

```text
uint32_be packet_length
packet bytes
repeat...
```

Properties:

- trivial to generate
- trivial to stream
- good for benchmarks and smoke tests
- no timestamps
- no source endpoint metadata

This format should remain supported by readers.

## Planned v2 Format

Alpha 3 planning target:

```text
magic: "FDPK"
version: uint16
flags: uint16
packet_count: uint64 or unknown marker

per packet:
  timestamp_ns: uint64
  source_address_length: uint8
  source_address bytes
  source_port: uint16
  packet_length: uint32
  packet bytes
```

Expected benefits:

- preserve timing for replay
- preserve source address and source port
- support recorded cadence or rate-multiplied replay
- improve benchmark reproducibility
- improve debugging for multi-sender exercises

## Reader/Writer Compatibility Rule

Alpha 3 should preserve:

- v1 read support
- v2 planning and staged implementation

If v2 lands during Alpha 3, the reader contract should be:

- auto-detect v1 versus v2
- reject malformed headers cleanly
- keep packet bytes untouched for the parser/scanner layer

## Tooling Consumers

Replay formats are primarily for:

- `fastdis-capture`
- `fastdis-replay-send`
- `fastdis-recv --write-replay`
- benchmark/replay workflows
- Unreal/Godot demo and verification harnesses

The core parser ABI should not depend on replay policy.

## Replay Modes to Support

Planned sender modes:

- as fast as possible
- fixed packet rate
- preserve recorded timestamps
- rate multiplier
- loop

These modes belong in optional tools and helper layers, not the core ABI.

## Integrity and Truthfulness

Replay files are evidence artifacts when used for benchmark or engine proof.
That means Alpha 3 tooling should prefer:

- explicit version markers
- clear malformed-file errors
- deterministic iteration order
- stable writer behavior
- source-bundle exclusion of large generated captures unless intentionally
  curated as sample fixtures
