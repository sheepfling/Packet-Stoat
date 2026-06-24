# Release Artifacts

FastDIS should ship as one tag with several installable products. The
repository codename remains `Packet-Stoat`, but release artifacts should use
the public FastDIS naming.

The current Unreal/Fab closeout lane is tracked under `v0.17.0-alpha12`. Some
lower-level helper script names still include historical `alpha5` stems; treat
those as implementation history rather than the public release identity.

Current version example:

```text
v0.17.0-alpha12
```

## Product Matrix

| Product | Publish endpoint | Install path | Current priority |
|---|---|---|---|
| Python package + CLI | TestPyPI, then PyPI | `pip install fastdis` | Must |
| Native C/C++ SDK | GitHub Releases | download SDK archive, use `find_package(fastdis CONFIG REQUIRED)` | Must |
| Unreal plugin | GitHub Releases first; Fab later | unzip into `Project/Plugins/FastDIS` | Must |
| Godot GDExtension | GitHub Releases first; AssetLib later | unzip into project `addons/fastdis` | Must |
| Unity UPM package | Git URL / GitHub Releases first; Asset Store later | add package from git URL | Must |
| Lattice Lab | GitHub Releases + GHCR | `fastdis lattice ...` or container run | Should |
| Docs site | GitHub Pages | browser docs | Should |
| Verification bundle | GitHub Releases | reports, checksums, manifest, SBOM | Must |

## Expected Release Assets

```text
fastdis-v0.17.0-alpha12-source.zip
fastdis-v0.17.0-alpha12-source.tar.gz
fastdis-0.17.0a12-py3-none-any.whl
fastdis-0.17.0a12.tar.gz
fastdis-native-v0.17.0-alpha12-macos-universal.tar.gz
fastdis-native-v0.17.0-alpha12-linux-x86_64.tar.gz
fastdis-native-v0.17.0-alpha12-windows-x86_64.zip
fastdis-unreal-v0.17.0-alpha12-ue5.8-macos.zip
fastdis-unreal-v0.17.0-alpha12-ue5.8-windows.zip
fastdis-godot-v0.17.0-alpha12-godot4-macos.zip
fastdis-godot-v0.17.0-alpha12-godot4-linux.zip
fastdis-godot-v0.17.0-alpha12-godot4-windows.zip
fastdis-unity-upm-v0.17.0-alpha12.zip
fastdis-lattice-lab-v0.17.0-alpha12.zip
fastdis-verification-v0.17.0-alpha12.zip
fastdis-docs-v0.17.0-alpha12.zip
SHA256SUMS
RELEASE_MANIFEST.json
SBOM.spdx.json
```

## Python Product

- PyPI/TestPyPI distribution: `fastdis`
- Import package: `fastdis`
- Primary CLI: `fastdis`
- Compatibility CLI alias: `packet-stoat`
- Fallback distribution name, if `fastdis` is unavailable: `packet-stoat`

Build locally:

```bash
python tools/dev_check.py --package
```

Smoke after install:

```bash
python -m pip install fastdis
fastdis doctor
```

See [Publishing Bootstrap](PUBLISHING_BOOTSTRAP.md) for account setup, PyPI
name checks, and the first-publish smoke procedure.

## Native SDK Product

Target archive layout:

```text
fastdis-native/
  include/fastdis/fastdis.h
  include/fastdis/fastdis.hpp
  include/fastdis/fastdis_frames.hpp
  lib/
  lib/cmake/fastdis/
  bin/
  README_NATIVE.md
  LICENSE
```

Consumer target:

```cmake
find_package(fastdis CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE fastdis::fastdis)
```

Build locally:

```bash
python tools/dev_check.py --native
```

## Unreal Product

The Unreal deliverable is an installable plugin zip, not the repository.

Target install location:

```text
Project/Plugins/FastDIS/
```

Local verification:

```bash
fastdis engine unreal doctor --engine-version 5.8
fastdis engine unreal build --engine-version 5.8
fastdis engine unreal verify --engine-version 5.8
```

The current Unreal/Fab lane should publish GitHub Release assets first and only
prepare Fab draft materials.

Fab draft readiness:

```bash
python tools/check_unreal_fab_readiness.py
```

Use `--strict` only when the authored binary demo map, Blueprint widget, and
real screenshot exports are committed.

## Godot Product

The Godot deliverable is an addon/GDExtension zip, not the repository.

Target install location:

```text
addons/fastdis/
```

Local verification:

```bash
fastdis engine godot doctor
fastdis engine godot build
fastdis engine godot verify
```

The current Godot lane should publish GitHub Release assets first and only
prepare AssetLib draft materials.

## Unity Product

The Unity deliverable is still a UPM package preview in the current alpha lane.
It includes package shape checks, staged native plug-in payloads, and a
scratch-project Unity Test Framework runtime verification command. Asset Store
submission remains later release work.

Alpha install target:

```text
https://github.com/sheepfling/Packet-Stoat.git?path=integrations/unity/com.sheepfling.fastdis
```

Current package path:

```text
integrations/unity/com.sheepfling.fastdis/
```

Unity runtime verification:

```bash
fastdis engine unity runtime-verify --unity-version 6000.5
```

The default macOS verifier launches a normal Editor executeMethod run through a
login shell so Unity Hub login state is visible. If the local Unity Editor is not
activated, or if a Unity Personal install is forced into `-batchmode` /
`-nographics`, the command reports `blocked_license` and writes
`build/reports/unity_runtime_verification.json` with `diagnostic_code` and
`remediation` fields. That state is acceptable as a host credential/license
blocker, but not as a runtime-pass claim.

Unity is the direct competitor lane against GRILL DIS. Asset Store submission is
later release work after the package loads native libraries in Unity runtime,
replay demos move GameObjects, UDP ingest runs, and orientation verification
reports pass from an activated editor.

## Lattice Lab Product

FastDIS Lattice Lab is mock-first and public-docs-aligned. It is not an
official Anduril integration and should not claim live endpoint verification
without real credentials.

Local package output:

```text
integrations/lattice/dist/packet_stoat_lattice-*.whl
integrations/lattice/dist/packet_stoat_lattice-*.tar.gz
```

Local checks:

```bash
python -m build integrations/lattice
fastdis lattice sdk-check
```

Planned container target:

```text
ghcr.io/sheepfling/fastdis-lattice-lab:0.17.0-alpha12
```

## Verification Bundle

The verification bundle should collect:

- deliverables report
- dev-check report
- benchmark summaries, when run
- Unreal/Godot verification reports, when run
- orientation reports, when run
- Lattice SDK gap report
- checksums and release manifest

Local inspection:

```bash
python tools/list_deliverables.py
```

## Release Rules

- Built artifacts, wheels, zips, reports, checksums, and SBOMs are release
  outputs and should not be committed.
- The root source tree must remain buildable without Unreal, Godot, Anduril
  SDKs, Docker, or a Lattice endpoint.
- Release notes must state what was built, skipped, or deferred.
- Live Lattice claims require explicit credential-gated verification.
