# Epic 2 Parity Report

This generated report keeps the current cross-engine/Lattice parity claim honest.

## Summary

- records: `141`
- rows with catalog visibility on all tracked surfaces: `141`
- rows with deep/runtime support on all tracked surfaces: `12`
- surface catalog counts: `{"c": 141, "cpp": 141, "godot": 141, "python": 141, "unity": 141, "unreal": 141}`
- surface deep/runtime counts: `{"c": 12, "cpp": 12, "godot": 12, "python": 12, "unity": 12, "unreal": 12}`
- lattice direct rows: `4`
- lattice projected rows: `137`

Current honest state: catalog visibility is broad, while deep/runtime support is still partial. The shared-library proof now covers Entity State, Entity State Update, and the first simulation-management lifecycle tranche across the tracked surfaces.

## Representative Typed Rows

| DIS | PDU | Name | Catalog surfaces | Deep/runtime surfaces | Lattice bucket | Lattice mode |
| ---: | ---: | --- | --- | --- | --- | --- |
| 6 | 1 | Entity State | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | Entity | strict_only |
| 6 | 67 | Entity State Update | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | Entity | bidirectional |
| 7 | 1 | Entity State | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | Entity | strict_only |
| 7 | 67 | Entity State Update | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | Entity | bidirectional |

## Deep/Runtime Rows

| DIS | PDU | Name | C | C++ | Python | Unreal | Godot | Unity |
| ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 6 | 1 | Entity State | yes | yes | yes | yes | yes | yes |
| 6 | 11 | Create Entity | yes | yes | yes | yes | yes | yes |
| 6 | 12 | Remove Entity | yes | yes | yes | yes | yes | yes |
| 6 | 13 | Start Resume | yes | yes | yes | yes | yes | yes |
| 6 | 14 | Stop Freeze | yes | yes | yes | yes | yes | yes |
| 6 | 67 | Entity State Update | yes | yes | yes | yes | yes | yes |
| 7 | 1 | Entity State | yes | yes | yes | yes | yes | yes |
| 7 | 11 | Create Entity | yes | yes | yes | yes | yes | yes |
| 7 | 12 | Remove Entity | yes | yes | yes | yes | yes | yes |
| 7 | 13 | Start Resume | yes | yes | yes | yes | yes | yes |
| 7 | 14 | Stop Freeze | yes | yes | yes | yes | yes | yes |
| 7 | 67 | Entity State Update | yes | yes | yes | yes | yes | yes |

