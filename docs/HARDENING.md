# Hardening

Alpha 2 adds three native fuzz harnesses:

```text
fuzz/fuzz_header.cpp
fuzz/fuzz_entity_transform.cpp
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
./build-fuzz/fastdis_fuzz_entity_transform /tmp/random.bin
./build-fuzz/fastdis_fuzz_entity_table_ingest /tmp/random.bin
```

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
