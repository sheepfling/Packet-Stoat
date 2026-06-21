# Engine Marketplace Research

FastDIS should use GitHub Releases as the first alpha distribution endpoint for
engine packages. Marketplace submissions should be draft/prep work until clean
install tests pass for each engine package.

## Godot

Godot announced the new Godot Asset Store on 2026-05-22. The announcement says
the older Asset Library will keep running for older engine versions, but should
be considered deprecated and will become read-only in the future.

Reference:

- `https://godotengine.org/article/introducing-the-godot-asset-store/`

Alpha strategy:

- publish GitHub Release addon zips first
- prepare Godot Asset Store / Asset Library draft material
- submit only after the addon zip works from a clean project

## Unity

Unity should start as a UPM Git package and GitHub Release package. Asset Store
submission should wait until the package imports cleanly, the native library is
staged for target platforms, and demos are supportable.

References:

- `https://docs.unity3d.com/Manual/cus-layout.html`
- `https://docs.unity3d.com/Manual/plug-ins-native.html`

Alpha strategy:

- publish UPM Git path first
- publish GitHub Release `.tgz` or zip package next
- prepare Asset Store draft after runnable Unity preview

## Unreal

Unreal should continue using GitHub Release plugin zips first. Fab submission is
later release work after clean project install and verification map behavior are
stable.
