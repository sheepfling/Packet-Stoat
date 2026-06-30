# Evidence Pack

FastDIS can generate a local evidence pack that turns source-of-truth files into
human-readable charts, tables, traces, and hashes.

The default output is intentionally under `artifacts/verification_reports/`:

```bash
python tools/generate_evidence_pack.py --clean --render-symbols never
python tools/check_evidence_pack.py artifacts/verification_reports/evidence/latest/manifest.json
```

Equivalent CLI wrapper:

```bash
fastdis release evidence-pack --clean --render-symbols never
fastdis release check-evidence artifacts/verification_reports/evidence/latest/manifest.json
```

Use `--render-symbols auto` after installing the proof harness dependencies:

```bash
npm ci --prefix extensions/fastdis-symbols-proof --cache build/npm-cache
python tools/generate_evidence_pack.py --clean --render-symbols auto
```

## Generated Outputs

The pack includes:

- `index.md`
- `manifest.json`
- `sha256sums.txt`
- charts for PDU handling, fast path, ABI portability, Entity State symbol field
  sufficiency, symbol handoff, dependency boundary, benchmarks, and snapshot
  handoff
- Markdown tables for PDU handling, ABI surface, and symbol cases
- symbol contact sheet and optional per-case `milsymbol` SVGs
- trace receipts for Entity State to symbol handoff and transform-only negative
  behavior

## Policy

Commit the generator, checker, docs, proof cases, and rules. Do not commit
generated evidence packs or rendered marketplace exports. Release tags may attach
an evidence pack as an external release artifact.
