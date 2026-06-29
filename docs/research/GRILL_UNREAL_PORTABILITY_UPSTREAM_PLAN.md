# GRILL Unreal Portability Upstream Plan

This document turns the current local GRILL Unreal portability work into an
upstream-friendly plan.

Scope:

- make the public `GRILL_DISPluginForUnreal` source route credible on Unreal
  `5.7` and `5.8`
- preserve the existing Windows route
- add reproducible Mac and Linux rebuild steps
- keep example-project cleanup separate from the core plugin portability fix

## Why Split The Work

Two repos are involved and they should not be mixed into one PR:

1. `GRILL_DISPluginForUnreal`
2. `GRILL_DISForUnrealExample`

The plugin repo is the real portability surface.

The example repo is a consumer of that plugin plus extra dependencies such as
Cesium and LowEntry. If the example still breaks after the plugin is portable,
that should be tracked as a separate issue rather than muddying the plugin PR.

## Near-Term Goal

Deliver a minimal upstream plugin PR that makes the public GRILL Unreal plugin
buildable on Unreal `5.7` and `5.8` across `Mac`, `Windows`, and `Linux`,
preserves the current Windows DLL route, adds deterministic Mac/Linux OpenDIS
rebuild steps, and documents the exact proof workflow. Follow with a second PR
that aligns the example project to the updated plugin without overstating any
remaining marketplace or host dependency gaps.

## Issue Checklist

Use this as the top-level tracking issue or GitHub project checklist.

### Plugin Portability

- [ ] Remove the stale Unreal engine pin from the plugin descriptor.
- [ ] Confirm the plugin descriptor module allowlist includes `Mac`, `Win64`,
      and `Linux`.
- [ ] Keep the Windows dynamic `OpenDIS6.dll` / `OpenDIS6.lib` route intact.
- [ ] Add static `libOpenDIS6.a` linkage for `Mac`.
- [ ] Add static `libOpenDIS6.a` linkage for `Linux`.
- [ ] Restrict runtime `GetDllHandle` logic to Windows only.
- [ ] Fix vendored OpenDIS export and warning-guard headers so they compile on
      Clang/GCC and not only MSVC.
- [ ] Add a reproducible Mac payload build command.
- [ ] Add a reproducible Linux payload build command from Docker.
- [ ] Document the payload rebuild process in the repo README.

### Proof And Verification

- [ ] Prove Mac payload build on a Mac host.
- [ ] Prove `RunUAT BuildPlugin` on Unreal `5.7` for Mac.
- [ ] Prove `RunUAT BuildPlugin` on Unreal `5.8` for Mac.
- [ ] Prove the existing Windows packaging route still works.
- [ ] Prove Linux static payload build from Docker.
- [ ] Prove `RunUAT.sh BuildPlugin -TargetPlatforms=Linux` on a Linux Unreal
      host or private Unreal Linux container.
- [ ] Capture exact commands, engine versions, and outputs for reruns.

### Example Project Follow-Up

- [ ] Update the example project to the portable plugin commit.
- [ ] Keep the `UE 5.8` C++ standard fix in the example module rules.
- [ ] Audit example plugin dependencies and mark what is required versus
      optional.
- [ ] Separate “plugin failed” from “example dependency unavailable” in notes
      and evidence.

## PR 1 Draft

Repository:

- `GRILL_DISPluginForUnreal`

Suggested title:

- `Add UE 5.7/5.8 cross-platform portability for Mac, Win64, and Linux`

Suggested summary:

- remove the stale engine-version pin from the plugin descriptor
- expand the runtime and editor module platform allowlists to `Mac`, `Win64`,
  and `Linux`
- keep the existing Windows DLL-based OpenDIS route
- add static OpenDIS linkage for Mac and Linux
- fix vendored OpenDIS headers that assumed MSVC-only compilation
- add rerunnable scripts for building Mac and Linux OpenDIS payloads
- document a reproducible Linux `BuildPlugin` proof route using a private
  Unreal Linux container

Suggested rationale:

The public plugin source route currently requires extra portability work to be
credible on modern Unreal `5.7` and `5.8` lanes outside the historical Windows
path. This PR keeps the Windows route intact while making the plugin descriptor,
build rules, vendored OpenDIS headers, and native payload workflow portable
enough for cross-platform packaging proof.

Suggested test plan:

1. On a Mac host, build the static Mac OpenDIS payload.
2. Package the plugin with Unreal `5.7` for `Mac`.
3. Package the plugin with Unreal `5.8` for `Mac`.
4. On Windows, package the plugin and confirm the existing DLL route still
   works.
5. Build the Linux static OpenDIS payload from Docker.
6. On a Linux Unreal host or private Unreal Linux container, run
   `RunUAT.sh BuildPlugin -TargetPlatforms=Linux`.

Files expected in this PR:

- `GRILLDISForUnreal.uplugin`
- `Source/DISRuntime/DISRuntime.Build.cs`
- `Source/DISRuntime/Private/DISRuntime.cpp`
- `Source/ThirdParty/include/dis6/opendis6_export.h`
- `Source/ThirdParty/include/dis6/utils/DataStream.h`
- `Source/ThirdParty/include/dis7/opendis7_export.h`
- `Source/ThirdParty/include/dis7/utils/DataStream.h`
- `Scripts/build_opendis_static.py`
- `Scripts/build_plugin_linux_container.sh`
- `Scripts/linux_proof.env.example`
- `README.md`
- `CHANGELOG.md`

## PR 2 Draft

Repository:

- `GRILL_DISForUnrealExample`

Suggested title:

- `Align the Unreal example project with the portable plugin and UE 5.8`

Suggested summary:

- update the example to the portable plugin commit
- retain the `UE 5.8`-safe C++ standard setting
- clarify which example dependencies are required and which are merely part of
  the richer sample environment
- document any remaining host-specific or marketplace-specific blockers

Suggested rationale:

The example project should be updated only after the plugin repo itself is
portable. This keeps the source of failures obvious: plugin portability issues
belong in the plugin repo, while sample-scene and third-party dependency drift
belong in the example repo.

Suggested test plan:

1. Open the example on Unreal `5.7`.
2. Open the example on Unreal `5.8`.
3. Confirm it consumes the updated plugin revision.
4. Record any remaining failures as dependency-specific rather than plugin-core
   failures.

Files expected in this PR:

- `GRILLDISExample.uproject`
- `Source/GRILLDISExample/GRILLDISExample.Build.cs`
- plugin submodule or vendored plugin pointer updates
- README or setup note updates if needed

## Junior-Friendly Runbook

This runbook is intentionally explicit so it can be rerun without reconstructing
context from chat history.

### 1. Prepare The Source Route

From the `fastdis` repo:

```bash
python tools/prepare_grill_source_route.py
python tools/run_grill_unreal_source_smoke.py --engine-version 5.8
```

This confirms the checkouts exist and records the current public-route status.

### 2. Mac Proof For The GRILL Plugin Repo

From `GRILL_DISPluginForUnreal`:

```bash
python3 Scripts/build_opendis_static.py --platform Mac --clean
```

Expected output:

- `Source/ThirdParty/Binaries/Mac/libOpenDIS6.a`

Then package the plugin on each target Unreal lane:

```bash
"$FASTDIS_UNREAL_57_UAT" BuildPlugin \
  -Plugin="$FASTDIS_GRILL_UNREAL_PLUGIN" \
  -Package="$FASTDIS_GRILL_BUILDPLUGIN_OUT_57" \
  -TargetPlatforms=Mac \
  -StrictIncludes
```

```bash
"$FASTDIS_UNREAL_58_UAT" BuildPlugin \
  -Plugin="$FASTDIS_GRILL_UNREAL_PLUGIN" \
  -Package="$FASTDIS_GRILL_BUILDPLUGIN_OUT_58" \
  -TargetPlatforms=Mac \
  -StrictIncludes
```

Record:

- engine version
- exact command
- exit code
- packaged output directory

### 3. Windows Proof

On a Windows Unreal host, run the equivalent packaging command with
`-TargetPlatforms=Win64` and confirm the plugin still packages against the
historical DLL route.

Suggested command shape:

```powershell
RunUAT.bat BuildPlugin `
  -Plugin="%FASTDIS_GRILL_UNREAL_PLUGIN%" `
  -Package="%FASTDIS_GRILL_BUILDPLUGIN_OUT_WIN64%" `
  -TargetPlatforms=Win64 `
  -StrictIncludes
```

### 4. Linux Static Payload Build From Docker

From `GRILL_DISPluginForUnreal` on the Mac host:

```bash
python3 Scripts/build_opendis_static.py --platform Linux --docker --clean
```

Expected output:

- `Source/ThirdParty/Binaries/Linux/libOpenDIS6.a`

This proves the archive can be built reproducibly, but not yet that Unreal can
package the plugin on Linux.

### 5. Linux Unreal Packaging Proof

This step requires either:

- a real Linux Unreal host, or
- a private Unreal Linux container image that already contains a Linux Unreal
  development install

Copy the env template:

```bash
cp Scripts/linux_proof.env.example Scripts/linux_proof.env
```

Fill in:

- `UE_LINUX_IMAGE`
- `UE_ROOT_IN_CONTAINER` if different from `/opt/unreal-engine`

Then run:

```bash
set -a
source Scripts/linux_proof.env
set +a
chmod +x Scripts/build_plugin_linux_container.sh
Scripts/build_plugin_linux_container.sh
```

Expected output:

- `.build/grill_buildplugin_linux/package`

### 6. Example Project Follow-Up

After the plugin PR is stable, move to `GRILL_DISForUnrealExample`:

- confirm the example points to the portable plugin revision
- keep the `CppStandardVersion.Default` fix
- document any remaining third-party dependency blockers rather than silently
  treating them as plugin failures

## Where User Help Is Most Valuable

The highest-leverage operator help is host coverage:

- Windows host proof for `Win64`
- Linux Unreal host or private Unreal Linux image for final `BuildPlugin`
  verification
- upstream preference on whether they want the example cleanup split into a
  second PR

## Messaging Guardrails

Until the Linux and Windows reruns are captured, keep claims narrow:

- safe: “we have a minimal portability patch set for the GRILL Unreal plugin”
- safe: “the public GRILL Unreal route needed portability work for modern
  Unreal and non-Windows hosts”
- unsafe: “GRILL fully supports Mac and Linux now”
- unsafe: “the example project is fixed everywhere”

The public claim should follow proof, not lead it.
