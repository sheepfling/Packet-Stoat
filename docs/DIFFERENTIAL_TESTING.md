# Differential Testing

Alpha 3 uses Open-DIS Python as an independent implementation oracle where that
comparison is practical.

This is not a claim that Open-DIS is the authoritative DIS standard. The
authoritative source remains the IEEE DIS specifications. Open-DIS is used here
to catch disagreements between two independent implementations.

## Current scope

The current differential report covers:

- DIS7 catalog overlap against `opendis.PduFactory.PduTypeDecoders`
- header interpretation on the raw Open-DIS test fixtures
- Entity State fixed-prefix fields on the Open-DIS `EntityStatePdu` fixture

It does not yet claim full semantic body equivalence across every PDU. That is
deliberately narrower than "full DIS support."

## Run the report

Clone the reference implementation somewhere local, then point the report tool
at it:

```bash
git clone https://github.com/open-dis/open-dis-python.git build/work/open-dis-python

python tools/run_differential_report.py \
  --open-dis-root build/work/open-dis-python \
  --lib build/libfastdis.dylib \
  --out generated/differential_report.json \
  --md-out generated/differential_report.md
```

On Linux/Windows, point `--lib` at `libfastdis.so` or `fastdis.dll`.

## Output

- `generated/differential_report.json`
- `generated/differential_report.md`

The JSON report is the machine-readable artifact for Alpha 3 audit work. It
records:

- oracle checkout path and git revision, when available
- catalog overlap and name mismatches
- fixture-level header match/mismatch status
- Entity State field comparisons where fastdis has typed support

## Known divergences to expect

The current Open-DIS Python comparison is useful, but it is not perfect. At the
reference revision used during Alpha 3 work, the report shows a few catalog
differences that should be treated as comparison data, not automatic fastdis
bugs:

- PDU type `6` maps to `ResupplyOfferPdu` in the fastdis catalog but
  `CollisionElasticPdu` in Open-DIS Python.
- PDU type `23` differs only by naming:
  `ElectronicEmissionsPdu` vs `ElectromagneticEmissionsPdu`.
- Open-DIS Python exposes some decoder entries that do not line up one-for-one
  with the generated fastdis DIS7 catalog numbering, and vice versa.

## Known limitations

- Open-DIS Python is DIS7-oriented and does not expose the full fastdis DIS6/7
  catalog surface.
- Header agreement on a fixture is stronger evidence than catalog overlap, but
  still narrower than full semantic equivalence.
- Only Entity State currently has typed field-level differential comparison in
  this report because it is the fastdis typed fast path.
