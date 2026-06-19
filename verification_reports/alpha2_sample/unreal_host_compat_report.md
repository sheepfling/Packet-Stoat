# Unreal Host Compatibility Report

- generated_at: `2026-06-19T15:06:12.186206+00:00`
- host_platform: `Darwin`
- host_machine: `arm64`

| Version | Discovered | Probe Status | Failure Kind | Summary |
| --- | --- | --- | --- | --- |
| 5.7 | yes | ok | none | Mac target-generation probe succeeded |
| 5.8 | yes | ok | none | Mac target-generation probe succeeded |

## Host Facts

### xcode_select

- returncode: `0`
```text
/Applications/Xcode.app/Contents/Developer
```

### sw_vers

- returncode: `0`
```text
ProductName:		macOS
ProductVersion:		26.5.1
BuildVersion:		25F80
```

### clang_version

- returncode: `0`
```text
Apple clang version 21.0.0 (clang-2100.1.1.101)
Target: arm64-apple-darwin25.5.0
Thread model: posix
InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
```

### sdk_path

- returncode: `0`
```text
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk
```

## Compatibility Interpretation

- Official Epic reference: `https://dev.epicgames.com/documentation/en-us/unreal-engine/macos-development-requirements-for-unreal-engine`
- UE 5.6 macOS baseline from Epic (kept as optional compatibility reference, not a required Alpha 2 signoff lane): minimum macOS `Sonoma 14.0`, recommended macOS `Latest macOS 14 Sonoma`, minimum Xcode `Xcode 15.2`, recommended Xcode `Xcode 15.4 or newer`.
- This host reported macOS `26.5.1`.
- This host reported toolchain `Apple clang version 21.0.0 (clang-2100.1.1.101)`.
- Alpha 2 signoff uses Unreal 5.7 and 5.8 as the supported engine lanes. Use an explicit `--versions 5.6 5.7 5.8` run only when you want optional 5.6 compatibility evidence.

## Lane Details

### 5.7

- install_root: `/Users/Shared/Epic Games/UE_5.7`
- editor_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor`
- dotnet_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/ThirdParty/DotNet/8.0.412/mac-arm64/dotnet`
- ubt_path: `/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll`
- quirk: editor app bundle present
- probe status: `ok`
- probe detail: Mac target-generation probe succeeded
- probe command:
```text
/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/ThirdParty/DotNet/8.0.412/mac-arm64/dotnet /Users/Shared/Epic Games/UE_5.7/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll FastDisOrientationVerificationEditor Mac Development -project=/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/examples/unreal/FastDisOrientationVerification/FastDisOrientationVerification.uproject -NoAction -NoHotReloadFromIDE -WaitMutex
```
- probe output excerpt:
```text
Log file: /Users/Shared/Epic Games/UE_5.7/Engine/Source/Epic/UnrealBuildTool/Log.txt
Creating makefile for FastDisOrientationVerificationEditor (no existing makefile)
Choosing MODERN XCODE based on .ini settings
UHT compiled-in object format Default
Parsing headers for FastDisOrientationVerificationEditor
  Running Internal UnrealHeaderTool "/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/examples/unreal/FastDisOrientationVerification/FastDisOrientationVerification.uproject" "/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/examples/unreal/FastDisOrientationVerification/Intermediate/Build/Mac/FastDisOrientationVerificationEditor/Development/FastDisOrientationVerificationEditor.uhtmanifest" -WarningsAsErrors -installed
UHT processed FastDisOrientationVerificationEditor in 1.6175252 seconds (14 files written)
Compiling with Mac SDK 26.5, minimum Target OS version 14.00
Building FastDisOrientationVerificationEditor...
[Upgrade]
[Upgrade] Using backward-compatible include order. The latest version of UE has changed the order of includes, which may require code changes. The current setting is:
[Upgrade]     IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_4
[Upgrade] Suppress this message by setting 'IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;' in FastDisOrientationVerificationEditor.Target.cs.
[Upgrade] Alternatively you can set this to 'EngineIncludeOrderVersion.Latest' to always use the latest include order. This will potentially cause compile errors when integrating new versions of the engine.
[Upgrade]
[Adaptive Build] Excluded from FastDisUnreal unity file: FastDisReplayActor.cpp, FastDisModule.cpp, FastDisSampleTrafficComponent.cpp, FastDisWorldSubsystem.cpp
Determining max actions to execute in parallel (8 physical cores, 8 logical cores)
  Executing up to 8 processes, one per physical core
Using Unreal Build Accelerator local executor to run 25 action(s)
  Storage capacity 40Gb
---- Starting trace ----
UbaServer - Listening on 0.0.0.0:1345
[1/25] Copy libfastdis.dylib [NoUba]
[2/25] Copy libfastdis.0.12.0.dylib [NoUba]
[3/25] Copy libfastdis.0.dylib [NoUba]
[4/25] Compile [Apple] SharedPCH.Core.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_4.h
[5/25] Compile [Apple] SharedPCH.CoreUObject.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_4.h
[6/25] Compile [Apple] SharedPCH.Slate.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_4.h
[7/25] Compile [Apple] SharedPCH.Engine.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_4.h
[8/25] Compile [Apple] SharedPCH.UnrealEd.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_4.h
[9/25] Compile [Apple] FastDisModule.cpp
[10/25] Compile [Apple] FastDisOrientationProbeActor.cpp
[11/25] Compile [Apple] FastDisOrientation.spec.cpp
[12/25] Compile [Apple] FastDisWorldSubsystem.cpp
[13/25] Compile [Apple] FastDisOrientationTestsModule.cpp
[14/25] Compile [Apple] FastDisReplayActor.cpp
[15/25] Compile [Apple] Module.FastDisUnreal.cpp
[16/25] Compile [Apple] FastDisSampleTrafficComponent.cpp
[17/25] Compile [Apple] PerModuleInline.gen.cpp
[18/25] Link [Apple] UnrealEditor-FastDisUnreal.dylib
[19/25] Compile [Apple] PerModuleInline.gen.cpp
[20/25] Compile [Apple] FastDisOrientationVerificationModule.cpp
[21/25] Compile [Apple] Module.FastDisOrientationTests.gen.cpp
[22/25] Link [Apple] UnrealEditor-FastDisOrientationVerification.dylib
[23/25] Compile [Apple] FastDisReplay.spec.cpp
[24/25] Link [Apple] UnrealEditor-FastDisOrientationTests.dylib
[25/25] WriteMetadata FastDisOrientationVerificationEditor.target [NoUba]

Trace written to file /Users/Shared/Epic Games/UE_5.7/Engine/Source/Epic/UnrealBuildTool/Log.uba with size 7.9kb
Total time in Unreal Build Accelerator local executor: 39.42 seconds
Deploying FastDisOrientationVerificationEditor Mac Development...
Deploying now!

Result: Succeeded
Total execution time: 46.96 seconds
```

### 5.8

- install_root: `/Users/Shared/Epic Games/UE_5.8`
- editor_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor`
- dotnet_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet`
- ubt_path: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll`
- quirk: editor app bundle present
- probe status: `ok`
- probe detail: Mac target-generation probe succeeded
- probe command:
```text
/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet /Users/Shared/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll FastDisOrientationVerificationEditor Mac Development -project=/Users/rick/Library/Mobile Documents/com~apple~CloudDocs/GIT/fastdis/examples/unreal/FastDisOrientationVerification/FastDisOrientationVerification.uproject -NoAction -NoHotReloadFromIDE -WaitMutex
```
- probe output excerpt:
```text
Log file: /tmp/fastdis_unreal/home/Library/Application Support/Epic/UnrealBuildTool/Log.txt
Determining max actions to execute in parallel (8 physical cores, 8 logical cores)
  Executing up to 8 processes, one per physical core
Creating makefile for FastDisOrientationVerificationEditor (no existing makefile)
UbaServer - Listening on 0.0.0.0:1345
Compiling with Mac SDK 26.5, minimum Target OS version 14.00
UHT compiled-in object format Default
Building FastDisOrientationVerificationEditor...
===== Toolchain Information =====
Using Clang compiler 21.1.6 (/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++)
  Apple clang version 21.0.0 (clang-2100.1.1.101) Target: arm64-apple-darwin25.5.0 Thread model: posix InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
Using Clang archiver (/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/libtool)
  Apple clang version 21.0.0 (clang-2100.1.1.101) Target: arm64-apple-darwin25.5.0 Thread model: posix InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
[Upgrade]
[Upgrade] Using backward-compatible include order. The latest version of UE has changed the order of includes, which may require code changes. The current setting is:
[Upgrade]     IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_6
[Upgrade] Suppress this message by setting 'IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;' in FastDisOrientationVerificationEditor.Target.cs.
[Upgrade] Alternatively you can set this to 'EngineIncludeOrderVersion.Latest' to always use the latest include order. This will potentially cause compile errors when integrating new versions of the engine.
[Upgrade]
[Adaptive Build] Excluded from FastDisUnreal unity file: FastDisReplayActor.cpp, FastDisModule.cpp, FastDisSampleTrafficComponent.cpp, FastDisWorldSubsystem.cpp
=================================
Using Unreal Build Accelerator local executor to run 21 action(s)
  CPU 8 physical cores, 8 logical cores
  Memory 16 GB physical, 12.43 GB/16 GB committed
  UBA Storage capacity 40 GB
[1/21] Copy libfastdis.0.dylib [NoUba]
[2/21] Compile [Apple] SharedPCH.UnrealEd.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_6.h
[3/21] Copy libfastdis.0.12.0.dylib [NoUba]
[4/21] Copy libfastdis.dylib [NoUba]
[5/21] Compile [Apple] FastDisOrientationTestsModule.cpp
[6/21] Compile [Apple] FastDisOrientationProbeActor.cpp
[7/21] Compile [Apple] FastDisWorldSubsystem.cpp
[8/21] Compile [Apple] FastDisSampleTrafficComponent.cpp
[9/21] Compile [Apple] Module.FastDisUnreal.cpp
[10/21] Compile [Apple] FastDisOrientation.spec.cpp
[11/21] Compile [Apple] FastDisReplayActor.cpp
[12/21] Compile [Apple] FastDisModule.cpp
[13/21] Compile [Apple] Module.FastDisOrientationTests.gen.cpp
[14/21] Compile [Apple] FastDisReplay.spec.cpp
[15/21] Compile [Apple] PerModuleInline.gen.cpp
[16/21] Compile [Apple] FastDisOrientationVerificationModule.cpp
[17/21] Link [Apple] libUnrealEditor-FastDisUnreal.dylib
[18/21] Compile [Apple] PerModuleInline.gen.cpp
[19/21] Link [Apple] libUnrealEditor-FastDisOrientationVerification.dylib
[20/21] Link [Apple] libUnrealEditor-FastDisOrientationTests.dylib
[21/21] WriteMetadata FastDisOrientationVerificationEditor.target [NoUba]

Total time in Unreal Build Accelerator local executor: 39.50 seconds
Output binary: /Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor
Deploying FastDisOrientationVerificationEditor Mac Development...
Deploying now!

Result: Succeeded
Total execution time: 49.41 seconds
Trace written to file /tmp/fastdis_unreal/home/Library/Application Support/Epic/UnrealBuildTool/Trace.uba with size 9.6kb
```
