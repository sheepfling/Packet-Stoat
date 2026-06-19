# Godot Workflow

Alpha 2 needs the Godot path to be rerunnable and machine-tolerant in the same
way as the Unreal path.

The operator entry point is:

```bash
python tools/godot_workflow.py doctor
python tools/godot_workflow.py full
```

## Commands

```bash
python tools/godot_workflow.py discover
python tools/godot_workflow.py doctor
python tools/godot_workflow.py build
python tools/godot_workflow.py verify
python tools/godot_workflow.py full
```

## Discovery contract

`tools/godot_env.py` is the shared install-discovery and host-layout layer used
by:

- `tools/godot_workflow.py`
- `tools/build_godot_extension.py`
- `tools/run_godot_orientation_verification.py`

It resolves:

- `FASTDIS_GODOT`
- `FASTDIS_SCONS`
- common `godot` and `scons` executable names on `PATH`
- common host-specific Godot locations on macOS, Windows, and Linux

## Host-aware artifacts

Wrapper names:

- Windows: `fastdis_gdextension.windows.template_debug.x86_64.dll`
- macOS: `libfastdis_gdextension.macos.template_debug.dylib`
- Linux: `libfastdis_gdextension.linux.template_debug.x86_64.so`

Core library names:

- Windows: `fastdis.dll`
- macOS: `libfastdis.dylib`
- Linux: `libfastdis.so`

## No-space work root

The Godot helpers default to a no-space temp root:

```text
/private/tmp/fastdis_godot/
```

This is used for:

- native CMake build output
- Godot home/config/cache state
- a best-effort no-space repo alias when the repo itself lives under a path with
  spaces

That is specifically intended to reduce path-related breakage for iCloud-backed
or other space-containing workspace roots.
