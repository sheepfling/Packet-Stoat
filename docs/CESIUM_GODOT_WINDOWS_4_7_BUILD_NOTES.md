# Cesium Godot Windows 4.7 Build Notes

This note records the exact process and patch direction used to turn the
Battle Road Cesium Godot lane green on Windows with Godot 4.7.

## Vendor checkout

- upstream: `https://github.com/Battle-Road-Labs/3D-Tiles-For-Godot`
- local plugin root:
  `external/cesium/3D-Tiles-For-Godot`

## Verified proof command

```powershell
.\.venv\Scripts\python.exe tools\godot_vendor_workflow.py handoff `
  --vendor cesium-godot `
  --plugin-root external\cesium\3D-Tiles-For-Godot `
  --scons-jobs 2 `
  --log-mode capture `
  --log-tail-lines 160 `
  --build-json-out artifacts\reports\godot_vendor_plugin\cesium-godot_build_windows_live.json `
  --build-md-out artifacts\reports\godot_vendor_plugin\cesium-godot_build_windows_live.md `
  --log-out artifacts\reports\godot_vendor_plugin\cesium-godot_build_windows_live.log `
  --json-out artifacts\reports\godot_vendor_plugin\cesium-godot_upstream_handoff_windows_live.json `
  --md-out artifacts\reports\godot_vendor_plugin\cesium-godot_upstream_handoff_windows_live.md
```

## Required workflow normalizations

- delete `cesium_godot/native/CMakeCache.txt` before configure
- delete `cesium_godot/native/CMakeFiles` before configure
- use the configured short work root from `FASTDIS_GODOT_WORK_ROOT`
- set `EZVCPKG_BASEDIR` under that short work root to avoid long-path churn

Those normalizations are now emitted by `tools/godot_vendor_workflow.py` into
the report packet.

## Vendor-side patch that unblocked the Windows build

The decisive fix was in
`external/cesium/3D-Tiles-For-Godot/cesium_godot/SCsub`.

1. Normalize Windows `LIBPATH` prepends to lists rather than bare strings.
2. Only keep `abseil_dll` in the Windows library list when that library is
   actually present in the installed vcpkg layout.

Without that patch, the Windows lane failed at link time with:

```text
LINK : fatal error LNK1181: cannot open input file 'abseil_dll.lib'
```

The installed vcpkg layout on this host provided static `absl_*.lib` files
under `x64-windows-static`, but did not provide `abseil_dll.lib`.

## Current proof artifacts

- `artifacts/reports/godot_vendor_plugin/cesium-godot_build_windows_live.json`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_build_windows_live.md`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_build_windows_live.log`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_upstream_handoff_windows_live.json`
- `artifacts/reports/godot_vendor_plugin/cesium-godot_upstream_handoff_windows_live.md`

## Matrix status after refresh

- Unreal 5.7: pass
- Unreal 5.8: pass
- Godot 4.7: pass
- Unity 6000.5: fail

The remaining Cesium plugin gate is Unity/Reinterop, not Godot.
