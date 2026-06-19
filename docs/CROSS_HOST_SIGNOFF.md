# Cross-Host Signoff

Alpha 2 is not honestly complete until the engine proof is more than one host's
sample run. The repository now has a concrete route for collecting that
evidence instead of relying on ad hoc copies.

## Staging One Host

On a machine that has already produced the local Alpha 2 reports under
`verification_reports/alpha2_sample/`, run:

```bash
python tools/stage_alpha2_host_report.py --overwrite
```

That writes a normalized host bundle under:

```text
verification_reports/alpha2_hosts/<host-label>/
```

Each staged host bundle includes:

- `unreal_version_matrix.json` / `.md`
- `godot_workflow_report.json` / `.md`
- `orientation_runtime_report.json` / `.md`
- `orientation_visual_report.json` / `.md`
- `unreal_host_compat_report.json` / `.md`
- `alpha2_release_audit_report.json` / `.md`
- `alpha2_signoff_matrix.json` / `.md`
- `host_report_manifest.json` / `.md`

The manifest records which machine produced the report set and preserves the
source report directory and host/platform identity. It also records:

- `host_fingerprint`: a stable identity fingerprint for the machine
- `report_digest_sha256`: a digest of the staged Alpha 2 proof payload

## Aggregating Hosts

Once one or more host bundles exist under `verification_reports/alpha2_hosts/`,
run:

```bash
python tools/run_alpha2_signoff_matrix.py \
  --report-root verification_reports/alpha2_hosts \
  --out-dir verification_reports/alpha2_sample
```

The signoff matrix auto-discovers staged host subdirectories and reports one of
these states:

- `no-host-reports`: no usable staged host bundles were found.
- `host-sample-only`: fewer than the configured minimum host count were found.
- `cross-host-partial`: multiple hosts were staged, but not enough passed the
  Unreal/Godot proof gates.
- `cross-host-ready`: the required number of hosts passed the configured proof
  gates.

The matrix also rejects dishonest duplicates:

- staged bundles with the same `host_fingerprint` do not count as separate
  hosts
- staged bundles with the same `report_digest_sha256` do not count as separate
  proof sets

## Practical Operator Flow

1. Run the local Unreal/Godot workflows on a host.
2. Refresh the local machine-readable proof reports if needed.
3. Stage that host with `python tools/stage_alpha2_host_report.py --overwrite`.
4. Repeat on another machine.
5. Re-run `python tools/run_alpha2_signoff_matrix.py`.
6. Re-run `python tools/package_alpha2.py --write-root-checksums`.

Until step 4 exists with a genuinely different host report set, the honest
state remains `host-sample-only`.
