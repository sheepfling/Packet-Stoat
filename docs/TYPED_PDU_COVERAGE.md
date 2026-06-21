# Typed PDU Parsers

FastDIS generates slotted Python typed PDU envelope classes for every standard DIS 6/7 PDU row.

## Summary

- Typed envelope classes: `141 / 141`
- Typed structural parsers: `114 / 141`
- Typed semantic parsers: `2 / 141`
- Byte-preserving serializers: `141 / 141`

Typed envelope coverage means every standard PDU dispatches to a named class with header fields, raw body bytes, and byte-preserving serialization. Typed structural coverage means XML/IR-backed declared fields are exposed as a generated field mapping. Typed semantic coverage remains wave-based.

| DIS | PDU | Name | Parser class | Level | Declared fields |
| ---: | ---: | --- | --- | --- | ---: |
| 6 | 0 | Other | `Dis6OtherPdu` | `typed_envelope` | 0 |
| 6 | 1 | Entity State | `Dis6EntityStatePdu` | `typed_semantic_prefix` | 20 |
| 6 | 2 | Fire | `Dis6FirePdu` | `typed_structural` | 16 |
| 6 | 3 | Detonation | `Dis6DetonationPdu` | `typed_structural` | 19 |
| 6 | 4 | Collision | `Dis6CollisionPdu` | `typed_structural` | 15 |
| 6 | 5 | Service Request | `Dis6ServiceRequestPdu` | `typed_structural` | 13 |
| 6 | 6 | Resupply Offer | `Dis6ResupplyOfferPdu` | `typed_structural` | 13 |
| 6 | 7 | Resupply Received | `Dis6ResupplyReceivedPdu` | `typed_structural` | 13 |
| 6 | 8 | Resupply Cancel | `Dis6ResupplyCancelPdu` | `typed_structural` | 9 |
| 6 | 9 | Repair Complete | `Dis6RepairCompletePdu` | `typed_structural` | 11 |
| 6 | 10 | Repair Response | `Dis6RepairResponsePdu` | `typed_structural` | 12 |
| 6 | 11 | Create Entity | `Dis6CreateEntityPdu` | `typed_structural` | 10 |
| 6 | 12 | Remove Entity | `Dis6RemoveEntityPdu` | `typed_structural` | 10 |
| 6 | 13 | Start/Resume | `Dis6StartResumePdu` | `typed_structural` | 12 |
| 6 | 14 | Stop/Freeze | `Dis6StopFreezePdu` | `typed_structural` | 14 |
| 6 | 15 | Acknowledge | `Dis6AcknowledgePdu` | `typed_structural` | 12 |
| 6 | 16 | Action Request | `Dis6ActionRequestPdu` | `typed_structural` | 15 |
| 6 | 17 | Action Response | `Dis6ActionResponsePdu` | `typed_structural` | 15 |
| 6 | 18 | Data Query | `Dis6DataQueryPdu` | `typed_structural` | 15 |
| 6 | 19 | Set Data | `Dis6SetDataPdu` | `typed_structural` | 15 |
| 6 | 20 | Data | `Dis6DataPdu` | `typed_structural` | 15 |
| 6 | 21 | Event Report | `Dis6EventReportPdu` | `typed_structural` | 15 |
| 6 | 22 | Comment | `Dis6CommentPdu` | `typed_structural` | 13 |
| 6 | 23 | Electromagnetic Emission | `Dis6ElectronicEmissionsPdu` | `typed_structural` | 13 |
| 6 | 24 | Designator | `Dis6DesignatorPdu` | `typed_structural` | 19 |
| 6 | 25 | Transmitter | `Dis6TransmitterPdu` | `typed_structural` | 28 |
| 6 | 26 | Signal | `Dis6SignalPdu` | `typed_structural` | 15 |
| 6 | 27 | Receiver | `Dis6ReceiverPdu` | `typed_structural` | 14 |
| 6 | 28 | IFF/ATC/NAVAIDS | `Dis6IffAtcNavAidsLayer1Pdu` | `typed_structural` | 13 |
| 6 | 29 | Underwater Acoustic | `Dis6UaPdu` | `typed_structural` | 19 |
| 6 | 30 | Supplemental Emission / Entity State | `Dis6SEESPdu` | `typed_structural` | 15 |
| 6 | 31 | Intercom Signal | `Dis6IntercomSignalPdu` | `typed_structural` | 15 |
| 6 | 32 | Intercom Control | `Dis6IntercomControlPdu` | `typed_structural` | 19 |
| 6 | 33 | Aggregate State | `Dis6AggregateStatePdu` | `typed_structural` | 28 |
| 6 | 34 | IsGroupOf | `Dis6IsGroupOfPdu` | `typed_structural` | 14 |
| 6 | 35 | Transfer Control | `Dis6TransferControlRequestPdu` | `typed_structural` | 15 |
| 6 | 36 | IsPartOf | `Dis6IsPartOfPdu` | `typed_structural` | 13 |
| 6 | 37 | Minefield State | `Dis6MinefieldStatePdu` | `typed_structural` | 19 |
| 6 | 38 | Minefield Query | `Dis6MinefieldQueryPdu` | `typed_structural` | 17 |
| 6 | 39 | Minefield Data | `Dis6MinefieldDataPdu` | `typed_structural` | 21 |
| 6 | 40 | Minefield Response NACK | `Dis6MinefieldResponseNackPdu` | `typed_structural` | 12 |
| 6 | 41 | Environmental Process | `Dis6EnvironmentalProcessPdu` | `typed_structural` | 14 |
| 6 | 42 | Gridded Data | `Dis6GriddedDataPdu` | `typed_structural` | 22 |
| 6 | 43 | Point Object State | `Dis6PointObjectStatePdu` | `typed_structural` | 19 |
| 6 | 44 | Linear Object State | `Dis6LinearObjectStatePdu` | `typed_structural` | 16 |
| 6 | 45 | Areal Object State | `Dis6ArealObjectStatePdu` | `typed_structural` | 18 |
| 6 | 46 | TSPI | `Dis6TSPIPdu` | `typed_envelope` | 0 |
| 6 | 47 | Appearance | `Dis6AppearancePdu` | `typed_envelope` | 0 |
| 6 | 48 | Articulated Parts | `Dis6ArticulatedPartsPdu` | `typed_envelope` | 0 |
| 6 | 49 | LE Fire | `Dis6LEFirePdu` | `typed_envelope` | 0 |
| 6 | 50 | LE Detonation | `Dis6LEDetonationPdu` | `typed_envelope` | 0 |
| 6 | 51 | Create Entity-R | `Dis6CreateEntityReliablePdu` | `typed_structural` | 13 |
| 6 | 52 | Remove Entity-R | `Dis6RemoveEntityReliablePdu` | `typed_structural` | 13 |
| 6 | 53 | Start/Resume-R | `Dis6StartResumeReliablePdu` | `typed_structural` | 15 |
| 6 | 54 | Stop/Freeze-R | `Dis6StopFreezeReliablePdu` | `typed_structural` | 15 |
| 6 | 55 | Acknowledge-R | `Dis6AcknowledgeReliablePdu` | `typed_structural` | 12 |
| 6 | 56 | Action Request-R | `Dis6ActionRequestReliablePdu` | `typed_structural` | 18 |
| 6 | 57 | Action Response-R | `Dis6ActionResponseReliablePdu` | `typed_structural` | 15 |
| 6 | 58 | Data Query-R | `Dis6DataQueryReliablePdu` | `typed_structural` | 18 |
| 6 | 59 | Set Data-R | `Dis6SetDataReliablePdu` | `typed_structural` | 17 |
| 6 | 60 | Data-R | `Dis6DataReliablePdu` | `typed_structural` | 17 |
| 6 | 61 | Event Report-R | `Dis6EventReportReliablePdu` | `typed_structural` | 15 |
| 6 | 62 | Comment-R | `Dis6CommentReliablePdu` | `typed_structural` | 13 |
| 6 | 63 | Record-R | `Dis6RecordReliablePdu` | `typed_envelope` | 0 |
| 6 | 64 | Set Record-R | `Dis6SetRecordReliablePdu` | `typed_structural` | 15 |
| 6 | 65 | Record Query-R | `Dis6RecordQueryReliablePdu` | `typed_structural` | 17 |
| 6 | 66 | Collision-Elastic | `Dis6CollisionElasticPdu` | `typed_structural` | 22 |
| 6 | 67 | Entity State Update | `Dis6EntityStateUpdatePdu` | `typed_structural` | 15 |
| 7 | 0 | Other | `Dis7OtherPdu` | `typed_envelope` | 0 |
| 7 | 1 | Entity State | `Dis7EntityStatePdu` | `typed_semantic_prefix` | 21 |
| 7 | 2 | Fire | `Dis7FirePdu` | `typed_structural` | 17 |
| 7 | 3 | Detonation | `Dis7DetonationPdu` | `typed_structural` | 20 |
| 7 | 4 | Collision | `Dis7CollisionPdu` | `typed_structural` | 16 |
| 7 | 5 | Service Request | `Dis7ServiceRequestPdu` | `typed_structural` | 14 |
| 7 | 6 | Resupply Offer | `Dis7ResupplyOfferPdu` | `typed_structural` | 14 |
| 7 | 7 | Resupply Received | `Dis7ResupplyReceivedPdu` | `typed_structural` | 14 |
| 7 | 8 | Resupply Cancel | `Dis7ResupplyCancelPdu` | `typed_envelope` | 0 |
| 7 | 9 | Repair Complete | `Dis7RepairCompletePdu` | `typed_structural` | 12 |
| 7 | 10 | Repair Response | `Dis7RepairResponsePdu` | `typed_structural` | 13 |
| 7 | 11 | Create Entity | `Dis7CreateEntityPdu` | `typed_structural` | 11 |
| 7 | 12 | Remove Entity | `Dis7RemoveEntityPdu` | `typed_structural` | 11 |
| 7 | 13 | Start/Resume | `Dis7StartResumePdu` | `typed_structural` | 13 |
| 7 | 14 | Stop/Freeze | `Dis7StopFreezePdu` | `typed_structural` | 15 |
| 7 | 15 | Acknowledge | `Dis7AcknowledgePdu` | `typed_structural` | 13 |
| 7 | 16 | Action Request | `Dis7ActionRequestPdu` | `typed_structural` | 16 |
| 7 | 17 | Action Response | `Dis7ActionResponsePdu` | `typed_structural` | 16 |
| 7 | 18 | Data Query | `Dis7DataQueryPdu` | `typed_structural` | 16 |
| 7 | 19 | Set Data | `Dis7SetDataPdu` | `typed_structural` | 16 |
| 7 | 20 | Data | `Dis7DataPdu` | `typed_structural` | 16 |
| 7 | 21 | Event Report | `Dis7EventReportPdu` | `typed_structural` | 16 |
| 7 | 22 | Comment | `Dis7CommentPdu` | `typed_structural` | 14 |
| 7 | 23 | Electromagnetic Emission | `Dis7ElectronicEmissionsPdu` | `typed_structural` | 18 |
| 7 | 24 | Designator | `Dis7DesignatorPdu` | `typed_structural` | 20 |
| 7 | 25 | Transmitter | `Dis7TransmitterPdu` | `typed_structural` | 29 |
| 7 | 26 | Signal | `Dis7SignalPdu` | `typed_structural` | 14 |
| 7 | 27 | Receiver | `Dis7ReceiverPdu` | `typed_structural` | 13 |
| 7 | 28 | IFF | `Dis7IffPdu` | `typed_envelope` | 0 |
| 7 | 29 | Underwater Acoustic | `Dis7UaPdu` | `typed_structural` | 20 |
| 7 | 30 | Supplemental Emission / Entity State | `Dis7SEESPdu` | `typed_structural` | 16 |
| 7 | 31 | Intercom Signal | `Dis7IntercomSignalPdu` | `typed_structural` | 16 |
| 7 | 32 | Intercom Control | `Dis7IntercomControlPdu` | `typed_structural` | 20 |
| 7 | 33 | Aggregate State | `Dis7AggregateStatePdu` | `typed_envelope` | 0 |
| 7 | 34 | IsGroupOf | `Dis7IsGroupOfPdu` | `typed_envelope` | 0 |
| 7 | 35 | Transfer Ownership | `Dis7TransferOwnershipPdu` | `typed_envelope` | 0 |
| 7 | 36 | IsPartOf | `Dis7IsPartOfPdu` | `typed_structural` | 14 |
| 7 | 37 | Minefield State | `Dis7MinefieldStatePdu` | `typed_structural` | 20 |
| 7 | 38 | Minefield Query | `Dis7MinefieldQueryPdu` | `typed_envelope` | 0 |
| 7 | 39 | Minefield Data | `Dis7MinefieldDataPdu` | `typed_envelope` | 0 |
| 7 | 40 | Minefield Response NACK | `Dis7MinefieldResponseNackPdu` | `typed_structural` | 13 |
| 7 | 41 | Environmental Process | `Dis7EnvironmentalProcessPdu` | `typed_envelope` | 0 |
| 7 | 42 | Gridded Data | `Dis7GriddedDataPdu` | `typed_envelope` | 0 |
| 7 | 43 | Point Object State | `Dis7PointObjectStatePdu` | `typed_structural` | 20 |
| 7 | 44 | Linear Object State | `Dis7LinearObjectStatePdu` | `typed_structural` | 17 |
| 7 | 45 | Areal Object State | `Dis7ArealObjectStatePdu` | `typed_structural` | 20 |
| 7 | 46 | TSPI | `Dis7TSPIPdu` | `typed_envelope` | 0 |
| 7 | 47 | Appearance | `Dis7AppearancePdu` | `typed_envelope` | 0 |
| 7 | 48 | Articulated Parts | `Dis7ArticulatedPartsPdu` | `typed_envelope` | 0 |
| 7 | 49 | LE Fire | `Dis7LEFirePdu` | `typed_envelope` | 0 |
| 7 | 50 | LE Detonation | `Dis7LEDetonationPdu` | `typed_envelope` | 0 |
| 7 | 51 | Create Entity-R | `Dis7CreateEntityReliablePdu` | `typed_structural` | 14 |
| 7 | 52 | Remove Entity-R | `Dis7RemoveEntityReliablePdu` | `typed_structural` | 14 |
| 7 | 53 | Start/Resume-R | `Dis7StartResumeReliablePdu` | `typed_structural` | 16 |
| 7 | 54 | Stop/Freeze-R | `Dis7StopFreezeReliablePdu` | `typed_structural` | 16 |
| 7 | 55 | Acknowledge-R | `Dis7AcknowledgeReliablePdu` | `typed_structural` | 13 |
| 7 | 56 | Action Request-R | `Dis7ActionRequestReliablePdu` | `typed_structural` | 19 |
| 7 | 57 | Action Response-R | `Dis7ActionResponseReliablePdu` | `typed_structural` | 16 |
| 7 | 58 | Data Query-R | `Dis7DataQueryReliablePdu` | `typed_structural` | 19 |
| 7 | 59 | Set Data-R | `Dis7SetDataReliablePdu` | `typed_structural` | 18 |
| 7 | 60 | Data-R | `Dis7DataReliablePdu` | `typed_structural` | 18 |
| 7 | 61 | Event Report-R | `Dis7EventReportReliablePdu` | `typed_structural` | 16 |
| 7 | 62 | Comment-R | `Dis7CommentReliablePdu` | `typed_structural` | 14 |
| 7 | 63 | Record-R | `Dis7RecordReliablePdu` | `typed_envelope` | 0 |
| 7 | 64 | Set Record-R | `Dis7SetRecordReliablePdu` | `typed_envelope` | 0 |
| 7 | 65 | Record Query-R | `Dis7RecordQueryReliablePdu` | `typed_structural` | 18 |
| 7 | 66 | Collision-Elastic | `Dis7CollisionElasticPdu` | `typed_structural` | 23 |
| 7 | 67 | Entity State Update | `Dis7EntityStateUpdatePdu` | `typed_structural` | 16 |
| 7 | 68 | Directed Energy Fire | `Dis7DirectedEnergyFirePdu` | `typed_structural` | 26 |
| 7 | 69 | Entity Damage Status | `Dis7EntityDamageStatusPdu` | `typed_structural` | 15 |
| 7 | 70 | Information Operations Action | `Dis7InformationOperationsActionPdu` | `typed_envelope` | 0 |
| 7 | 71 | Information Operations Report | `Dis7InformationOperationsReportPdu` | `typed_envelope` | 0 |
| 7 | 72 | Attribute | `Dis7AttributePdu` | `typed_envelope` | 0 |
