# Engine Logging

FastDIS engine plugins should consume one generated logging contract instead
of hand-writing per-PDU log cases.

## Generated Descriptor Tables

- Unreal: `packages/unreal/FastDis/Source/FastDisUnreal/Public/FastDisPduLogCatalog.h`
- Unity: `packages/unity/com.sheepfling.fastdis/Runtime/Logging/FastDisPduLogCatalog.cs`
- Godot: `packages/godot/fastdis_demo/addons/fastdis/fastdis_pdu_log_catalog.gd`

Each table contains all 141 DIS 6/7 versioned PDU rows.

## Engine Sinks

Unreal should map `FastDisLogEvent` into `UE_LOG(LogFastDIS, ...)`, a monitor
ring buffer, and optional JSONL export. Spatial Visual Logger output should be
reserved for entity lifecycle, orientation, and mapping diagnostics.

Unity should route through one `FastDisUnityLogger` wrapper over
`Debug.unityLogger`, an editor monitor window, and optional JSONL export.

Godot should use `GD.Print`, `GD.PushWarning`, and `GD.PushError` first, with a
dock/monitor panel and optional JSONL export. Avoid recursive custom logger
paths until the basic addon behavior is stable.

## Product Rule

Engine adapters should know log levels and summary strings. They should not know
141 PDU-specific cases. PDU behavior belongs in the generated catalog.
