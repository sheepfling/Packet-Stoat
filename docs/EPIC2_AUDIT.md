# Epic 2 Audit

Use the Epic 2 audit report to see what is actually proven today across the
five Epic 2 requirement surfaces:

- 141-row generated truth
- generic wire and field coverage
- typed semantic waves
- cross-engine and Lattice/Zorn parity
- evidence and release gates

For the generated row-by-row parity view that backs the cross-engine criterion,
see [Epic 2 parity](EPIC2_PARITY.md).
For the generated milestone blurbs and current milestone status rollup, see
[Epic 2 milestones](EPIC2_MILESTONES.md).

Generate the current report locally:

```bash
python tools/run_epic2_audit.py
```

Equivalent CLI wrapper:

```bash
fastdis release epic2-audit
```

Outputs:

- `artifacts/reports/epic2/epic2_audit_report.json`
- `artifacts/reports/epic2/epic2_audit_report.md`

Use strict mode only when you want the command to fail unless every criterion is
fully complete:

```bash
python tools/run_epic2_audit.py --strict
```

Current expectation: the audit should report `complete` for the generated
coverage lanes and `partial` where cross-engine/runtime parity or full
release-gate receipts are still weaker than the parser/manifests proof.
