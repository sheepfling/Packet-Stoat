# Networking and Optional I/O

Alpha 3 can include sender/receiver/capture/replay utilities, but they should
remain outside the core parser ABI.

The layering rule is:

```text
libfastdis
  parser/scanner/table/snapshot/orientation
  deterministic packet processing
  no sockets required

optional fastdis_io / helper layer
  UDP receive/send
  multicast/broadcast helpers
  replay capture/send
  CLI tools
  optional build
```

This keeps the release claim honest:

- `libfastdis` is the packet-processing SDK.
- optional I/O tooling exists for operator workflows, testing, replay, and
  engine/demo integration.
- networking policy is not part of the core C ABI contract in Alpha 3.

## Scope

Useful Alpha 3 utilities:

- `fastdis-recv`
- `fastdis-send-entity`
- `fastdis-capture`
- `fastdis-replay-send`
- `fastdis-net-smoke`

Useful Alpha 3 library surfaces:

- `include/fastdis/fastdis_io.hpp`
- `src/io/fastdis_udp.cpp`
- `src/io/fastdis_replay.cpp`

Suggested C++ types:

```cpp
namespace fastdis::io {
struct UdpEndpoint {
    std::string address;
    uint16_t port;
};

struct UdpReceiverConfig {
    std::string bind_address = "0.0.0.0";
    uint16_t port = 3001;
    std::string multicast_group;
    std::string interface_address;
    int receive_buffer_bytes = 4 * 1024 * 1024;
    bool nonblocking = true;
    bool reuse_address = true;
};

class UdpReceiver;
class UdpSender;
class ReplayReader;
class ReplayWriter;
class ReplaySender;
}
```

## Non-Goals

Alpha 3 should not:

- add sockets to `include/fastdis/fastdis.h`
- require networking support to build the core library
- make Python networking the engine-performance path
- expose a premature cross-platform C socket ABI before the C++ I/O layer has
  stabilized
- encourage a full-PDU-object-per-packet workflow in the hot path

## Preferred Data Flow

Do not optimize around a "deserialize a full object and print it" model.

Preferred fastdis flow:

```text
UDP packet burst
  -> packet views
  -> native scanner filters
  -> entity table
  -> snapshot buffer
  -> print / JSON / engine/runtime consumer
```

The convenience tools should exercise the same validated packet-processing path
that the engine adapters and benchmarks use.

## CLI Planning

### `fastdis-recv`

Example:

```bash
fastdis-recv --bind 0.0.0.0 --port 3001 --stats
fastdis-recv --bind 0.0.0.0 --port 3001 --entity-state --jsonl
fastdis-recv --bind 239.1.2.3 --port 3001 --multicast --iface en0
```

Useful modes:

- header counts
- Entity State transform print
- latest-state entity table
- changed snapshot summary
- replay file writing
- orientation debug output
- JSON Lines output for tooling

### `fastdis-send-entity`

Example:

```bash
fastdis-send-entity \
  --dst 127.0.0.1 \
  --port 3001 \
  --site 100 \
  --application 1 \
  --entity 42 \
  --lat 29.5597 \
  --lon -95.0831 \
  --alt 100 \
  --heading 90 \
  --pitch 0 \
  --roll 0 \
  --rate-hz 30
```

This sender should be orientation-paranoid:

- accept local geodetic position plus heading/pitch/roll
- derive ECEF XYZ and DIS `psi/theta/phi`
- optionally print basis/debug output for orientation verification

### `fastdis-capture`

Example:

```bash
fastdis-capture --bind 0.0.0.0 --port 3001 --out session.fastdispkt
fastdis-capture --port 3001 --max-packets 100000 --out smoke.fastdispkt
```

### `fastdis-replay-send`

Example:

```bash
fastdis-replay-send capture.fastdispkt --dst 127.0.0.1 --port 3001
fastdis-replay-send capture.fastdispkt --multicast 239.1.2.3 --port 3001 --rate 2.0
fastdis-replay-send capture.fastdispkt --loop
```

### `fastdis-net-smoke`

Intent:

- start a localhost receiver
- send a known Entity State PDU
- verify header decode, entity ID, position/orientation conversion, and
  snapshot-table update
- exit `0` / nonzero

## Python Convenience Wrappers

Python should get simple wrappers for debugging and operator workflow:

```bash
python -m fastdis.tools.recv --port 3001 --stats
python -m fastdis.tools.send_entity --dst 127.0.0.1 --port 3001
python -m fastdis.tools.capture --port 3001 --out test.fastdispkt
python -m fastdis.tools.replay_send test.fastdispkt --dst 127.0.0.1 --port 3001
```

These are convenience paths, not the engine fast path.

## Build and Packaging Policy

Suggested CMake flags:

```text
FASTDIS_BUILD_IO=ON/OFF
FASTDIS_BUILD_TOOLS=ON/OFF
FASTDIS_BUILD_EXAMPLES=ON/OFF
FASTDIS_BUILD_ENGINE_EXAMPLES=ON/OFF
```

Suggested defaults:

```text
FASTDIS_BUILD_IO=ON
FASTDIS_BUILD_TOOLS=ON
FASTDIS_BUILD_EXAMPLES=ON
FASTDIS_BUILD_ENGINE_EXAMPLES=OFF
```

The core library must still build cleanly with:

```text
FASTDIS_BUILD_IO=OFF
```

## Portability Topics

Alpha 3 should explicitly track:

- macOS/Linux/Windows socket setup differences
- multicast join/leave quirks
- reuse-address semantics
- large receive-buffer behavior
- no-space scratch/output directory policy where toolchains are sensitive
- replay/capture artifact staging without polluting the source bundle

That portability matrix belongs to `A3-040`.
