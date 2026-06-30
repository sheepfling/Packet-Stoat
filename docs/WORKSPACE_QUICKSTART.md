# Workspace Quickstart

Start here on any host.

FastDIS can light up different routes depending on:

- your host platform
- what engines are installed
- what toolchains are installed
- which routes are intentionally supported on that host

The fastest honest preview is:

```bash
fastdis workspace doctor
```

For CI logs or a quick onboarding screenshot, use the compact summary:

```bash
fastdis workspace doctor --format summary
```

For automation or machine-readable handoff:

```bash
fastdis workspace routes --format json
```

For manifest-driven CI planning:

```bash
fastdis workspace ci --host-class windows --include-compat --format summary
fastdis workspace ci-print --section workspace_ci_declared_engine --format summary
fastdis workspace ci-sync
fastdis workspace ci-check
python tools/generate_workspace_ci_matrix.py check --path .github/workflows/generated/workspace-ci-matrix.json
```

What this tells you:

- which routes are `ready-now`
- which routes are `ready-after-install`
- which routes are `ready-after-setup`
- which routes are unsupported on the current host
- what command to run next for each route
- which CI rows should exist for a given host/version policy

Common examples:

```bash
fastdis workspace doctor
fastdis engine godot doctor
fastdis engine unity doctor --unity-version 6000.5
fastdis engine unreal doctor --engine-version 5.8
python tools/windows_wheel_workflow.py doctor
```

On the current Windows flow, the typical pattern is:

- Godot native on Windows
- Unity native on Windows
- Unreal native on Windows
- Linux cross-build routes from Windows when Zig or Docker is available
- Windows wheel setup via the MinGW/CMake path

Use `fastdis bootstrap doctor` after `workspace doctor` when you specifically
want the host-smart Godot and Unreal bootstrap preview.
