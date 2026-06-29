# Cross-Platform Evidence Rerun Runbook

This is the operator runbook for rerunning the FastDIS benchmark, proof, and
competitor evidence stack.

Use it when:

- bringing up a new Mac, Windows, or Linux host
- refreshing evidence after code changes
- capturing Unity, Unreal, Godot, or GRILL comparison artifacts

## First Rule

Preview the plan before you run anything:

```bash
python tools/refresh_engine_benchmark_artifacts.py --list-steps
```

If the step list looks wrong for the current host, stop and fix the
environment first.

## Main Commands

Preview only:

```bash
python tools/refresh_engine_benchmark_artifacts.py --list-steps
```

Core-only host:

```bash
python tools/refresh_engine_benchmark_artifacts.py --core-only
```

Full host:

```bash
python tools/refresh_engine_benchmark_artifacts.py
```

## Which Command To Use

### macOS host with Godot, Unity, and Unreal

Use:

```bash
python tools/refresh_engine_benchmark_artifacts.py --list-steps
python tools/refresh_engine_benchmark_artifacts.py
```

### Windows host with Unity and Unreal

Use:

```bash
python tools/refresh_engine_benchmark_artifacts.py --list-steps
python tools/refresh_engine_benchmark_artifacts.py
```

This is the preferred host for publishable GRILL Unreal same-host evidence if
the public GRILL Unreal route stays blocked on Mac/Linux.

### Linux host with core lanes and optionally Unreal/Godot

If only core lanes are installed:

```bash
python tools/refresh_engine_benchmark_artifacts.py --list-steps
python tools/refresh_engine_benchmark_artifacts.py --core-only
```

Only use the full refresh if the engine lanes are actually installed on that
Linux machine.

## GRILL-Only Commands

Normalize a GRILL raw capture into the shared report contract:

Unity:

```bash
python tools/normalize_grill_harness_capture.py \
  --input verification_reports/unity_grill_baseline/grill_unity_benchmark_baseline.json
```

Unreal:

```bash
python tools/unreal_workflow.py linux-package \
  --engine-path .build/linux_unreal_engine/ue5.7.4-linux
python tools/unreal_workflow.py linux-proof
python tools/unreal_workflow.py linux-verify --dry-run
python tools/unreal_workflow.py linux-demo --dry-run
python tools/unreal_workflow.py linux-verify --docker \
  --engine-path .build/linux_unreal_engine/ue5.7.4-linux
python tools/unreal_workflow.py linux-demo --docker \
  --engine-path .build/linux_unreal_engine/ue5.7.4-linux
python tools/unreal_workflow.py host-lane-matrix
python tools/unreal_workflow.py grill-linux-proof
python tools/normalize_grill_harness_capture.py \
  --input verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json
```

Cold-start alternative if the Linux engine only exists as a zip:

```bash
python tools/unreal_workflow.py linux-package \
  --engine-archive /path/to/Linux_Unreal_Engine_5.7.4.zip
python tools/unreal_workflow.py linux-proof
python tools/unreal_workflow.py grill-linux-proof
python tools/normalize_grill_harness_capture.py \
  --input verification_reports/unreal_grill_baseline/grill_unreal_benchmark_baseline.json
```

The FastDIS Linux proof command captures current native payload readiness and
upgrades to packaged proof if a real Linux Unreal package directory is present.

The `linux-verify` and `linux-demo` commands are the typed live-harness lanes
for a real Linux Unreal host. On macOS or Windows they emit bounded blocked or
dry-run evidence; on Linux they delegate to the real Unreal orientation and
replay/demo harness runners.

With `--docker`, those same lanes execute inside the Linux Docker route using
the staged Unreal engine payload. This is the preferred capture path on macOS
when you want Linux harness evidence instead of a dry-run planning artifact.

The Linux proof command captures the pinned Docker BuildPlugin result from the
GRILL repo into FastDIS verification reports. It proves packaging/installability,
not runtime benchmark throughput.

Build only the same-host GRILL comparison:

Unity:

```bash
python tools/run_unity_grill_benchmark.py --if-available
```

Unreal:

```bash
python tools/run_unreal_grill_benchmark.py --if-available
```

## First Files To Check After A Run

- `build/reports/engine_benchmarks/`
- `build/reports/benchmark_matrix/benchmark_matrix.json`
- `build/reports/benchmark_claim_summary/benchmark_claim_summary.json`
- `build/reports/benchmark_completion_audit/benchmark_completion_audit.json`
- `build/reports/competitor_lane_summary/competitor_lane_summary.json`

If GRILL is in scope, also check:

- `build/reports/engine_head_to_head/unity_vs_grill.json`
- `build/reports/engine_head_to_head/unreal_vs_grill.json`
- `build/reports/competitor_capture_validation.json`

## How To Interpret Failures

### The refresh script exits nonzero

That means at least one step failed.

The script still continues so it can write blocked evidence and claim-boundary
reports. Check:

- the first failing command in the console output
- the final exit code
- the generated status and matrix reports

### A GRILL lane is `blocked_on_competitor`

That means the public competitor route did not become runnable on that host.

Do not invent numbers. Instead read:

- `build/reports/engine_head_to_head/*_status.json`
- `build/reports/competitor_lane_summary/competitor_lane_summary.json`

### A report exists but timing fields are sparse

That usually means the route is a proof/verification bridge, not a full
throughput capture for every scenario.

Check the claim boundaries in:

- `build/reports/benchmark_matrix/benchmark_matrix.json`
- `build/reports/benchmark_claim_summary/benchmark_claim_summary.json`

## Junior Operator Checklist

1. Run `--list-steps`.
2. Confirm the host actually has the tools the list assumes.
3. Run the refresh command.
4. Check the final exit code.
5. Open `benchmark_claim_summary.json`.
6. Open `competitor_lane_summary.json` if Unity/Unreal GRILL is in scope.
7. If a lane is blocked, keep the blocked artifact and do not fabricate results.

## Raw GRILL Capture Rule

New GRILL harness/addon routes should emit:

- `fastdis.grill_harness_capture.v1`

Reference:

- `docs/research/GRILL_HARNESS_CAPTURE_STANDARD.md`
