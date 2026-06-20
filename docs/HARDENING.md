# Hardening

Alpha 3 expands the native fuzz harness set to cover both breadth and depth:

```text
fuzz/fuzz_header.cpp
fuzz/fuzz_scan_many.cpp
fuzz/fuzz_catalog_dispatch.cpp
fuzz/fuzz_min_lengths.cpp
fuzz/fuzz_unknown_pdu.cpp
fuzz/fuzz_entity_transform.cpp
fuzz/fuzz_snapshot_buffer.cpp
fuzz/fuzz_frame_orientation.cpp
fuzz/fuzz_entity_table_ingest.cpp
```

Enable them with:

```bash
cmake -S . -B build-fuzz \
  -DFASTDIS_BUILD_SHARED=ON \
  -DFASTDIS_BUILD_FUZZERS=ON
cmake --build build-fuzz --config Debug
```

These harnesses compile as normal executables by default so they can be smoke-run
without a dedicated libFuzzer toolchain:

```bash
./build-fuzz/fastdis_fuzz_header /tmp/random.bin
./build-fuzz/fastdis_fuzz_scan_many /tmp/random.bin
./build-fuzz/fastdis_fuzz_catalog_dispatch /tmp/random.bin
./build-fuzz/fastdis_fuzz_min_lengths /tmp/random.bin
./build-fuzz/fastdis_fuzz_unknown_pdu /tmp/random.bin
./build-fuzz/fastdis_fuzz_entity_transform /tmp/random.bin
./build-fuzz/fastdis_fuzz_snapshot_buffer /tmp/random.bin
./build-fuzz/fastdis_fuzz_frame_orientation /tmp/random.bin
./build-fuzz/fastdis_fuzz_entity_table_ingest /tmp/random.bin
```

Deep-path intent:

- `fuzz_entity_transform`: typed Entity State parse/transform path
- `fuzz_entity_table_ingest`: latest-state ingest path
- `fuzz_snapshot_buffer`: publish/acquire/release/copy/resize snapshot handoff path
- `fuzz_frame_orientation`: ENU/Unreal/Godot pose conversion and orientation basis/quaternion path

## Shallow all-PDU corpus

Alpha 3 now includes a generated shallow fuzz corpus that covers every
cataloged DIS 6/7 PDU with a valid header seed, plus malformed seeds for short
packets, undersized declared lengths, oversized declared lengths, and unknown
PDU values.

Generate or verify it with:

```bash
python tools/generate_shallow_fuzz_corpus.py
python tools/generate_shallow_fuzz_corpus.py --check
```

Outputs:

- `generated/fuzz_shallow_corpus/`
- `generated/fuzz_shallow_corpus/manifest.json`

## Sanitizers

Sanitizer toggles are exposed through CMake:

```text
FASTDIS_ENABLE_ASAN
FASTDIS_ENABLE_UBSAN
FASTDIS_ENABLE_TSAN
```

`TSAN` must not be combined with `ASAN` or `UBSAN`.

Use the helper script for a repeatable native test run:

```bash
python tools/run_sanitizers.py --sanitizers asan,ubsan
python tools/run_sanitizers.py --build-dir build-tsan --sanitizers tsan
```

The sanitizer runner enables native tests and fuzz harnesses while disabling the
examples and benchmark targets so the build stays focused on parser hardening.

## Malformed packet coverage

The native API tests now exercise:

- null pointer inputs
- zero-length and short packets
- declared header length below 12 bytes
- declared PDU length beyond the datagram size
- truncated Entity State fixed prefix
- non-Entity-State PDUs passed to Entity-State decoders
- oversized `variable_parameter_count` values
- invalid/high protocol version values
- null/empty table/scanner/snapshot-buffer ingestion paths

The parser contract remains strict:

- malformed bytes return a `FASTDIS_ERR_*` status
- scan loops count malformed packets without crashing
- snapshot/table helpers reject null handles cleanly
