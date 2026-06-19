# Cross-Host Signoff

For the packaged macOS Alpha 2 scope, one verified host report is enough to
reach a truthful `host-ready` state. The same tooling can also enforce stricter
cross-host signoff by raising the minimum host count instead of relying on ad
hoc copies.

## One-Command Host Capture

The preferred operator entry point is now:

```bash
python tools/capture_alpha2_host_signoff.py
```

That wrapper runs the local Alpha 2 proof generators, stages the host bundle,
refreshes the aggregate signoff/audit reports, and then refreshes the source
bundle checksums/package. Use the lower-level commands below only when you need
to skip lanes or debug a specific step.

For stricter cross-host aggregation, add `--min-host-count 2` or higher.

## Moving a Host Bundle Between Machines

On the source machine, export one staged host bundle as a zip:

```bash
python tools/export_alpha2_host_report.py <host-label>
```

That writes:

- `dist/alpha2_host_reports/<host-label>.zip`
- `dist/alpha2_host_reports/<host-label>.zip.sha256`

On the destination machine or in the main repo checkout, import that archive:

```bash
python tools/import_alpha2_host_report.py dist/alpha2_host_reports/<host-label>.zip
```

If the `.sha256` sidecar is present next to the archive, import verifies it
before the bundle is accepted.

After import, refresh the aggregate readouts:

```bash
python tools/run_alpha2_signoff_matrix.py --out-dir verification_reports/alpha2_sample
python tools/run_alpha2_release_audit.py --out-dir verification_reports/alpha2_sample
python tools/package_alpha2.py --write-root-checksums
```

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
- `host-ready`: at least one unique staged host bundle satisfied the configured
  proof gates, and the configured minimum host count is `1`.
- `host-partial`: at least one host bundle was present, but none satisfied the
  configured proof gates while the configured minimum host count is `1`.
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
4. Export that host bundle with `python tools/export_alpha2_host_report.py <host-label>`.
5. Import it into the main repo with `python tools/import_alpha2_host_report.py <archive.zip>`.
6. Re-run `python tools/run_alpha2_signoff_matrix.py`.
7. Re-run `python tools/package_alpha2.py --write-root-checksums`.

With the default packaged macOS setting, one passing host report produces
`host-ready`. If you raise the minimum host count to `2` or more, the honest
state remains `host-sample-only` until a genuinely different host report set is
imported.
