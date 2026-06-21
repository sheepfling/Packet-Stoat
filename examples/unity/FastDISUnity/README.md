# FastDIS for Unity

This is an Alpha5 UPM package scaffold for a Unity adapter over the FastDIS
native C ABI. It is not yet a runnable Unity DIS ingest plugin.

## Install During Alpha

Use Unity Package Manager:

```text
Add package from git URL:
https://github.com/sheepfling/Packet-Stoat.git?path=examples/unity/FastDISUnity
```

## Current Scope

- package manifest and UPM layout
- C# P/Invoke declaration surface for the native C ABI
- Unity ENU frame mapping helpers
- placeholder world/entity components
- diagnostics window scaffold

## Deferred

- staged platform native libraries
- replay source implementation
- UDP source implementation
- snapshot application loop
- runnable Unity demo scenes
- Unity Asset Store submission

## Design Rule

Unity code binds to `fastdis` through the C ABI. It should not bind directly to
C++ RAII wrappers.
