# Epic 2 Parity Report

This generated report keeps the current cross-engine/Lattice parity claim honest.

## Summary

- records: `141`
- rows with catalog visibility on all tracked surfaces: `141`
- rows with deep/runtime support on all tracked surfaces: `141`
- surface catalog counts: `{"c": 141, "cpp": 141, "godot": 141, "python": 141, "unity": 141, "unreal": 141}`
- surface deep/runtime counts: `{"c": 141, "cpp": 141, "godot": 141, "python": 141, "unity": 141, "unreal": 141}`
- lattice direct rows: `4`
- lattice projected rows: `137`

Current honest state: catalog visibility is broad, while deep/runtime support is still partial. The shared-library proof now covers Entity State, Entity State Update, Acknowledge, the first simulation-management lifecycle tranche, the first simulation-management reliable tranche, the first Warfare event tranche, the first collision tranche, the first Protocol Family 0 plus Entity Management tranche, and the Synthetic Environment tranche across the tracked surfaces.

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
| 6 | 0 | Other | yes | yes | yes | yes | yes | yes |
| 6 | 1 | Entity State | yes | yes | yes | yes | yes | yes |
| 6 | 2 | Fire | yes | yes | yes | yes | yes | yes |
| 6 | 3 | Detonation | yes | yes | yes | yes | yes | yes |
| 6 | 4 | Collision | yes | yes | yes | yes | yes | yes |
| 6 | 5 | Service Request | yes | yes | yes | yes | yes | yes |
| 6 | 6 | Resupply Offer | yes | yes | yes | yes | yes | yes |
| 6 | 7 | Resupply Received | yes | yes | yes | yes | yes | yes |
| 6 | 8 | Resupply Cancel | yes | yes | yes | yes | yes | yes |
| 6 | 9 | Repair Complete | yes | yes | yes | yes | yes | yes |
| 6 | 10 | Repair Response | yes | yes | yes | yes | yes | yes |
| 6 | 11 | Create Entity | yes | yes | yes | yes | yes | yes |
| 6 | 12 | Remove Entity | yes | yes | yes | yes | yes | yes |
| 6 | 13 | Start Resume | yes | yes | yes | yes | yes | yes |
| 6 | 14 | Stop Freeze | yes | yes | yes | yes | yes | yes |
| 6 | 15 | Acknowledge | yes | yes | yes | yes | yes | yes |
| 6 | 16 | Action Request | yes | yes | yes | yes | yes | yes |
| 6 | 17 | Action Response | yes | yes | yes | yes | yes | yes |
| 6 | 18 | Data Query | yes | yes | yes | yes | yes | yes |
| 6 | 19 | Set Data | yes | yes | yes | yes | yes | yes |
| 6 | 20 | Data | yes | yes | yes | yes | yes | yes |
| 6 | 21 | Event Report | yes | yes | yes | yes | yes | yes |
| 6 | 22 | Comment | yes | yes | yes | yes | yes | yes |
| 6 | 23 | Electronic Emissions | yes | yes | yes | yes | yes | yes |
| 6 | 24 | Designator | yes | yes | yes | yes | yes | yes |
| 6 | 25 | Transmitter | yes | yes | yes | yes | yes | yes |
| 6 | 26 | Signal | yes | yes | yes | yes | yes | yes |
| 6 | 27 | Receiver | yes | yes | yes | yes | yes | yes |
| 6 | 28 | Iff Atc Nav Aids Layer1 | yes | yes | yes | yes | yes | yes |
| 6 | 29 | Ua | yes | yes | yes | yes | yes | yes |
| 6 | 30 | Sees | yes | yes | yes | yes | yes | yes |
| 6 | 31 | Intercom Signal | yes | yes | yes | yes | yes | yes |
| 6 | 32 | Intercom Control | yes | yes | yes | yes | yes | yes |
| 6 | 33 | Aggregate State | yes | yes | yes | yes | yes | yes |
| 6 | 34 | Is Group Of | yes | yes | yes | yes | yes | yes |
| 6 | 35 | Transfer Control Request | yes | yes | yes | yes | yes | yes |
| 6 | 36 | Is Part Of | yes | yes | yes | yes | yes | yes |
| 6 | 37 | Minefield State | yes | yes | yes | yes | yes | yes |
| 6 | 38 | Minefield Query | yes | yes | yes | yes | yes | yes |
| 6 | 39 | Minefield Data | yes | yes | yes | yes | yes | yes |
| 6 | 40 | Minefield Response Nack | yes | yes | yes | yes | yes | yes |
| 6 | 41 | Environmental Process | yes | yes | yes | yes | yes | yes |
| 6 | 42 | Gridded Data | yes | yes | yes | yes | yes | yes |
| 6 | 43 | Point Object State | yes | yes | yes | yes | yes | yes |
| 6 | 44 | Linear Object State | yes | yes | yes | yes | yes | yes |
| 6 | 45 | Areal Object State | yes | yes | yes | yes | yes | yes |
| 6 | 46 | T S P I | yes | yes | yes | yes | yes | yes |
| 6 | 47 | Appearance | yes | yes | yes | yes | yes | yes |
| 6 | 48 | Articulated Parts | yes | yes | yes | yes | yes | yes |
| 6 | 49 | L E Fire | yes | yes | yes | yes | yes | yes |
| 6 | 50 | L E Detonation | yes | yes | yes | yes | yes | yes |
| 6 | 51 | Create Entity Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 52 | Remove Entity Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 53 | Start Resume Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 54 | Stop Freeze Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 55 | Acknowledge Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 56 | Action Request Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 57 | Action Response Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 58 | Data Query Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 59 | Set Data Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 60 | Data Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 61 | Event Report Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 62 | Comment Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 63 | Record Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 64 | Set Record Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 65 | Record Query Reliable | yes | yes | yes | yes | yes | yes |
| 6 | 66 | Collision Elastic | yes | yes | yes | yes | yes | yes |
| 6 | 67 | Entity State Update | yes | yes | yes | yes | yes | yes |
| 7 | 0 | Other | yes | yes | yes | yes | yes | yes |
| 7 | 1 | Entity State | yes | yes | yes | yes | yes | yes |
| 7 | 2 | Fire | yes | yes | yes | yes | yes | yes |
| 7 | 3 | Detonation | yes | yes | yes | yes | yes | yes |
| 7 | 4 | Collision | yes | yes | yes | yes | yes | yes |
| 7 | 5 | Service Request | yes | yes | yes | yes | yes | yes |
| 7 | 6 | Resupply Offer | yes | yes | yes | yes | yes | yes |
| 7 | 7 | Resupply Received | yes | yes | yes | yes | yes | yes |
| 7 | 8 | Resupply Cancel | yes | yes | yes | yes | yes | yes |
| 7 | 9 | Repair Complete | yes | yes | yes | yes | yes | yes |
| 7 | 10 | Repair Response | yes | yes | yes | yes | yes | yes |
| 7 | 11 | Create Entity | yes | yes | yes | yes | yes | yes |
| 7 | 12 | Remove Entity | yes | yes | yes | yes | yes | yes |
| 7 | 13 | Start Resume | yes | yes | yes | yes | yes | yes |
| 7 | 14 | Stop Freeze | yes | yes | yes | yes | yes | yes |
| 7 | 15 | Acknowledge | yes | yes | yes | yes | yes | yes |
| 7 | 16 | Action Request | yes | yes | yes | yes | yes | yes |
| 7 | 17 | Action Response | yes | yes | yes | yes | yes | yes |
| 7 | 18 | Data Query | yes | yes | yes | yes | yes | yes |
| 7 | 19 | Set Data | yes | yes | yes | yes | yes | yes |
| 7 | 20 | Data | yes | yes | yes | yes | yes | yes |
| 7 | 21 | Event Report | yes | yes | yes | yes | yes | yes |
| 7 | 22 | Comment | yes | yes | yes | yes | yes | yes |
| 7 | 23 | Electronic Emissions | yes | yes | yes | yes | yes | yes |
| 7 | 24 | Designator | yes | yes | yes | yes | yes | yes |
| 7 | 25 | Transmitter | yes | yes | yes | yes | yes | yes |
| 7 | 26 | Signal | yes | yes | yes | yes | yes | yes |
| 7 | 27 | Receiver | yes | yes | yes | yes | yes | yes |
| 7 | 28 | Iff | yes | yes | yes | yes | yes | yes |
| 7 | 29 | Ua | yes | yes | yes | yes | yes | yes |
| 7 | 30 | Sees | yes | yes | yes | yes | yes | yes |
| 7 | 31 | Intercom Signal | yes | yes | yes | yes | yes | yes |
| 7 | 32 | Intercom Control | yes | yes | yes | yes | yes | yes |
| 7 | 33 | Aggregate State | yes | yes | yes | yes | yes | yes |
| 7 | 34 | Is Group Of | yes | yes | yes | yes | yes | yes |
| 7 | 35 | Transfer Ownership | yes | yes | yes | yes | yes | yes |
| 7 | 36 | Is Part Of | yes | yes | yes | yes | yes | yes |
| 7 | 37 | Minefield State | yes | yes | yes | yes | yes | yes |
| 7 | 38 | Minefield Query | yes | yes | yes | yes | yes | yes |
| 7 | 39 | Minefield Data | yes | yes | yes | yes | yes | yes |
| 7 | 40 | Minefield Response Nack | yes | yes | yes | yes | yes | yes |
| 7 | 41 | Environmental Process | yes | yes | yes | yes | yes | yes |
| 7 | 42 | Gridded Data | yes | yes | yes | yes | yes | yes |
| 7 | 43 | Point Object State | yes | yes | yes | yes | yes | yes |
| 7 | 44 | Linear Object State | yes | yes | yes | yes | yes | yes |
| 7 | 45 | Areal Object State | yes | yes | yes | yes | yes | yes |
| 7 | 46 | T S P I | yes | yes | yes | yes | yes | yes |
| 7 | 47 | Appearance | yes | yes | yes | yes | yes | yes |
| 7 | 48 | Articulated Parts | yes | yes | yes | yes | yes | yes |
| 7 | 49 | L E Fire | yes | yes | yes | yes | yes | yes |
| 7 | 50 | L E Detonation | yes | yes | yes | yes | yes | yes |
| 7 | 51 | Create Entity Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 52 | Remove Entity Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 53 | Start Resume Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 54 | Stop Freeze Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 55 | Acknowledge Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 56 | Action Request Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 57 | Action Response Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 58 | Data Query Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 59 | Set Data Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 60 | Data Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 61 | Event Report Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 62 | Comment Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 63 | Record Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 64 | Set Record Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 65 | Record Query Reliable | yes | yes | yes | yes | yes | yes |
| 7 | 66 | Collision Elastic | yes | yes | yes | yes | yes | yes |
| 7 | 67 | Entity State Update | yes | yes | yes | yes | yes | yes |
| 7 | 68 | Directed Energy Fire | yes | yes | yes | yes | yes | yes |
| 7 | 69 | Entity Damage Status | yes | yes | yes | yes | yes | yes |
| 7 | 70 | Information Operations Action | yes | yes | yes | yes | yes | yes |
| 7 | 71 | Information Operations Report | yes | yes | yes | yes | yes | yes |
| 7 | 72 | Attribute | yes | yes | yes | yes | yes | yes |

