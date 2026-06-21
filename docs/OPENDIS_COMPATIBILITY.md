# OpenDIS Compatibility Position

Packet Stoat and OpenDIS optimize for different jobs.

Packet Stoat is designed for high-rate ingestion, filtering, Entity State
extraction, replay, and engine handoff. It avoids building deep object trees in
the hot path and keeps the native C ABI stable for hosts such as Unreal, Godot,
Python `ctypes`, Rust, C#, Go, and C/C++.

OpenDIS remains the better choice when the main requirement is a generated
object model for broad semantic DIS PDU manipulation.

## Current Support Levels

- Header/catalog compatibility: broad DIS 6/7 catalog surface.
- Entity State compatibility: fast prefix/transform path and canonical entity
  conversion.
- Full object-model compatibility: intentionally deferred.

## Practical Guidance

Use Packet Stoat when you need to scan/filter many packets, maintain latest
Entity State, feed an engine, or build replay/network verification tools.

Use OpenDIS when you need a full generated object graph for many PDU families
and maximum semantic coverage is more important than hot-path allocation cost.

