# Epic 2 Semantic Waves

This generated worklist assigns every standard DIS 6/7 versioned row to one typed-semantic buildout wave.

## Summary

- Versioned rows classified: `141 / 141`
- Waves: `5`
- Field visitor rows already present: `115 / 141`
- Typed structural rows already present: `115 / 141`
- Semantic prefix rows already present: `4 / 141`
- Fully domain-decoded rows already present: `84 / 141`

The waves are planning buckets, not claims that every row in a wave is already semantically complete.

## Wave Summary

| Wave | Rows | Structural | Prefix | Fully decoded | Goal |
| --- | ---: | ---: | ---: | ---: | --- |
| Wave 1: State And Lifecycle | 19 | 12 | 4 | 12 | Drive entity state, identity, and immediate lifecycle rows first so the hot-path product semantics become deeper before broader protocol families. |
| Wave 2: Warfare And Effects | 14 | 10 | 0 | 10 | Add semantically useful combat, collision, and visible-effect rows that unblock gameplay events and verification scenes. |
| Wave 3: Radio, Sensor, EW, IFF, And Designator | 20 | 20 | 0 | 19 | Deepen sensor, comms, emission, designator, and identification semantics with consistent engine and bridge events. |
| Wave 4: Simulation Management | 46 | 43 | 0 | 43 | Complete typed task/control semantics for simulation-management families, including reliable variants that currently stay generic. |
| Wave 5: Logistics, Environment, Aggregate, And Remaining Rows | 42 | 30 | 0 | 0 | Finish the remaining logistics, environment, aggregate, minefield, attribute, and information-operations families without leaving uncategorized rows behind. |

## Wave 1: State And Lifecycle

Drive entity state, identity, and immediate lifecycle rows first so the hot-path product semantics become deeper before broader protocol families.

| DIS | PDU | Name | Family | Semantic level | Structural | Decoded | Reason |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 6 | 1 | Entity State | Entity Information | `semantic_prefix` | yes | yes | direct state/lifecycle row |
| 6 | 11 | Create Entity | Simulation Management | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 6 | 12 | Remove Entity | Simulation Management | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 6 | 46 | TSPI | Live Entity | `semantic_observation` | no | no | direct state/lifecycle row |
| 6 | 47 | Appearance | Live Entity | `semantic_observation` | no | no | direct state/lifecycle row |
| 6 | 48 | Articulated Parts | Live Entity | `semantic_observation` | no | no | direct state/lifecycle row |
| 6 | 51 | Create Entity-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 6 | 52 | Remove Entity-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 6 | 67 | Entity State Update | Entity Information | `semantic_prefix` | yes | yes | direct state/lifecycle row |
| 7 | 1 | Entity State | Entity Information | `semantic_prefix` | yes | yes | direct state/lifecycle row |
| 7 | 11 | Create Entity | Simulation Management | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 7 | 12 | Remove Entity | Simulation Management | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 7 | 46 | TSPI | Live Entity | `semantic_observation` | no | no | direct state/lifecycle row |
| 7 | 47 | Appearance | Live Entity | `semantic_observation` | no | no | direct state/lifecycle row |
| 7 | 48 | Articulated Parts | Live Entity | `semantic_observation` | no | no | direct state/lifecycle row |
| 7 | 51 | Create Entity-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 7 | 52 | Remove Entity-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | direct state/lifecycle row |
| 7 | 67 | Entity State Update | Entity Information | `semantic_prefix` | yes | yes | direct state/lifecycle row |
| 7 | 72 | Attribute | Entity Information | `semantic_observation` | no | no | direct state/lifecycle row |

## Wave 2: Warfare And Effects

Add semantically useful combat, collision, and visible-effect rows that unblock gameplay events and verification scenes.

| DIS | PDU | Name | Family | Semantic level | Structural | Decoded | Reason |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 6 | 2 | Fire | Warfare | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 6 | 3 | Detonation | Warfare | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 6 | 4 | Collision | Entity Information | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 6 | 49 | LE Fire | Live Entity | `semantic_observation` | no | no | direct warfare/effects row |
| 6 | 50 | LE Detonation | Live Entity | `semantic_observation` | no | no | direct warfare/effects row |
| 6 | 66 | Collision-Elastic | Entity Information | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 7 | 2 | Fire | Warfare | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 7 | 3 | Detonation | Warfare | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 7 | 4 | Collision | Entity Information | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 7 | 49 | LE Fire | Live Entity | `semantic_observation` | no | no | direct warfare/effects row |
| 7 | 50 | LE Detonation | Live Entity | `semantic_observation` | no | no | direct warfare/effects row |
| 7 | 66 | Collision-Elastic | Entity Information | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 7 | 68 | Directed Energy Fire | Warfare | `semantic_decoded` | yes | yes | direct warfare/effects row |
| 7 | 69 | Entity Damage Status | Warfare | `semantic_decoded` | yes | yes | direct warfare/effects row |

## Wave 3: Radio, Sensor, EW, IFF, And Designator

Deepen sensor, comms, emission, designator, and identification semantics with consistent engine and bridge events.

| DIS | PDU | Name | Family | Semantic level | Structural | Decoded | Reason |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 6 | 23 | Electromagnetic Emission | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 6 | 24 | Designator | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 6 | 25 | Transmitter | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 6 | 26 | Signal | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 6 | 27 | Receiver | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 6 | 28 | IFF/ATC/NAVAIDS | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 6 | 29 | Underwater Acoustic | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 6 | 30 | Supplemental Emission / Entity State | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 6 | 31 | Intercom Signal | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 6 | 32 | Intercom Control | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 7 | 23 | Electromagnetic Emission | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 7 | 24 | Designator | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 7 | 25 | Transmitter | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 7 | 26 | Signal | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 7 | 27 | Receiver | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 7 | 28 | IFF | Distributed Emission Regeneration | `semantic_observation` | yes | no | family=Distributed Emission Regeneration |
| 7 | 29 | Underwater Acoustic | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 7 | 30 | Supplemental Emission / Entity State | Distributed Emission Regeneration | `semantic_decoded` | yes | yes | family=Distributed Emission Regeneration |
| 7 | 31 | Intercom Signal | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |
| 7 | 32 | Intercom Control | Radio Communications | `semantic_decoded` | yes | yes | family=Radio Communications |

## Wave 4: Simulation Management

Complete typed task/control semantics for simulation-management families, including reliable variants that currently stay generic.

| DIS | PDU | Name | Family | Semantic level | Structural | Decoded | Reason |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 6 | 13 | Start/Resume | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 14 | Stop/Freeze | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 15 | Acknowledge | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 16 | Action Request | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 17 | Action Response | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 18 | Data Query | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 19 | Set Data | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 20 | Data | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 21 | Event Report | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 22 | Comment | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 6 | 53 | Start/Resume-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 54 | Stop/Freeze-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 55 | Acknowledge-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 56 | Action Request-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 57 | Action Response-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 58 | Data Query-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 59 | Set Data-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 60 | Data-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 61 | Event Report-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 62 | Comment-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 63 | Record-R | Simulation Management with Reliability | `semantic_observation` | no | no | family=Simulation Management with Reliability |
| 6 | 64 | Set Record-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 6 | 65 | Record Query-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 13 | Start/Resume | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 14 | Stop/Freeze | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 15 | Acknowledge | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 16 | Action Request | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 17 | Action Response | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 18 | Data Query | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 19 | Set Data | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 20 | Data | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 21 | Event Report | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 22 | Comment | Simulation Management | `semantic_decoded` | yes | yes | family=Simulation Management |
| 7 | 53 | Start/Resume-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 54 | Stop/Freeze-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 55 | Acknowledge-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 56 | Action Request-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 57 | Action Response-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 58 | Data Query-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 59 | Set Data-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 60 | Data-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 61 | Event Report-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 62 | Comment-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |
| 7 | 63 | Record-R | Simulation Management with Reliability | `semantic_observation` | no | no | family=Simulation Management with Reliability |
| 7 | 64 | Set Record-R | Simulation Management with Reliability | `semantic_observation` | no | no | family=Simulation Management with Reliability |
| 7 | 65 | Record Query-R | Simulation Management with Reliability | `semantic_decoded` | yes | yes | family=Simulation Management with Reliability |

## Wave 5: Logistics, Environment, Aggregate, And Remaining Rows

Finish the remaining logistics, environment, aggregate, minefield, attribute, and information-operations families without leaving uncategorized rows behind.

| DIS | PDU | Name | Family | Semantic level | Structural | Decoded | Reason |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 6 | 0 | Other | Protocol Family 0 | `semantic_observation` | no | no | family=Protocol Family 0 |
| 6 | 5 | Service Request | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 6 | 6 | Resupply Offer | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 6 | 7 | Resupply Received | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 6 | 8 | Resupply Cancel | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 6 | 9 | Repair Complete | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 6 | 10 | Repair Response | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 6 | 33 | Aggregate State | Entity Management | `semantic_observation` | yes | no | family=Entity Management |
| 6 | 34 | IsGroupOf | Entity Management | `semantic_observation` | yes | no | family=Entity Management |
| 6 | 35 | Transfer Control | Entity Management | `semantic_observation` | yes | no | family=Entity Management |
| 6 | 36 | IsPartOf | Entity Management | `semantic_observation` | yes | no | family=Entity Management |
| 6 | 37 | Minefield State | Minefield | `semantic_observation` | yes | no | family=Minefield |
| 6 | 38 | Minefield Query | Minefield | `semantic_observation` | yes | no | family=Minefield |
| 6 | 39 | Minefield Data | Minefield | `semantic_observation` | yes | no | family=Minefield |
| 6 | 40 | Minefield Response NACK | Minefield | `semantic_observation` | yes | no | family=Minefield |
| 6 | 41 | Environmental Process | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 6 | 42 | Gridded Data | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 6 | 43 | Point Object State | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 6 | 44 | Linear Object State | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 6 | 45 | Areal Object State | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 7 | 0 | Other | Protocol Family 0 | `semantic_observation` | no | no | family=Protocol Family 0 |
| 7 | 5 | Service Request | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 7 | 6 | Resupply Offer | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 7 | 7 | Resupply Received | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 7 | 8 | Resupply Cancel | Logistics | `semantic_observation` | no | no | family=Logistics |
| 7 | 9 | Repair Complete | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 7 | 10 | Repair Response | Logistics | `semantic_observation` | yes | no | family=Logistics |
| 7 | 33 | Aggregate State | Entity Management | `semantic_observation` | no | no | family=Entity Management |
| 7 | 34 | IsGroupOf | Entity Management | `semantic_observation` | no | no | family=Entity Management |
| 7 | 35 | Transfer Ownership | Entity Management | `semantic_observation` | no | no | family=Entity Management |
| 7 | 36 | IsPartOf | Entity Management | `semantic_observation` | yes | no | family=Entity Management |
| 7 | 37 | Minefield State | Minefield | `semantic_observation` | yes | no | family=Minefield |
| 7 | 38 | Minefield Query | Minefield | `semantic_observation` | no | no | family=Minefield |
| 7 | 39 | Minefield Data | Minefield | `semantic_observation` | no | no | family=Minefield |
| 7 | 40 | Minefield Response NACK | Minefield | `semantic_observation` | yes | no | family=Minefield |
| 7 | 41 | Environmental Process | Synthetic Environment | `semantic_observation` | no | no | family=Synthetic Environment |
| 7 | 42 | Gridded Data | Synthetic Environment | `semantic_observation` | no | no | family=Synthetic Environment |
| 7 | 43 | Point Object State | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 7 | 44 | Linear Object State | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 7 | 45 | Areal Object State | Synthetic Environment | `semantic_observation` | yes | no | family=Synthetic Environment |
| 7 | 70 | Information Operations Action | Information Operations | `semantic_observation` | no | no | family=Information Operations |
| 7 | 71 | Information Operations Report | Information Operations | `semantic_observation` | no | no | family=Information Operations |
