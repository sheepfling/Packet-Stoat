# Epic 2 Parity Report

This generated report keeps the current cross-engine/Lattice parity claim honest.

## Summary

- records: `141`
- rows with catalog visibility on all tracked surfaces: `141`
- rows with deep/runtime support on all tracked surfaces: `0`
- surface catalog counts: `{"c": 141, "cpp": 141, "godot": 141, "python": 141, "unity": 141, "unreal": 141}`
- surface deep/runtime counts: `{"c": 4, "cpp": 4, "godot": 4, "python": 4, "unity": 0, "unreal": 4}`
- lattice direct rows: `4`
- lattice projected rows: `137`

Current honest state: catalog visibility is broad, but deep/runtime support is still concentrated in Entity State and Entity State Update. Unity currently has generated catalog visibility for all rows and runtime/deep support for none.

## Representative Typed Rows

| DIS | PDU | Name | Catalog surfaces | Deep/runtime surfaces | Lattice bucket | Lattice mode |
| ---: | ---: | --- | --- | --- | --- | --- |
| 6 | 1 | Entity State | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": false, "unreal": true}` | Entity | strict_only |
| 6 | 67 | Entity State Update | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": false, "unreal": true}` | Entity | bidirectional |
| 7 | 1 | Entity State | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": false, "unreal": true}` | Entity | strict_only |
| 7 | 67 | Entity State Update | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": true, "unreal": true}` | `{"c": true, "cpp": true, "godot": true, "python": true, "unity": false, "unreal": true}` | Entity | bidirectional |

## Deep/Runtime Rows

| DIS | PDU | Name | C | C++ | Python | Unreal | Godot | Unity |
| ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 6 | 1 | Entity State | yes | yes | yes | yes | yes | no |
| 6 | 67 | Entity State Update | yes | yes | yes | yes | yes | no |
| 7 | 1 | Entity State | yes | yes | yes | yes | yes | no |
| 7 | 67 | Entity State Update | yes | yes | yes | yes | yes | no |

