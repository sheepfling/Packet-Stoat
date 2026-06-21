# Godot DIS Scan

## Current Read

Godot is the low-competition engine lane for FastDIS. A quick scan did not find
a clear purpose-built Godot DIS, Open-DIS, or HLA plugin. That is not proof that
none exists, but it is enough to treat Godot as a whitespace opportunity.

Godot's new Asset Store is live, while the old Asset Library remains available
for older engine versions and is expected to become read-only later.

Reference:

- `https://godotengine.org/article/introducing-the-godot-asset-store/`

## Product Positioning

FastDIS for Godot brings high-rate DIS Entity State ingestion to Godot 4 through
a native GDExtension, a simple `FastDisWorld` node, replay/UDP tools, and
verified georeferenced transforms.

## Implementation Route

```text
libfastdis / C ABI
  -> C++ GDExtension wrapper
  -> FastDisWorld node
  -> entity map resources
  -> Node3D snapshot application
```

## Alpha5 / Alpha6 Work

- keep Godot as a first-class product lane in release docs
- preserve the existing doctor/build/verify workflow
- add cleaner install docs for a release addon zip
- keep orientation verification explicit and opt-in
- prepare marketplace draft material only after clean install proof

## Honest Claim

Godot is a likely whitespace lane, but FastDIS should only claim support for the
specific Godot versions and host platforms that the build/verify workflow has
actually exercised.
