# Engine integration notes

`fastdis` is meant to be consumed as a normal third-party native library. The
engine-facing layer can include either the plain C ABI header `fastdis/fastdis.h`
or the header-only C++ RAII wrapper `fastdis/fastdis.hpp`, then link/load the
platform shared library. The DLL/shared-object boundary remains the C ABI either
way.


## C++ RAII wrapper shape

For C++ engine modules, prefer `fastdis/fastdis.hpp` over hand-written destroy/release calls:

```cpp
fastdis::Scanner scanner(fastdis::ScanConfig::entity_transform());
fastdis::EntityTable table(4096);
fastdis::SnapshotBuffer snapshots(4096);

fastdis::ScopedSnapshotView view = snapshots.ingest_publish_changed_and_acquire(
    table,
    scanner,
    packet_views,
    true,
    true);

for (const fastdis::EntitySnapshot& snapshot : view) {
    // Apply actor/node transform.
}
// read slot releases automatically here.
```

Define `FASTDIS_CPP_NO_EXCEPTIONS` in Unreal/Godot builds that disable C++ exceptions and use the wrapper's `try_*` methods for explicit `fastdis_status_t` handling.

## Unreal Engine shape

Recommended layout inside a plugin:

```text
Plugins/FastDis/
  Source/FastDis/                    # Unreal-facing wrapper module
  Source/ThirdParty/FastDis/include/fastdis/fastdis.h
  Source/ThirdParty/FastDis/include/fastdis/fastdis.hpp
  Source/ThirdParty/FastDis/lib/Win64/fastdis.lib
  Binaries/ThirdParty/FastDis/Win64/fastdis.dll
```

The Unreal wrapper module should convert Unreal types (`TArray<uint8>`, `FString`,
Blueprint events) into calls to the C ABI. Do not expose `fastdis` internal types
to Blueprint directly.

Minimal Build.cs fragment:

```csharp
using System.IO;
using UnrealBuildTool;

public class FastDisThirdParty : ModuleRules
{
    public FastDisThirdParty(ReadOnlyTargetRules Target) : base(Target)
    {
        Type = ModuleType.External;
        string ThirdParty = ModuleDirectory;
        PublicIncludePaths.Add(Path.Combine(ThirdParty, "include"));

        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            string LibDir = Path.Combine(ThirdParty, "lib", "Win64");
            PublicAdditionalLibraries.Add(Path.Combine(LibDir, "fastdis.lib"));
            PublicDelayLoadDLLs.Add("fastdis.dll");
            RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/FastDis/Win64/fastdis.dll");
        }
        else if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            string LibDir = Path.Combine(ThirdParty, "lib", "Linux");
            PublicAdditionalLibraries.Add(Path.Combine(LibDir, "libfastdis.so"));
            RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/FastDis/Linux/libfastdis.so");
        }
        else if (Target.Platform == UnrealTargetPlatform.Mac)
        {
            string LibDir = Path.Combine(ThirdParty, "lib", "Mac");
            PublicAdditionalLibraries.Add(Path.Combine(LibDir, "libfastdis.dylib"));
            RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/FastDis/Mac/libfastdis.dylib");
        }
    }
}
```

## Godot shape

For Godot 4, the usual approach is a small GDExtension wrapper that depends on
`fastdis`:

```text
addons/fastdis/
  fastdis.gdextension
  bin/libfastdis_godot.linux.template_debug.x86_64.so  # Godot wrapper
  bin/libfastdis.so                                    # this library
```

The GDExtension wrapper should expose Godot-friendly methods/signals, while the
hot path stays inside the `fastdis` C ABI.

## Python shape

Python can either use the CPython extension path:

```python
import fastdis
fastdis.scan_many(packets, callback, pdu_types={1}, sample_every=100)
```

or load the engine-style shared library through `ctypes`:

```python
import fastdis.native as native
lib = native.load_native("/path/to/libfastdis.so")
print(lib.parse_header_tuple(packet))
```

The ctypes layer is for ABI validation and interoperability. For maximum Python
throughput, prefer the CPython extension scanner.

## Recommended runtime pattern

For a game engine, prefer one long-lived `fastdis_scanner_t` per network stream
or network thread:

```c
fastdis_scan_config_t cfg;
fastdis_scan_config_init(&cfg);
cfg.entity_state_fields = FASTDIS_ES_FIELD_POSE;

fastdis_scanner_t *scanner = fastdis_scanner_create(&cfg);
fastdis_scanner_set_entity_id_filter_mode(scanner, FASTDIS_ENTITY_ID_FILTER_ALLOW);
fastdis_scanner_add_entity_id(scanner, 100, 1, 42);
```

Then, on each receive burst:

```c
fastdis_scan_stats_t stats;
fastdis_scan_stats_init(&stats);
fastdis_scanner_scan_entity_state_packets(
    scanner,
    packet_views,
    packet_count,
    on_entity_state,
    engine_queue,
    &stats);
```

The callback should enqueue a compact engine event or update a lock-free/ring
buffer; it should not perform expensive game-thread work directly. Packet memory
is borrowed only for the duration of the callback.

Use field masks to avoid decoding data that the engine will throw away. For
example, an entity pose replication layer usually wants:

```c
cfg.entity_state_fields = FASTDIS_ES_FIELD_POSE;
```

A diagnostics overlay might use:

```c
cfg.entity_state_fields = FASTDIS_ES_FIELD_POSE | FASTDIS_ES_FIELD_MARKING;
```

## C++ RAII wrapper

C++ engine modules can include `fastdis/fastdis.hpp` for move-only ownership of
native handles while still linking to the same C ABI shared library. The wrapper
adds:

- `fastdis::Scanner` for fluent filters and entity-ID allow/block lists.
- `fastdis::EntityTable` for latest-state storage.
- `fastdis::SnapshotBuffer` for double-buffer publication.
- `fastdis::ScopedSnapshotView` for acquire/release safety.
- `FASTDIS_CPP_NO_EXCEPTIONS` support for exception-free engine builds.

See `docs/CPP_RAII.md` and `examples/cpp/raii_snapshot_buffer.cpp`.
