# Semantic PDU Coverage

FastDIS generates semantic parser entry points for every standard DIS 6/7 PDU row.

## Summary

- Semantic parser entry points: `141 / 141`
- Semantic observation parsers: `139 / 141`
- Semantic prefix parsers: `2 / 141`
- Fully domain-decoded semantic parsers: `2 / 141`

A semantic observation is a real parser entry point with a named slotted class, header identity, raw body preservation, declared-field metadata where available, and diagnostics that say full domain decoding is not implemented yet. This avoids silent overclaiming while still giving every PDU a typed semantic surface.

| DIS | PDU | Name | Semantic class | Level | Fully decoded |
| ---: | ---: | --- | --- | --- | --- |
| 6 | 0 | Other | `Dis6OtherSemanticPdu` | `semantic_observation` | no |
| 6 | 1 | Entity State | `Dis6EntityStateSemanticPdu` | `semantic_prefix` | yes |
| 6 | 2 | Fire | `Dis6FireSemanticPdu` | `semantic_observation` | no |
| 6 | 3 | Detonation | `Dis6DetonationSemanticPdu` | `semantic_observation` | no |
| 6 | 4 | Collision | `Dis6CollisionSemanticPdu` | `semantic_observation` | no |
| 6 | 5 | Service Request | `Dis6ServiceRequestSemanticPdu` | `semantic_observation` | no |
| 6 | 6 | Resupply Offer | `Dis6ResupplyOfferSemanticPdu` | `semantic_observation` | no |
| 6 | 7 | Resupply Received | `Dis6ResupplyReceivedSemanticPdu` | `semantic_observation` | no |
| 6 | 8 | Resupply Cancel | `Dis6ResupplyCancelSemanticPdu` | `semantic_observation` | no |
| 6 | 9 | Repair Complete | `Dis6RepairCompleteSemanticPdu` | `semantic_observation` | no |
| 6 | 10 | Repair Response | `Dis6RepairResponseSemanticPdu` | `semantic_observation` | no |
| 6 | 11 | Create Entity | `Dis6CreateEntitySemanticPdu` | `semantic_observation` | no |
| 6 | 12 | Remove Entity | `Dis6RemoveEntitySemanticPdu` | `semantic_observation` | no |
| 6 | 13 | Start/Resume | `Dis6StartResumeSemanticPdu` | `semantic_observation` | no |
| 6 | 14 | Stop/Freeze | `Dis6StopFreezeSemanticPdu` | `semantic_observation` | no |
| 6 | 15 | Acknowledge | `Dis6AcknowledgeSemanticPdu` | `semantic_observation` | no |
| 6 | 16 | Action Request | `Dis6ActionRequestSemanticPdu` | `semantic_observation` | no |
| 6 | 17 | Action Response | `Dis6ActionResponseSemanticPdu` | `semantic_observation` | no |
| 6 | 18 | Data Query | `Dis6DataQuerySemanticPdu` | `semantic_observation` | no |
| 6 | 19 | Set Data | `Dis6SetDataSemanticPdu` | `semantic_observation` | no |
| 6 | 20 | Data | `Dis6DataSemanticPdu` | `semantic_observation` | no |
| 6 | 21 | Event Report | `Dis6EventReportSemanticPdu` | `semantic_observation` | no |
| 6 | 22 | Comment | `Dis6CommentSemanticPdu` | `semantic_observation` | no |
| 6 | 23 | Electromagnetic Emission | `Dis6ElectronicEmissionsSemanticPdu` | `semantic_observation` | no |
| 6 | 24 | Designator | `Dis6DesignatorSemanticPdu` | `semantic_observation` | no |
| 6 | 25 | Transmitter | `Dis6TransmitterSemanticPdu` | `semantic_observation` | no |
| 6 | 26 | Signal | `Dis6SignalSemanticPdu` | `semantic_observation` | no |
| 6 | 27 | Receiver | `Dis6ReceiverSemanticPdu` | `semantic_observation` | no |
| 6 | 28 | IFF/ATC/NAVAIDS | `Dis6IffAtcNavAidsLayer1SemanticPdu` | `semantic_observation` | no |
| 6 | 29 | Underwater Acoustic | `Dis6UaSemanticPdu` | `semantic_observation` | no |
| 6 | 30 | Supplemental Emission / Entity State | `Dis6SEESSemanticPdu` | `semantic_observation` | no |
| 6 | 31 | Intercom Signal | `Dis6IntercomSignalSemanticPdu` | `semantic_observation` | no |
| 6 | 32 | Intercom Control | `Dis6IntercomControlSemanticPdu` | `semantic_observation` | no |
| 6 | 33 | Aggregate State | `Dis6AggregateStateSemanticPdu` | `semantic_observation` | no |
| 6 | 34 | IsGroupOf | `Dis6IsGroupOfSemanticPdu` | `semantic_observation` | no |
| 6 | 35 | Transfer Control | `Dis6TransferControlRequestSemanticPdu` | `semantic_observation` | no |
| 6 | 36 | IsPartOf | `Dis6IsPartOfSemanticPdu` | `semantic_observation` | no |
| 6 | 37 | Minefield State | `Dis6MinefieldStateSemanticPdu` | `semantic_observation` | no |
| 6 | 38 | Minefield Query | `Dis6MinefieldQuerySemanticPdu` | `semantic_observation` | no |
| 6 | 39 | Minefield Data | `Dis6MinefieldDataSemanticPdu` | `semantic_observation` | no |
| 6 | 40 | Minefield Response NACK | `Dis6MinefieldResponseNackSemanticPdu` | `semantic_observation` | no |
| 6 | 41 | Environmental Process | `Dis6EnvironmentalProcessSemanticPdu` | `semantic_observation` | no |
| 6 | 42 | Gridded Data | `Dis6GriddedDataSemanticPdu` | `semantic_observation` | no |
| 6 | 43 | Point Object State | `Dis6PointObjectStateSemanticPdu` | `semantic_observation` | no |
| 6 | 44 | Linear Object State | `Dis6LinearObjectStateSemanticPdu` | `semantic_observation` | no |
| 6 | 45 | Areal Object State | `Dis6ArealObjectStateSemanticPdu` | `semantic_observation` | no |
| 6 | 46 | TSPI | `Dis6TSPISemanticPdu` | `semantic_observation` | no |
| 6 | 47 | Appearance | `Dis6AppearanceSemanticPdu` | `semantic_observation` | no |
| 6 | 48 | Articulated Parts | `Dis6ArticulatedPartsSemanticPdu` | `semantic_observation` | no |
| 6 | 49 | LE Fire | `Dis6LEFireSemanticPdu` | `semantic_observation` | no |
| 6 | 50 | LE Detonation | `Dis6LEDetonationSemanticPdu` | `semantic_observation` | no |
| 6 | 51 | Create Entity-R | `Dis6CreateEntityReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 52 | Remove Entity-R | `Dis6RemoveEntityReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 53 | Start/Resume-R | `Dis6StartResumeReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 54 | Stop/Freeze-R | `Dis6StopFreezeReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 55 | Acknowledge-R | `Dis6AcknowledgeReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 56 | Action Request-R | `Dis6ActionRequestReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 57 | Action Response-R | `Dis6ActionResponseReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 58 | Data Query-R | `Dis6DataQueryReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 59 | Set Data-R | `Dis6SetDataReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 60 | Data-R | `Dis6DataReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 61 | Event Report-R | `Dis6EventReportReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 62 | Comment-R | `Dis6CommentReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 63 | Record-R | `Dis6RecordReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 64 | Set Record-R | `Dis6SetRecordReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 65 | Record Query-R | `Dis6RecordQueryReliableSemanticPdu` | `semantic_observation` | no |
| 6 | 66 | Collision-Elastic | `Dis6CollisionElasticSemanticPdu` | `semantic_observation` | no |
| 6 | 67 | Entity State Update | `Dis6EntityStateUpdateSemanticPdu` | `semantic_observation` | no |
| 7 | 0 | Other | `Dis7OtherSemanticPdu` | `semantic_observation` | no |
| 7 | 1 | Entity State | `Dis7EntityStateSemanticPdu` | `semantic_prefix` | yes |
| 7 | 2 | Fire | `Dis7FireSemanticPdu` | `semantic_observation` | no |
| 7 | 3 | Detonation | `Dis7DetonationSemanticPdu` | `semantic_observation` | no |
| 7 | 4 | Collision | `Dis7CollisionSemanticPdu` | `semantic_observation` | no |
| 7 | 5 | Service Request | `Dis7ServiceRequestSemanticPdu` | `semantic_observation` | no |
| 7 | 6 | Resupply Offer | `Dis7ResupplyOfferSemanticPdu` | `semantic_observation` | no |
| 7 | 7 | Resupply Received | `Dis7ResupplyReceivedSemanticPdu` | `semantic_observation` | no |
| 7 | 8 | Resupply Cancel | `Dis7ResupplyCancelSemanticPdu` | `semantic_observation` | no |
| 7 | 9 | Repair Complete | `Dis7RepairCompleteSemanticPdu` | `semantic_observation` | no |
| 7 | 10 | Repair Response | `Dis7RepairResponseSemanticPdu` | `semantic_observation` | no |
| 7 | 11 | Create Entity | `Dis7CreateEntitySemanticPdu` | `semantic_observation` | no |
| 7 | 12 | Remove Entity | `Dis7RemoveEntitySemanticPdu` | `semantic_observation` | no |
| 7 | 13 | Start/Resume | `Dis7StartResumeSemanticPdu` | `semantic_observation` | no |
| 7 | 14 | Stop/Freeze | `Dis7StopFreezeSemanticPdu` | `semantic_observation` | no |
| 7 | 15 | Acknowledge | `Dis7AcknowledgeSemanticPdu` | `semantic_observation` | no |
| 7 | 16 | Action Request | `Dis7ActionRequestSemanticPdu` | `semantic_observation` | no |
| 7 | 17 | Action Response | `Dis7ActionResponseSemanticPdu` | `semantic_observation` | no |
| 7 | 18 | Data Query | `Dis7DataQuerySemanticPdu` | `semantic_observation` | no |
| 7 | 19 | Set Data | `Dis7SetDataSemanticPdu` | `semantic_observation` | no |
| 7 | 20 | Data | `Dis7DataSemanticPdu` | `semantic_observation` | no |
| 7 | 21 | Event Report | `Dis7EventReportSemanticPdu` | `semantic_observation` | no |
| 7 | 22 | Comment | `Dis7CommentSemanticPdu` | `semantic_observation` | no |
| 7 | 23 | Electromagnetic Emission | `Dis7ElectronicEmissionsSemanticPdu` | `semantic_observation` | no |
| 7 | 24 | Designator | `Dis7DesignatorSemanticPdu` | `semantic_observation` | no |
| 7 | 25 | Transmitter | `Dis7TransmitterSemanticPdu` | `semantic_observation` | no |
| 7 | 26 | Signal | `Dis7SignalSemanticPdu` | `semantic_observation` | no |
| 7 | 27 | Receiver | `Dis7ReceiverSemanticPdu` | `semantic_observation` | no |
| 7 | 28 | IFF | `Dis7IffSemanticPdu` | `semantic_observation` | no |
| 7 | 29 | Underwater Acoustic | `Dis7UaSemanticPdu` | `semantic_observation` | no |
| 7 | 30 | Supplemental Emission / Entity State | `Dis7SEESSemanticPdu` | `semantic_observation` | no |
| 7 | 31 | Intercom Signal | `Dis7IntercomSignalSemanticPdu` | `semantic_observation` | no |
| 7 | 32 | Intercom Control | `Dis7IntercomControlSemanticPdu` | `semantic_observation` | no |
| 7 | 33 | Aggregate State | `Dis7AggregateStateSemanticPdu` | `semantic_observation` | no |
| 7 | 34 | IsGroupOf | `Dis7IsGroupOfSemanticPdu` | `semantic_observation` | no |
| 7 | 35 | Transfer Ownership | `Dis7TransferOwnershipSemanticPdu` | `semantic_observation` | no |
| 7 | 36 | IsPartOf | `Dis7IsPartOfSemanticPdu` | `semantic_observation` | no |
| 7 | 37 | Minefield State | `Dis7MinefieldStateSemanticPdu` | `semantic_observation` | no |
| 7 | 38 | Minefield Query | `Dis7MinefieldQuerySemanticPdu` | `semantic_observation` | no |
| 7 | 39 | Minefield Data | `Dis7MinefieldDataSemanticPdu` | `semantic_observation` | no |
| 7 | 40 | Minefield Response NACK | `Dis7MinefieldResponseNackSemanticPdu` | `semantic_observation` | no |
| 7 | 41 | Environmental Process | `Dis7EnvironmentalProcessSemanticPdu` | `semantic_observation` | no |
| 7 | 42 | Gridded Data | `Dis7GriddedDataSemanticPdu` | `semantic_observation` | no |
| 7 | 43 | Point Object State | `Dis7PointObjectStateSemanticPdu` | `semantic_observation` | no |
| 7 | 44 | Linear Object State | `Dis7LinearObjectStateSemanticPdu` | `semantic_observation` | no |
| 7 | 45 | Areal Object State | `Dis7ArealObjectStateSemanticPdu` | `semantic_observation` | no |
| 7 | 46 | TSPI | `Dis7TSPISemanticPdu` | `semantic_observation` | no |
| 7 | 47 | Appearance | `Dis7AppearanceSemanticPdu` | `semantic_observation` | no |
| 7 | 48 | Articulated Parts | `Dis7ArticulatedPartsSemanticPdu` | `semantic_observation` | no |
| 7 | 49 | LE Fire | `Dis7LEFireSemanticPdu` | `semantic_observation` | no |
| 7 | 50 | LE Detonation | `Dis7LEDetonationSemanticPdu` | `semantic_observation` | no |
| 7 | 51 | Create Entity-R | `Dis7CreateEntityReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 52 | Remove Entity-R | `Dis7RemoveEntityReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 53 | Start/Resume-R | `Dis7StartResumeReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 54 | Stop/Freeze-R | `Dis7StopFreezeReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 55 | Acknowledge-R | `Dis7AcknowledgeReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 56 | Action Request-R | `Dis7ActionRequestReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 57 | Action Response-R | `Dis7ActionResponseReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 58 | Data Query-R | `Dis7DataQueryReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 59 | Set Data-R | `Dis7SetDataReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 60 | Data-R | `Dis7DataReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 61 | Event Report-R | `Dis7EventReportReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 62 | Comment-R | `Dis7CommentReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 63 | Record-R | `Dis7RecordReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 64 | Set Record-R | `Dis7SetRecordReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 65 | Record Query-R | `Dis7RecordQueryReliableSemanticPdu` | `semantic_observation` | no |
| 7 | 66 | Collision-Elastic | `Dis7CollisionElasticSemanticPdu` | `semantic_observation` | no |
| 7 | 67 | Entity State Update | `Dis7EntityStateUpdateSemanticPdu` | `semantic_observation` | no |
| 7 | 68 | Directed Energy Fire | `Dis7DirectedEnergyFireSemanticPdu` | `semantic_observation` | no |
| 7 | 69 | Entity Damage Status | `Dis7EntityDamageStatusSemanticPdu` | `semantic_observation` | no |
| 7 | 70 | Information Operations Action | `Dis7InformationOperationsActionSemanticPdu` | `semantic_observation` | no |
| 7 | 71 | Information Operations Report | `Dis7InformationOperationsReportSemanticPdu` | `semantic_observation` | no |
| 7 | 72 | Attribute | `Dis7AttributeSemanticPdu` | `semantic_observation` | no |
