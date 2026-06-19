# Unreal Version Matrix

Alpha 2 needs a repeatable Unreal verification route that does not assume one
fixed install path or one fixed editor binary layout.

Current supported matrix target:

- Unreal `5.6`
- Unreal `5.7`
- Unreal `5.8`

## Discovery Contract

`tools/unreal_env.py` is the shared install-discovery layer used by:

- `tools/build_unreal_plugin.py`
- `tools/run_unreal_orientation_verification.py`
- `tools/list_unreal_installs.py`
- `tools/run_unreal_matrix.py`

It resolves Unreal installs in this order:

1. repo-local `.env` / `.env.local` versioned variables such as
   `FASTDIS_UNREAL_ENGINE_DIR_5_7`
2. unversioned variables such as `FASTDIS_UNREAL_ENGINE_DIR`
3. common install roots for the current host OS

Accepted engine-root forms:

- install root, for example `/Users/Shared/Epic Games/UE_5.7`
- direct `Engine/` path, which is normalized back to the install root

Accepted editor forms:

- direct executable path
- macOS `.app` bundle path, which is normalized to its inner executable

## Recorded Quirks

The matrix report records install quirks rather than hiding them. Examples:

- macOS install has `UnrealEditor.app` and `UnrealEditor`, but no
  `UnrealEditor-Cmd`
- `RunUAT` missing
- `UnrealBuildTool.dll` missing
- no direct editor executable discovered

That gives us a durable place to encode host-specific differences without
special-casing them in docs by hand.

## Version-Neutral Harness Rules

The orientation verification project is intentionally not pinned to one Unreal
minor version in its target files.

Rules:

- use `BuildSettingsVersion.V6`
- do not hard-code `IncludeOrderVersion.Unreal5_7`
- launch the harness through an explicit editor selected by
  `--engine-version`

The project file may still be opened in a specific editor, but the scripted
path is the source of truth for matrix verification.

## Commands

List discovered installs:

```bash
python tools/list_unreal_installs.py
python tools/list_unreal_installs.py --format json
```

Run one explicit version:

```bash
python tools/build_unreal_plugin.py --engine-version 5.7 --clean-package
python tools/run_unreal_orientation_verification.py --engine-version 5.7
```

Run the full matrix and write reports:

```bash
python tools/run_unreal_matrix.py
```

Reports are written to:

```text
build/reports/unreal_version_matrix.json
build/reports/unreal_version_matrix.md
```
