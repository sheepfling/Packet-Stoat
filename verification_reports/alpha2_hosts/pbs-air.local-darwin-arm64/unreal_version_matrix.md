# Unreal Version Matrix

- generated_at: `2026-06-19T11:51:01.203887+00:00`
- host_platform: `darwin`

| Version | Discovered | Plugin Build | Orientation | Demo | Notes |
| --- | --- | --- | --- | --- | --- |
| 5.7 | yes | passed | passed | passed | none |
| 5.8 | yes | passed | passed | passed | none |

## Install Quirks

### 5.7
- install_root: `/Users/Shared/Epic Games/UE_5.7`
- editor_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor`
- uat_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Build/BatchFiles/RunUAT.sh`
- quirk: editor app bundle present
- lane artifacts:
  - plugin_build: passed (`verification_reports/alpha2_sample/unreal_matrix_5_7_plugin_build.log`)
  - orientation: passed (`verification_reports/alpha2_sample/unreal_matrix_5_7_orientation.log`)
  - demo: passed (`verification_reports/alpha2_sample/unreal_matrix_5_7_demo.log`)
### 5.8
- install_root: `/Users/Shared/Epic Games/UE_5.8`
- editor_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor`
- uat_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh`
- quirk: editor app bundle present
- lane artifacts:
  - plugin_build: passed (`verification_reports/alpha2_sample/unreal_matrix_5_8_plugin_build.log`)
  - orientation: passed (`verification_reports/alpha2_sample/unreal_matrix_5_8_orientation.log`)
  - demo: passed (`verification_reports/alpha2_sample/unreal_matrix_5_8_demo.log`)
