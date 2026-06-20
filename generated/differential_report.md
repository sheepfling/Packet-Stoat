# fastdis differential report

This report compares fastdis against Open-DIS Python as an independent implementation oracle.
Open-DIS is treated as a practical reference implementation, not as the normative DIS standard.

## Catalog overlap

- fastdis DIS7 catalog entries: `53`
- Open-DIS Python decoder entries: `52`
- overlapping PDU types: `49`
- name mismatches on overlapping types: `2`
- fastdis-only DIS7 entries: `4`
- Open-DIS-only decoder entries: `3`

## Fixture comparisons

- raw fixtures checked: `6`
- header matches: `6`
- Entity State fixtures checked: `1`
- Entity State matches: `1`

- `ElectromagneticEmissionPdu-single-system.raw`: header `PASS`, Entity State `n/a`
- `EntityStatePdu-26.raw`: header `PASS`, Entity State `PASS`
- `SetDataPdu-multi-variable-datums.raw`: header `PASS`, Entity State `n/a`
- `SetDataPdu-vbs-script-cmd.raw`: header `PASS`, Entity State `n/a`
- `SignalPdu.raw`: header `PASS`, Entity State `n/a`
- `TransmitterPdu.raw`: header `PASS`, Entity State `n/a`

