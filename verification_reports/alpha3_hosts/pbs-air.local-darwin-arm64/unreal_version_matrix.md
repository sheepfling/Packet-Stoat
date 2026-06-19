# Unreal Version Matrix

- generated_at: `2026-06-19T17:27:07.013748+00:00`
- host_platform: `darwin`

| Version | Discovered | Plugin Build | Orientation | Demo | Notes |
| --- | --- | --- | --- | --- | --- |
| 5.7 | yes | passed | failed | failed | orientation harness failed; managed/sandboxed run denied Unreal writes under ~/Library; rerun outside the sandbox or provide writable Unreal log/cache paths; demo smoke failed |
| 5.8 | yes | passed | failed | failed | orientation harness failed; managed/sandboxed run denied Unreal writes under ~/Library; rerun outside the sandbox or provide writable Unreal log/cache paths; demo smoke failed |

## Install Quirks

### 5.7
- install_root: `/Users/Shared/Epic Games/UE_5.7`
- editor_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor`
- uat_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Build/BatchFiles/RunUAT.sh`
- quirk: editor app bundle present
- lane artifacts:
  - plugin_build: passed (`verification_reports/alpha3_current/unreal_matrix_5_7_plugin_build.log`)
  - orientation: failed (`verification_reports/alpha3_current/unreal_matrix_5_7_orientation.log`)
  - demo: failed (`verification_reports/alpha3_current/unreal_matrix_5_7_demo.log`)
### 5.8
- install_root: `/Users/Shared/Epic Games/UE_5.8`
- editor_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor`
- uat_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh`
- quirk: editor app bundle present
- lane artifacts:
  - plugin_build: passed (`verification_reports/alpha3_current/unreal_matrix_5_8_plugin_build.log`)
  - orientation: failed (`verification_reports/alpha3_current/unreal_matrix_5_8_orientation.log`)
  - demo: failed (`verification_reports/alpha3_current/unreal_matrix_5_8_demo.log`)
