# Cesium macOS Silicon Build Notes

This note tracks the current Cesium Unreal issues that block a clean macOS
arm64 build on Apple Silicon hardware in this repo.

The goal is simple:

1. make the public `cesium-unreal` source route package on macOS arm64
2. keep the fix list small and upstreamable
3. preserve a repeatable local retry command for 5.7 and 5.8

## Current Retry Command

The active retry path is:

```bash
python3 tools/unreal_vendor_workflow.py build \
  --vendor cesium \
  --engine-version 5.8 \
  --plugin-root external/cesium/cesium-unreal \
  --uplugin CesiumForUnreal.uplugin \
  --package-dir build/unreal_vendor_plugins/cesium/5_8/CesiumForUnreal \
  --target-platforms Mac \
  --mac-architectures arm64 \
  --disable-uba \
  --clean-package
```

On this managed macOS host, `--disable-uba` is still the safest route because
Unreal Build Accelerator attempts to allocate shared memory and bind sockets
that the sandbox denies.

## 5.8 Proof

The UE 5.8 macOS arm64 package lane completed successfully after the source
fixes below were applied.

Proof points:

- final result: `Succeeded`
- package path: `build/unreal_vendor_plugins/cesium/5_8/CesiumForUnreal`
- host log:
  `/tmp/fastdis_unreal/home/Library/Logs/Unreal Engine/LocalBuildLogs/UBA-UnrealEditor-Mac-Development.txt`

Operational note:

- the linker still emitted ThirdParty macOS version warnings, but they did not
  fail the build
- `--disable-uba` remained required on this managed host

## Known Compile Fixes

### 1. Remove unreachable tail return in `CesiumTextureUtility.cpp`

Observed failure:

- `CesiumTextureUtility.cpp:476:10`
- Clang warning promoted to error:
  `-Wunreachable-code-return`

Root cause:

- the function already returned from every branch inside the `switch`
- the trailing `return std::nullopt;` could never execute

Fix:

- delete the dead return after the `if` / `switch` chain
- let control flow end naturally once every branch returns

Current on-disk file:

- [CesiumTextureUtility.cpp](/Users/rick/LocalStorage/GIT_LOCAL/active/fastdis/external/cesium/cesium-unreal/Source/CesiumRuntime/Private/CesiumTextureUtility.cpp)

### 2. Replace the single-item actor iterator loop in `CesiumGaussianSplatSubsystem.cpp`

Observed failure:

- `CesiumGaussianSplatSubsystem.cpp:159:68`
- Clang warning promoted to error:
  `-Wunreachable-code-loop-increment`

Root cause:

- the code only needed the first matching actor
- a `for` loop with `TActorIterator` suggested an increment path that the
  compiler could prove was never used

Fix:

- switch to a single `TActorIterator` value
- guard it with `if (It)` and return after initializing the first actor

Current on-disk file:

- [CesiumGaussianSplatSubsystem.cpp](/Users/rick/LocalStorage/GIT_LOCAL/active/fastdis/external/cesium/cesium-unreal/Source/CesiumRuntime/Private/CesiumGaussianSplatSubsystem.cpp)

### 3. Keep the `IonQuickAddPanel.cpp` window capture safe

This was a separate editor-side cleanup that matters for the same macOS
compile lane.

Fix:

- capture a `TWeakPtr<SWindow>` instead of a reference to the window being
  constructed
- avoid using the window from inside its own initializer in the dismissal
  callback

Current on-disk file:

- [IonQuickAddPanel.cpp](/Users/rick/LocalStorage/GIT_LOCAL/active/fastdis/external/cesium/cesium-unreal/Source/CesiumEditor/Private/IonQuickAddPanel.cpp)

## Validation Checklist

After each source fix:

1. rerun the 5.8 macOS arm64 build command above
2. confirm the compile log advances beyond the previous failing file
3. keep the package directory clean so the retry cannot reuse stale output
4. verify the final `BuildPlugin` output exists under the versioned package
   directory

## Fork Incorporation

If we need to carry these changes in a fork until upstream takes them, the fork
should include the same narrow source edits and nothing broader:

1. `CesiumTextureUtility.cpp`
   Remove the unreachable trailing `return std::nullopt;` so Clang does not
   reject the function on macOS with warnings-as-errors.
2. `CesiumGaussianSplatSubsystem.cpp`
   Keep the first-actor initialization rewritten as a single iterator guarded
   by `if (It)` so the compiler no longer sees a dead loop increment path.
3. `IonQuickAddPanel.cpp`
   Preserve the weak Slate window capture fix so the editor-side build stays
   clean on the same lane.

That is the practical fork payload for the current macOS silicon build break.
Anything beyond that should be treated as a separate upstream issue, not folded
into the same compatibility patch.

## 5.7 vs 5.8

5.7 was the baseline lane.

5.8 was the stricter lane that exposed the compiler-cleanup issues.

What belongs in a fork:

- the three source edits listed above
- the Mac arm64 packaging flags used for the retry
- the `--disable-uba` host workaround for this sandboxed machine

What does not belong in the fork patchset:

- the ThirdParty linker warnings, unless they become a separate packaging
  blocker
- the generated package output under `build/unreal_vendor_plugins`
- unrelated cleanup that is not needed for the macOS silicon compile path

## Upstreaming Note

These are all the kind of narrow, compiler-driven cleanups that should be easy
to upstream:

- remove dead code that Clang 16+ rejects as unreachable
- make iterator intent explicit when only the first actor matters
- prefer safe weak captures for Slate callbacks that outlive local scope
