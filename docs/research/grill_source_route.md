# GRILL Source Route

This note records the current source-first route for GRILL comparison work.
The benchmark program should treat the AF-GRILL GitHub organization as the
authoritative public source for GRILL Unity and Unreal code, examples, and
install expectations unless a newer official distribution path is pinned.

## Public Repositories

Observed in the AF-GRILL GitHub organization on 2026-06-26:

- `AF-GRILL/DISPluginForUnreal`
- `AF-GRILL/DISPluginForUnity`
- `AF-GRILL/DISForUnrealExample`
- `AF-GRILL/DISForUnityExample`

These four repositories are enough to define the current public source route:

- plugin source lives in the two `DISPluginFor*` repositories
- engine-specific example projects live in the two `DISFor*Example`
  repositories

## Unreal Route

Current public GRILL Unreal plugin route:

- source plugin repo: `AF-GRILL/DISPluginForUnreal`
- example project repo: `AF-GRILL/DISForUnrealExample`
- current public benchmark branch policy: use remote branch `ue5` for both repos

Current public repo guidance:

- the plugin README says this public plugin was made for Unreal Engine `4.27`
- install path is source-first: clone the repository, put the unpacked plugin
  folder into a project's `Plugins/` directory, then let Unreal rebuild needed
  modules
- the example project README says the example uses Unreal Engine `4.27`
- the example project README requires `git clone --recurse-submodule` because
  it contains submodules and LFS-backed content

Implication for FastDIS:

- if we want a same-host Unreal comparison on this Mac with Unreal `5.8`, we
  need to verify whether the public `DISPluginForUnreal` source actually builds
  or migrates there
- the GRILL Unreal example repo is part of the source route and should be
  considered a likely benchmark-host setup path

## Unity Route

Current public GRILL Unity plugin route:

- source plugin repo: `AF-GRILL/DISPluginForUnity`
- example project repo: `AF-GRILL/DISForUnityExample`
- current public benchmark branch policy: use remote branch `main` for the
  plugin repo and `github` for the example repo

Current public repo guidance:

- the plugin README says this public plugin was made for Unity `2020.3.26f1`
- install path is source-first: clone the repository, put the unpacked plugin
  folder into a project's `Assets/` folder, then let Unity build the added
  files
- the example project README says the example uses Unity `2021.3.11f1`
- the example project README explicitly says the project should use the Git
  submodule route rather than the Asset Store plugin

Implication for FastDIS:

- our current local editor is Unity `6000.5.0f1`, which is much newer than the
  public GRILL plugin and example pins
- the Unity comparison lane should treat GRILL import/build compatibility on
  modern Unity as an empirical question, not an assumption

## Current Local Evidence

Current local machine evidence on 2026-06-26:

- local Unity source checkout exists at `external/grill/GRILL_DISPluginForUnity`
- local benchmark branch policy keeps that checkout on `main`
- local Unity package also exists at
  `<local GRILL Unity package path>`
- current local Unity editors include `6000.3.18f1` and `6000.5.0f1`
- current local Unreal installs include `UE_4.27`, `UE_5.6`, `UE_5.7`, and
  `UE_5.8`
- local Unreal source checkouts exist at
  `external/grill/GRILL_DISPluginForUnreal` and
  `external/grill/GRILL_DISForUnrealExample`
- local benchmark branch policy keeps those checkouts on `ue5`

Current local Unity import evidence:

- source-checkout import smoke now passes on macOS with Unity `6000.5.0f1`
- automated same-host GRILL Unity baseline capture now succeeds on the public
  source checkout
- the remaining Unity competitor gap is no longer importability; it is direct
  comparator alignment and publishable matched metrics

Relevant local artifacts:

- `verification_reports/unity_grill_baseline/grill_unity_import_smoke.json`
- `verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json`
- `verification_reports/unity_grill_baseline/unitypackage_probe/grill_unity_import_smoke.json`
- `verification_reports/unreal_grill_baseline/grill_unreal_linux_build_proof.json`
- `verification_reports/unreal_grill_baseline/grill_mapping_export_report.json`
- `verification_reports/unreal_grill_baseline/grill_mapping_materialize_report.json`

Current local Unreal source evidence:

- the public GRILL Unreal `.uplugin` pins `EngineVersion` to `4.27.0`
- the runtime and editor modules whitelist only `Win64`
- `DISRuntime.Build.cs` links `OpenDIS6.lib` from
  `Source/ThirdParty/Binaries/Win64`
- the checked-in third-party binary payload under `Source/ThirdParty/Binaries`
  is `Win64` only
- a live Unreal `5.8` mapping export attempt on this Mac host exits with
  `missing-game-module` after Unreal skips the public GRILL plugins as
  engine-version incompatible and reports unloadable example assets
- a live Unreal `5.8` FastDIS mapping-materialization attempt against the same
  GRILL-shaped temp project hits the same `missing-game-module` boundary

Current local Linux portability evidence:

- the local GRILL Unreal portability branch now packages a Linux plugin payload
  from macOS via Docker against Linux Unreal Engine `5.7.4`
- the resulting packaged plugin includes Linux editor/runtime shared objects
  and a Linux `libOpenDIS6.a`
- that proof is recorded as packaging evidence, not runtime benchmark evidence

Implication:

- the pinned public GRILL Unreal source route still does not provide a direct
  same-host benchmark lane on this Mac host
- but the local portability work has now proven a reproducible Linux package
  build route, which is useful installability evidence and a candidate
  upstream PR lane

## Benchmark Program Consequences

Use this route for benchmark planning:

1. Prefer GRILL source repositories and example projects over assuming prebuilt
   plugin drops for current-engine targets.
2. Run `python tools/prepare_grill_source_route.py` as part of checkout or
   rebuild prep so the public-route repos are fetched, switched to the pinned
   benchmark branches, and submodules refreshed where required.
3. Treat Unity and Unreal example repos as likely benchmark-host setup routes,
   not just documentation extras.
4. Pin GRILL comparisons to specific repo commits, engine versions, and install
   methods.
5. Publish install failure evidence when GRILL cannot import or build on the
   same host and engine family used by FastDIS.

## Workaround And Messaging Guidance

Use the current GRILL route evidence in two distinct ways.

Testing workaround:

- for publishable competitor numbers, move the GRILL lane to a
  GRILL-compatible host rather than privately patching GRILL first
- for internal research, a local GRILL port is acceptable, but it does not
  count as GRILL's public product surface

Messaging angle:

- FastDIS can use the current public-route gap as an installability and
  verification differentiator
- claims must stay route-scoped, for example:
  "the current public GRILL Unreal source route is Windows-only"
- avoid broader unsupported claims such as:
  "GRILL does not support Mac"

## Immediate Next Steps

- capture `grill_unreal` on a Windows host if direct Unreal competitor numbers
  are required
- capture `grill_unity` on a GRILL-compatible Unity host/editor combination if
  direct Unity competitor numbers are required
- keep publishing source-route failure artifacts on the current Mac host so
  claim boundaries stay explicit
