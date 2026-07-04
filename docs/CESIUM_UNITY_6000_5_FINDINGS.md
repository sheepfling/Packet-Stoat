# Cesium Unity 6000.5 Findings

This note records the current state of the Cesium Unity plugin lane on
Windows with Unity `6000.5.1f1`.

## Current status

- lane: `unity-6000.5`
- host: `windows`
- status: `fail`
- primary packet:
  `artifacts/reports/unity_vendor_plugin/cesium-unity_6000_5_upstream_handoff.json`

## Proven blocker

The current Unity proof packet consistently shows:

- `analyzer_present_in_rsp = true`
- `generated_reinterop_paths = 0`
- compile failures for:
  - missing `ReinteropAttribute`
  - missing `ReinteropNativeImplementationAttribute`
  - `CS8795` partial methods with no generated implementation

That is the current primary finding:

- `reinterop-generator-inactive`

In other words, Unity/Bee includes `Packages/cesium-unity/Reinterop.dll` in the
compiler invocation, but the Reinterop generator does not produce the generated
C# glue before compile fails.

## Secondary drift seen earlier

One earlier rerun also surfaced editor API drift in
`Source/Editor/IonAssetsTreeView.cs` under Unity 6000:

- `TreeViewItem` obsolete
- `TreeViewState` obsolete

That likely becomes the next blocker once Reinterop generation is working.

## Experiments already tried

### 1. Explicit source checkout handoff

Command:

```powershell
.\.venv\Scripts\python.exe tools\unity_vendor_workflow.py handoff `
  --vendor cesium-unity `
  --plugin-root external\cesium\cesium-unity `
  --unity-version 6000.5 `
  --clean-project
```

Result:

- reproduced the failure cleanly
- confirmed analyzer inclusion
- still `generated_reinterop_paths = 0`

### 2. Replace package-root `Reinterop.deps.json` with the larger build output variant

Source used:

- `external/cesium/cesium-unity/Reinterop~\bin\Debug\netstandard2.0\Reinterop.deps.json`

Result:

- no change to Unity outcome
- generator still inert

### 3. Swap Reinterop from legacy `ISourceGenerator` to in-tree incremental generator

Temporary experiment:

- changed `Reinterop~\Reinterop.csproj` to exclude `RoslynSourceGenerator.cs`
  instead of `RoslynIncrementalGenerator.cs`
- republished with `dotnet publish Reinterop~ -o .`

Result:

- no change to Unity outcome
- generator still inert

This experiment was reverted afterward.

### 4. Manual staged `.meta` edit

A manual attempt to force-enable the staged `Reinterop.dll.meta` using a quick
PowerShell replacement corrupted the YAML and produced Unity YAML assertions.

Result:

- not a valid lane fix
- only useful as a reminder that any `.meta` normalization must be done with
  a proper YAML-safe rewrite

## Practical next steps

1. Inspect whether Unity 6000 requires analyzer companion assemblies to sit
   alongside `Reinterop.dll` in the staged package root.
2. Build a minimal Roslyn replay outside Unity that can confirm whether
   `Reinterop.dll` is actually executing or silently skipped.
3. Once Reinterop generation works, patch `IonAssetsTreeView` for Unity 6000's
   generic `TreeViewItem<T>` / `TreeViewState<T>` surface if the editor compile
   drift remains.
