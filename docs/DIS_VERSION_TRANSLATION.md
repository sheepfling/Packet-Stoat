# DIS Version Translation

FastDIS cross-version translation is built around a canonical internal model:

```text
DIS 6 packet -> versioned parser -> canonical FastDIS IR -> DIS 7 emitter
DIS 7 packet -> versioned parser -> canonical FastDIS IR -> DIS 6 emitter
```

The rule is explicit: every cataloged PDU gets a translation rule, not every rule is lossless, and no unsupported PDU is silently guessed.

This document is generated from the checked-in DIS XML catalogs. The current XML inputs produce 67 DIS 6 rows and 72 DIS 7 rows. If an OpenDIS enum value is not present in those XML catalogs, it is tracked as an upstream catalog gap rather than invented by hand.

## Status Enum

- `EXACT`
- `RENAMED`
- `DEFAULTED`
- `DROPPED_FIELD`
- `DROPPED_PDU`
- `PASSTHROUGH_RAW`
- `SYNTHETIC`
- `FAILED_STRICT`

## Policies

- `strict`: Allow exact, renamed, and documented safe defaults. Refuse target-incompatible loss.
- `tolerant`: Allow documented defaults and drops with structured diagnostics.
- `preserve_raw`: Tolerant behavior plus retain original packet bytes in sidecar metadata.
- `bridge`: Emit target DIS when possible and report every drop/failure for network bridge use.
- `engine`: Normalize to canonical engine events; untranslatable PDUs become monitor events.
- `lattice_lab`: Normalize to Lattice Lab entities/events/observations while preserving raw context.

## Summary

- DIS 6 catalog rows: `67`
- DIS 7 catalog rows: `72`
- Translation rows: `139`
- DIS 6-only catalog PDU types: `[]`
- DIS 7-only catalog PDU types: `[68, 69, 70, 71, 72]`

## Behavior

- `strict` mode refuses target-incompatible loss and reports `FAILED_STRICT` for PDU-level drops.
- `tolerant` mode emits target packets/events when a documented default/drop is allowed.
- `preserve_raw` mode keeps the original bytes in sidecar metadata when target DIS cannot represent the source exactly.
- Engine endpoints receive canonical events or explicit monitor events; known PDUs do not disappear.
- Lattice Lab maps Entity State to entities and unsupported traffic to `SimulationPduObservation` style events.

## Catalog Gaps

| PDU | DIS 6 name | DIS 7 name | Expected status | Note |
|---:|---|---|---|---|
| 28 | IFF/ATC/NAVAIDS | IFF | `RENAMED` | OpenDIS DIS7 enum commentary treats this as a DIS6/DIS7 name alias, but the checked-in DIS7 XML description does not catalog this PDU row. |
