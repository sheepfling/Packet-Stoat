# Cesium Unity 6000.5 Findings

This note records the current state of the Cesium Unity plugin lane on
Windows with Unity `6000.5.1f1`.

## Current status

- lane: `unity-6000.5`
- host: `windows`
- status: `fail`
- primary packet:
  `artifacts/reports/unity_vendor_plugin/cesium-unity_6000_5_upstream_handoff.json`

## Proven blockers

The Unity 6000.5 lane turned out to have two separate issues.

### 1. Bad staged Reinterop artifact

The earlier `prepare-source` path used:

```powershell
dotnet publish Reinterop~ -o .
```

That produced a package-root `Reinterop.dll` that looked prepared but was only
`4096` bytes. In practice that artifact caused:

- `using Reinterop` resolution failures
- missing `ReinteropAttribute`
- missing `ReinteropNativeImplementationAttribute`
- `CS8795` partial methods with no generated implementation

This is now treated as a doctor/reporting issue as well as a source-prep issue:

- `reinterop-staged-artifact-stub`

The fixed prep path is:

1. `dotnet build Reinterop~/Reinterop.csproj`
2. copy the built `Reinterop.dll`, companion `.dll` dependencies, `.pdb`, and
   `Reinterop.deps.json` into the package root

With that corrected staging, the Unity compiler gets a real Reinterop assembly
instead of the stub artifact.

### 2. Unity 6000 editor API drift

Once the real Reinterop build output is staged, the Unity 6000.5 lane advances
to the next real blocker:

- `TreeView` obsolete
- `TreeViewItem` obsolete
- `TreeViewState` obsolete

Those errors come from Cesium editor code in:

- `Source/Editor/CesiumIonAssetsWindow.cs`
- `Source/Editor/IonAssetsTreeView.cs`

That finding is:

- `unity-6000-editor-api-drift`

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

### 5. Build and stage the real Reinterop assembly

Commands:

```powershell
dotnet build external\cesium\cesium-unity\Reinterop~\Reinterop.csproj
```

Then stage:

- `Reinterop~\bin\Debug\netstandard2.0\Reinterop.dll`
- `Reinterop~\bin\Debug\netstandard2.0\*.dll`
- `Reinterop~\bin\Debug\netstandard2.0\*.pdb`
- `Reinterop~\obj\Debug\netstandard2.0\Reinterop.deps.json`

Result:

- Reinterop compile/generation failures disappear
- Unity advances to the actual `TreeView*` editor API errors
- this is the strongest current proof that the 4 KB publish artifact was the
  wrong prep output for the Unity source-checkout lane

## Practical next steps

1. Keep the doctor/report lane catching stub `Reinterop.dll` outputs before any
   expensive Unity run starts.
2. Prepare an upstream PR or fix packet that switches Cesium source-checkout
   prep away from the stub-producing publish shortcut.
3. Patch `IonAssetsTreeView` and `CesiumIonAssetsWindow` for Unity 6000's
   generic `TreeView<T>`, `TreeViewItem<T>`, and `TreeViewState<T>` editor APIs.
4. Re-run the Unity 6000.5 handoff after the editor patch and freeze the next
   packet into the Cesium matrix.
