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
python tools/godot_workflow.py demo
python tools/godot_workflow.py missing-lib
python tools/godot_workflow.py report
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
- the active Python interpreter for workflow subprocesses
- common `godot` and `scons` executable names on `PATH`
- common host-specific Godot locations on macOS, Windows, and Linux
- common Windows install shapes including standalone installs, `LOCALAPPDATA`
  installs, and Scoop-managed paths

## Host-aware artifacts

Wrapper names:

- Windows: `fastdis_gdextension.windows.template_debug.x86_64.dll`,
  `fastdis_gdextension.windows.template_release.x86_64.dll`
- macOS: `libfastdis_gdextension.macos.template_debug.dylib`,
  `libfastdis_gdextension.macos.template_release.dylib`
- Linux: `libfastdis_gdextension.linux.template_debug.x86_64.so`,
  `libfastdis_gdextension.linux.template_release.x86_64.so`

Core library names:

- Windows: `fastdis.dll`
- macOS: `libfastdis.dylib`
- Linux: `libfastdis.so`

The staging helper now prunes stale host artifacts in the Godot
`addons/fastdis/bin/` directories before copying the current runtime and
wrapper outputs. It also expects the full wrapper set declared by the
`.gdextension` manifest, so a stale debug-only or release-only bin directory is
treated as incomplete.
Each staged bin directory also carries a
`fastdis_godot_build_manifest.json` file keyed to the current wrapper sources,
manifest files, and core orientation headers. The runners use that to
distinguish a merely present wrapper from a current wrapper.

By default `tools/build_godot_extension.py` builds both `template_debug` and
`template_release` wrapper variants because Godot editor/headless runs use the
debug entry while exported templates use the release entry.
It also defaults to `--scons-jobs 1` because deterministic generated-header
builds are more important than aggressive parallelism for the operator path.
Raise that only after confirming your local `godot-cpp` setup is stable with
higher SCons fan-out.

## Demo smoke route

`python tools/godot_workflow.py demo` now exercises the runnable demo project in
headless mode. The runner:

- reuses a complete staged wrapper/shared-library set when present
- rebuilds/stages the wrapper only when the staged set is incomplete or stale
- generates `examples/godot/fastdis_demo/data/synthetic.fastdispkt`
- opens the real `fastdis_demo` scene with Godot headless
- asserts that the registered demo markers move under replay input

`python tools/godot_workflow.py full` now runs both the orientation harness and
the demo smoke lane after the shared build step.

## Missing-library route

`python tools/godot_workflow.py missing-lib` exercises the failure path required
by the Alpha 2 runnable-sample criteria. The runner:

- reuses or rebuilds the staged wrapper/shared-library set
- temporarily hides only the staged host-native `libfastdis` payload
- launches the real `fastdis_demo` scene headlessly
- asserts that the scene reports an extension/native-library load failure
  clearly instead of crashing

`python tools/godot_workflow.py full` includes this lane after the positive demo
smoke so both the success path and failure path stay rerunnable.

## Proof report

`python tools/godot_workflow.py report` writes a JSON/Markdown proof artifact
covering the full operator surface:

- doctor
- build/stage
- orientation verify
- replay demo smoke
- missing-native-library failure path

Artifacts:

```text
build/reports/godot_workflow_report.json
build/reports/godot_workflow_report.md
```

The report short-circuits runnable lanes as `blocked` when doctor proves a real
host/tooling problem, so the summary distinguishes “this machine cannot run the
lane yet” from “the lane ran and failed.”

## No-space work root

The Godot helpers default to a no-space temp root:

```text
/private/tmp/fastdis_godot/
```

This is used for:

- native CMake build output
- Godot home/config/cache state
- Godot temp state via `TMPDIR`
- macOS Core Foundation user-home resolution via `CFFIXED_USER_HOME`
- Windows user-profile/appdata resolution via `USERPROFILE`, `APPDATA`, and
  `LOCALAPPDATA`
- a best-effort no-space repo alias when the repo itself lives under a path with
  spaces

That is specifically intended to reduce path-related breakage for iCloud-backed
or other space-containing workspace roots.
