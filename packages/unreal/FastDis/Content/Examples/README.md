# FastDIS Unreal Example Content

This folder is intentionally source-controlled so the packaged plugin is shaped
as a content-capable Unreal product. Binary `.uasset` demo maps and UMG widgets
belong here once authored in the Unreal editor.

Current source-backed demo entry point:

- Place `AFastDisDemoController` in a map.
- Configure `UdpReceiver`, `UdpSender`, `GeoreferenceAdapter`, and
  `SampleTraffic` on that actor.
- Leave `DebugMarkers` enabled to visualize decoded Fire, Detonation, and
  Designator events through `UFastDisPduDebugMarkerComponent`.
- Derive a Blueprint widget from `UFastDisRuntimeStatusWidget`, or bind custom
  UI widgets to `RuntimeMonitor.GetLastSnapshot` / `RefreshMonitorSnapshot`.

The source demo controller keeps the Fab package useful before binary sample
assets are committed.
