# Standards Update Readiness

FastDIS does not treat DIS 6 and DIS 7 as a permanently closed universe.
Protocol layouts, enumerations, companion standards, and implementation
references are tracked separately.

## Source Layers

- Protocol layouts: IEEE 1278.1 family rows tracked through `standards/registry.yaml` and `generated/pdu_coverage_manifest.json`.
- Enumerations: SISO-REF-010 is tracked through `generated/enum_coverage_manifest.json`; full living-data import remains a future lane.
- Companion standards: C-DIS is tracked as planned companion support, not as DIS 8.
- Implementation references: OpenDIS enum/schema/source-generator references are treated as generation inputs, not as the sole source of truth.

## Update Commands

Refresh standards status:

```bash
python tools/generate_standards_status.py
```

Check generated standards artifacts:

```bash
python tools/generate_standards_status.py --check
python tools/check_generated_fresh.py
```

Operator CLI:

```bash
fastdis standards check
fastdis standards refresh
```

## Runtime Compatibility Policy

- Known DIS 6/7 PDU: parse, log, route, or emit a documented generic event.
- Known version with unknown PDU type: emit generic event and preserve raw payload when the caller selected a raw-preserving path.
- Unknown protocol version: emit a header/raw observation rather than guessing semantics.
- Known PDU with unknown enum value: preserve the numeric value and display `Unknown(value)`.
- Known PDU with extra trailing bytes: preserve raw trailing bytes and emit a diagnostic.
- Known PDU shorter than required: reject as malformed.

## Pre-Release Checklist

- Re-run `python tools/dev_check.py --release-ready --allow-credential-blockers`.
- Confirm `docs/STANDARDS_STATUS.md` says `overall_status: update_ready`.
- Confirm `generated/pdu_coverage_manifest.json` contains `source_metadata`.
- Confirm `generated/enum_coverage_manifest.json` names the pinned SISO-REF-010 reference.
- Review watch entries for P1278.1, SISO-REF-010 latest, C-DIS, and OpenDIS references.

## Future Work

- Add an importer for SISO-REF-010 EBV/XML data files.
- Add standards diff reports for new/deprecated enum values.
- Add protocol-layout import snapshots for future P1278.1 drafts when publicly available.
- Add C-DIS decode/encode support as a companion-standard adapter, not as a replacement for DIS 7.
