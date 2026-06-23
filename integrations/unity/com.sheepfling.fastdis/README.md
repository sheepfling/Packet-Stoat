# FastDIS for Unity

FastDIS for Unity is a Unity Package Manager package that wraps the native
`libfastdis` C ABI through C# P/Invoke and exposes Unity-friendly scanning,
snapshot, network, replay, and transform helpers.

Install from Git during alpha:

```text
https://github.com/sheepfling/Packet-Stoat.git?path=integrations/unity/com.sheepfling.fastdis
```

Alpha scope:

- desktop native plug-in layout for Windows, macOS, and Linux
- C# wrapper over the stable FastDIS C ABI
- Unity ENU mapping profile: East -> +X, Up -> +Y, North -> +Z
- package doctor and diagnostics window scaffolds
- runtime/editor test scaffolds
- samples for receiver, UDP loopback, orientation verification, and Lattice Lab bridge

The package does not claim Unity Asset Store readiness yet. Git/UPM install and
GitHub Release `.tgz` packages are the first target.

## Native Payload Matrix

From the repository root:

```bash
python tools/build_unity_native_matrix.py doctor
python tools/build_unity_native_matrix.py build --targets macos windows linux --keep-going
```

The matrix uses:

- macOS: host CMake build.
- Windows: MinGW-w64 cross compile.
- Linux: Docker `linux/amd64` build.

Successful staging produces:

- `Runtime/Plugins/macOS/libfastdis.dylib`
- `Runtime/Plugins/Windows/x86_64/fastdis.dll`
- `Runtime/Plugins/Linux/x86_64/libfastdis.so`

These native payloads are generated artifacts and are not committed.

## Package Documents

- [Changelog](CHANGELOG.md)
- [License](LICENSE.md)
- [Third Party Notices](Third%20Party%20Notices.md)
