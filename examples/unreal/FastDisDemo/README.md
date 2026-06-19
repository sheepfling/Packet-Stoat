# FastDIS Unreal Demo

This directory tracks the Alpha 2 Unreal demo setup without checking a full UE
project or generated build products into the source bundle.

Use the plugin sample in `../FastDis/` together with the host-project helper:

```bash
python tools/build_unreal_plugin.py --clean-package --open-rider
```

That creates:

```text
build/unreal/FastDisHostProject/HostProject.uproject
```

Inside the host project or your own UE project:

1. Enable the `FastDIS` plugin.
2. Add `AFastDisReplayActor` to a level.
3. Point `ReplayFile` at a `.fastdispkt` replay.
4. Bind DIS entity IDs to actors with `ActorBindings`.
5. Configure georeference, snapshot slots, stale ticks, and transform mode.

The generated host project is intentionally kept out of source control so the
Alpha 2 bundle remains source-only and repeatable across macOS, Windows, and
Linux hosts.
