# Unity Host Handoff

Unity host proof is staged under `artifacts/verification_reports/unity_hosts/` and then
reconciled into `artifacts/reports/` for the optional cross-host report set.

If the proof host will not clone the full repo, prepare a self-contained
handoff archive on the source machine first:

```bash
fastdis engine unity export-host-handoff
```

That writes `dist/unity_host_handoff/fastdis-unity-host-handoff-<version>.zip`
with the Unity package, proof scripts, and a bundle-local README for the
external host operator.

## One-Command Host Capture

On a Windows, Linux, or macOS Unity host that can run the local Unity proof
lane:

```bash
fastdis engine unity startup-probe --unity-version 6000.5
fastdis engine unity capture-host-report --unity-version 6000.5
```

Run `startup-probe` first when you are qualifying a new proof host. It is a
faster gate than install smoke and only asks Unity to create/import a minimal
scratch project. If that probe reports that `Library/` was never created, stop
there and fix the Unity/OS host before trusting any later install-smoke result.

That command can:

- run `fastdis engine unity full`
- stage a reusable Unity host bundle under `artifacts/verification_reports/unity_hosts/`
- export a portable archive under `dist/unity_host_reports/`

Before trusting a failed host receipt as a package problem, inspect
`unity_install_smoke_<host>.json`:

- `failure_stage=host-startup` or `failure_reason=project-import-never-started`
  means Unity never began importing the scratch project on that host.
- `failure_stage=package-install` means Unity started but did not show the git
  package in `Library/PackageCache`.
- `failure_stage=runtime-proof` means the package loaded far enough to attempt
  the replay/UDP/native smoke checks and one of those checks failed.

Useful overrides:

```bash
fastdis engine unity capture-host-report \
  --host-label windows-lab-a \
  --host-platform windows \
  --dest-root build/host_reports/unity_hosts \
  --archive-out-dir build/host_reports/unity_archives \
  --unity-version 6000.5
```

If a Windows or Linux proof host is only validating already-staged Unity native
plug-ins and does not have a local FastDIS native build toolchain available,
forward:

```bash
fastdis engine unity capture-host-report \
  --host-platform windows \
  --unity-version 6000.5 \
  --skip-native-build
```

That runs `fastdis engine unity full --skip-native-build`, which reuses the
package's staged plug-ins instead of compiling a host native library first.

## Import One Host Bundle

On the aggregation checkout:

```bash
fastdis engine unity import-host-report dist/unity_host_reports/windows-lab-a.zip
```

That import:

- copies the bundle into `artifacts/verification_reports/unity_hosts/`
- adopts `unity_install_smoke_<host>.json/.md` into `artifacts/reports/`
- refreshes `unity_install_matrix.json/.md`
- refreshes `unity_workflow_report.json/.md`
- refreshes `unity_signoff_report.json/.md`

## Sync All Staged Hosts

If multiple host bundles are already staged under
`artifacts/verification_reports/unity_hosts/`, reconcile them in one step:

```bash
fastdis engine unity sync-host-reports
```

This command rejects duplicate staged bundles for the same platform.
It also refreshes the install matrix, workflow report, and signoff report in
`artifacts/reports/`.

## Staged Host Matrix

To audit the staged host bundles directly, without first reconciling them into
`artifacts/reports/`, run:

```bash
fastdis engine unity host-matrix
```

For host what-if checks or junior troubleshooting, the route discovery tool can
pretend to be a different host class without changing the real machine:

```bash
python tools/host_capability_matrix.py --format summary --host-platform-override linux
python tools/host_capability_matrix.py --format summary --host-system-override Windows --host-machine-override x86_64
```

When staging a Unity host bundle, the same identity override fields are
available if the host label or hostname needs to be normalized for Docker,
remote capture, or lab machines:

```bash
fastdis engine unity stage-host-report --overwrite \
  --host-label lab-win-a \
  --hostname lab-win-a \
  --host-system Windows \
  --host-release 11 \
  --host-machine x86_64 \
  --host-fingerprint-seed unity-lab-a
```

The repo sanitization guard rejects tracked files under `artifacts/` and the
other generated-output roots. Raw Unity receipts stay local; only exported host
bundles should move between hosts.

Run it directly with:

```bash
python tools/check_repo_sanitization.py
```

That writes:

- `artifacts/reports/unity_host_matrix.json`
- `artifacts/reports/unity_host_matrix.md`

The host matrix reports:

- which platforms have staged host bundles
- whether each staged host bundle has passing workflow/runtime/orientation/install status
- whether duplicate host identities, duplicate payloads, or duplicate platforms
  would make a staged host bundle dishonest for cross-host signoff

## Final Unity Signoff Report

To summarize the full Unity Phase 1 exit criteria in one artifact:

```bash
fastdis engine unity signoff
```

That writes:

- `artifacts/reports/unity_signoff_report.json`
- `artifacts/reports/unity_signoff_report.md`

The signoff report combines:

- the local Unity workflow report
- the adopted install matrix in `artifacts/reports/`
- the staged host matrix under `artifacts/verification_reports/unity_hosts/`

## Final Signoff

For the Mac proof lane, the honest completion criteria are:

1. `unity_install_smoke_macos.json` exists and passes.
2. `unity_workflow_report.json` reports the local runtime/orientation/install
   lane as pass.
3. `unity_signoff_report.json` reports `Git/UPM install works on macOS` as
   complete.

The optional cross-host reports remain useful for later portability work, but
they no longer block the macOS proof lane.

If `unity_install_smoke_macos.json` reports `stage=host-startup`, use the
`stage=` / `reason=` fields before deciding whether the host needs Unity/OS
repair or whether the package install lane itself regressed.
