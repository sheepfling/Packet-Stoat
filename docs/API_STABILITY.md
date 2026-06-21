# API Stability

fastdis exposes a C ABI for host engines and language bindings. The C ABI is
the compatibility contract; C++ wrappers are header-only convenience code and
must not create a shared-library C++ ABI boundary.

## ABI Policy

The current unpublished line is:

- `FASTDIS_ABI_EPOCH == 0`
- `FASTDIS_ABI_REVISION == 9`
- `FASTDIS_ABI_VERSION == FASTDIS_ABI_REVISION`

`EPOCH == 0` means the native ABI has not been published as a compatibility
promise. `REVISION` may churn during alpha while we are still shaping native
engine/plugin surfaces. Before the first public native SDK or wheel with bundled
native artifacts, reset to:

- `FASTDIS_ABI_EPOCH == 1`
- `FASTDIS_ABI_REVISION == 0`
- `FASTDIS_ABI_VERSION == FASTDIS_ABI_EPOCH`

The current revision exists because the dead-reckoning parity surface appends
metadata to `fastdis_entity_transform_t` and exposes shared extrapolation
helpers so C, C++, Python, and engine bindings can use the same evaluator.

For future ABI changes:

- Add new functions instead of changing existing function signatures.
- Preserve old functions when practical as compatibility shorthands.
- Document migration in `docs/ABI.md` and the relevant release notes.
- Add export-check expectations for the new symbols.
- Add C and C++ tests for both old and new paths.
- While unpublished, bump `FASTDIS_ABI_REVISION` for binding/layout changes.
- After publication, bump the public epoch only for incompatible native ABI changes.

## ABI Checklist

Every C ABI change must satisfy this checklist:

- C structs remain POD.
- No STL types cross the C ABI.
- No C++ exceptions cross the C ABI.
- Ownership is explicit and unambiguous.
- Every `create` has a matching `destroy`.
- Every `acquire` has a matching `release`.
- Every returned borrowed pointer has documented lifetime.
- Functions tolerate null pointers where documented.
- Functions return documented `fastdis_status_t` values on invalid input.
- Packet memory remains caller-owned.
- No function stores packet pointers after the call returns.
- Struct fields are only appended, never reordered or removed.
- Struct appends require an ABI version bump unless the struct is opaque.
- New public symbols are listed by `tools/check_exports.py`.
- C tests cover null input and lifecycle behavior.
- C++ RAII wrappers remain header-only.

## Symbol Verification

Use the export checker against the built shared library:

```bash
python tools/check_exports.py build/libfastdis.dylib
python tools/check_exports.py build/libfastdis.so
python tools/check_exports.py build/Release/fastdis.dll
```

The script derives expected symbols from `include/fastdis/fastdis.h` by default
and reports missing exports. Release builds should archive the generated symbol
list in the chosen verification output directory.

Refresh the export report with:

```bash
python tools/run_export_report.py
```

## Engine Boundary Rules

- Unreal, Godot, Unity, Python `ctypes`, Rust, C#, Go, and plain C consumers
  must bind to the C ABI.
- C++ consumers may include `fastdis.hpp`, but those wrappers compile into the
  consumer and call the C ABI.
- Do not return C++ containers, references, exceptions, RTTI types, or allocator
  ownership across the DLL/shared-object boundary.
- Prefer opaque handles for mutable native state.
