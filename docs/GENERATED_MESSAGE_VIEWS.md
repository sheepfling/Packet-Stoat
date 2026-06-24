# Generated Message Views

FastDIS generates parser, visitor, and serializer views for every cataloged DIS 6/7 PDU.

Current guarantee:

- every known PDU has a generated generic parser
- every known PDU has generated header/body visitor coverage
- every known PDU has a byte-preserving serializer for parsed packet views
- typed semantic body decoders remain tracked separately

This is the broad product coverage layer. The Entity State fast path remains the production typed transform decoder.

| DIS | PDU | Family | Class | Declared fields | Parser | Visitor | Serializer |
|---:|---:|---|---|---:|---|---|---|
| 6 | 1 | Entity Information | `EntityStatePdu` | 20 | generated | generated | byte-preserving |
| 6 | 2 | Warfare | `FirePdu` | 16 | generated | generated | byte-preserving |
| 6 | 3 | Warfare | `DetonationPdu` | 19 | generated | generated | byte-preserving |
| 6 | 4 | Entity Information | `CollisionPdu` | 15 | generated | generated | byte-preserving |
| 6 | 5 | Logistics | `ServiceRequestPdu` | 13 | generated | generated | byte-preserving |
| 6 | 6 | Logistics | `ResupplyOfferPdu` | 13 | generated | generated | byte-preserving |
| 6 | 7 | Logistics | `ResupplyReceivedPdu` | 13 | generated | generated | byte-preserving |
| 6 | 8 | Logistics | `ResupplyCancelPdu` | 9 | generated | generated | byte-preserving |
| 6 | 9 | Logistics | `RepairCompletePdu` | 11 | generated | generated | byte-preserving |
| 6 | 10 | Logistics | `RepairResponsePdu` | 12 | generated | generated | byte-preserving |
| 6 | 11 | Simulation Management | `CreateEntityPdu` | 10 | generated | generated | byte-preserving |
| 6 | 12 | Simulation Management | `RemoveEntityPdu` | 10 | generated | generated | byte-preserving |
| 6 | 13 | Simulation Management | `StartResumePdu` | 12 | generated | generated | byte-preserving |
| 6 | 14 | Simulation Management | `StopFreezePdu` | 14 | generated | generated | byte-preserving |
| 6 | 15 | Simulation Management | `AcknowledgePdu` | 12 | generated | generated | byte-preserving |
| 6 | 16 | Simulation Management | `ActionRequestPdu` | 15 | generated | generated | byte-preserving |
| 6 | 17 | Simulation Management | `ActionResponsePdu` | 15 | generated | generated | byte-preserving |
| 6 | 18 | Simulation Management | `DataQueryPdu` | 15 | generated | generated | byte-preserving |
| 6 | 19 | Simulation Management | `SetDataPdu` | 15 | generated | generated | byte-preserving |
| 6 | 20 | Simulation Management | `DataPdu` | 15 | generated | generated | byte-preserving |
| 6 | 21 | Simulation Management | `EventReportPdu` | 15 | generated | generated | byte-preserving |
| 6 | 22 | Simulation Management | `CommentPdu` | 13 | generated | generated | byte-preserving |
| 6 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | 13 | generated | generated | byte-preserving |
| 6 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | 19 | generated | generated | byte-preserving |
| 6 | 25 | Radio Communications | `TransmitterPdu` | 28 | generated | generated | byte-preserving |
| 6 | 26 | Radio Communications | `SignalPdu` | 15 | generated | generated | byte-preserving |
| 6 | 27 | Radio Communications | `ReceiverPdu` | 14 | generated | generated | byte-preserving |
| 6 | 28 | Distributed Emission Regeneration | `IffAtcNavAidsLayer1Pdu` | 13 | generated | generated | byte-preserving |
| 6 | 29 | Distributed Emission Regeneration | `UaPdu` | 19 | generated | generated | byte-preserving |
| 6 | 30 | Distributed Emission Regeneration | `SeesPdu` | 15 | generated | generated | byte-preserving |
| 6 | 31 | Radio Communications | `IntercomSignalPdu` | 15 | generated | generated | byte-preserving |
| 6 | 32 | Radio Communications | `IntercomControlPdu` | 19 | generated | generated | byte-preserving |
| 6 | 33 | Entity Management | `AggregateStatePdu` | 28 | generated | generated | byte-preserving |
| 6 | 34 | Entity Management | `IsGroupOfPdu` | 14 | generated | generated | byte-preserving |
| 6 | 35 | Entity Management | `TransferControlRequestPdu` | 15 | generated | generated | byte-preserving |
| 6 | 36 | Entity Management | `IsPartOfPdu` | 13 | generated | generated | byte-preserving |
| 6 | 37 | Minefield | `MinefieldStatePdu` | 19 | generated | generated | byte-preserving |
| 6 | 38 | Minefield | `MinefieldQueryPdu` | 17 | generated | generated | byte-preserving |
| 6 | 39 | Minefield | `MinefieldDataPdu` | 21 | generated | generated | byte-preserving |
| 6 | 40 | Minefield | `MinefieldResponseNackPdu` | 12 | generated | generated | byte-preserving |
| 6 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | 14 | generated | generated | byte-preserving |
| 6 | 42 | Synthetic Environment | `GriddedDataPdu` | 22 | generated | generated | byte-preserving |
| 6 | 43 | Synthetic Environment | `PointObjectStatePdu` | 19 | generated | generated | byte-preserving |
| 6 | 44 | Synthetic Environment | `LinearObjectStatePdu` | 16 | generated | generated | byte-preserving |
| 6 | 45 | Synthetic Environment | `ArealObjectStatePdu` | 18 | generated | generated | byte-preserving |
| 6 | 46 | Live Entity | `TSPIPdu` | 11 | generated | generated | byte-preserving |
| 6 | 47 | Live Entity | `AppearancePdu` | 8 | generated | generated | byte-preserving |
| 6 | 48 | Live Entity | `ArticulatedPartsPdu` | 3 | generated | generated | byte-preserving |
| 6 | 49 | Live Entity | `LEFirePdu` | 9 | generated | generated | byte-preserving |
| 6 | 50 | Live Entity | `LEDetonationPdu` | 12 | generated | generated | byte-preserving |
| 6 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | 13 | generated | generated | byte-preserving |
| 6 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | 13 | generated | generated | byte-preserving |
| 6 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | 15 | generated | generated | byte-preserving |
| 6 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | 15 | generated | generated | byte-preserving |
| 6 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | 12 | generated | generated | byte-preserving |
| 6 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | 18 | generated | generated | byte-preserving |
| 6 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | 15 | generated | generated | byte-preserving |
| 6 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | 18 | generated | generated | byte-preserving |
| 6 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | 17 | generated | generated | byte-preserving |
| 6 | 60 | Simulation Management with Reliability | `DataReliablePdu` | 17 | generated | generated | byte-preserving |
| 6 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | 15 | generated | generated | byte-preserving |
| 6 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | 13 | generated | generated | byte-preserving |
| 6 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | 15 | generated | generated | byte-preserving |
| 6 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | 15 | generated | generated | byte-preserving |
| 6 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | 17 | generated | generated | byte-preserving |
| 6 | 66 | Entity Information | `CollisionElasticPdu` | 22 | generated | generated | byte-preserving |
| 6 | 67 | Entity Information | `EntityStateUpdatePdu` | 15 | generated | generated | byte-preserving |
| 7 | 1 | Entity Information | `EntityStatePdu` | 21 | generated | generated | byte-preserving |
| 7 | 2 | Warfare | `FirePdu` | 17 | generated | generated | byte-preserving |
| 7 | 3 | Warfare | `DetonationPdu` | 20 | generated | generated | byte-preserving |
| 7 | 4 | Entity Information | `CollisionPdu` | 16 | generated | generated | byte-preserving |
| 7 | 5 | Logistics | `ServiceRequestPdu` | 14 | generated | generated | byte-preserving |
| 7 | 6 | Logistics | `ResupplyOfferPdu` | 14 | generated | generated | byte-preserving |
| 7 | 7 | Logistics | `ResupplyReceivedPdu` | 14 | generated | generated | byte-preserving |
| 7 | 8 | Logistics | `ResupplyCancelPdu` | 10 | generated | generated | byte-preserving |
| 7 | 9 | Logistics | `RepairCompletePdu` | 12 | generated | generated | byte-preserving |
| 7 | 10 | Logistics | `RepairResponsePdu` | 13 | generated | generated | byte-preserving |
| 7 | 11 | Simulation Management | `CreateEntityPdu` | 11 | generated | generated | byte-preserving |
| 7 | 12 | Simulation Management | `RemoveEntityPdu` | 11 | generated | generated | byte-preserving |
| 7 | 13 | Simulation Management | `StartResumePdu` | 13 | generated | generated | byte-preserving |
| 7 | 14 | Simulation Management | `StopFreezePdu` | 15 | generated | generated | byte-preserving |
| 7 | 15 | Simulation Management | `AcknowledgePdu` | 13 | generated | generated | byte-preserving |
| 7 | 16 | Simulation Management | `ActionRequestPdu` | 16 | generated | generated | byte-preserving |
| 7 | 17 | Simulation Management | `ActionResponsePdu` | 16 | generated | generated | byte-preserving |
| 7 | 18 | Simulation Management | `DataQueryPdu` | 16 | generated | generated | byte-preserving |
| 7 | 19 | Simulation Management | `SetDataPdu` | 16 | generated | generated | byte-preserving |
| 7 | 20 | Simulation Management | `DataPdu` | 16 | generated | generated | byte-preserving |
| 7 | 21 | Simulation Management | `EventReportPdu` | 16 | generated | generated | byte-preserving |
| 7 | 22 | Simulation Management | `CommentPdu` | 14 | generated | generated | byte-preserving |
| 7 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | 18 | generated | generated | byte-preserving |
| 7 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | 20 | generated | generated | byte-preserving |
| 7 | 25 | Radio Communications | `TransmitterPdu` | 29 | generated | generated | byte-preserving |
| 7 | 26 | Radio Communications | `SignalPdu` | 14 | generated | generated | byte-preserving |
| 7 | 27 | Radio Communications | `ReceiverPdu` | 13 | generated | generated | byte-preserving |
| 7 | 28 | Distributed Emission Regeneration | `IffPdu` | 14 | generated | generated | byte-preserving |
| 7 | 29 | Distributed Emission Regeneration | `UaPdu` | 20 | generated | generated | byte-preserving |
| 7 | 30 | Distributed Emission Regeneration | `SeesPdu` | 16 | generated | generated | byte-preserving |
| 7 | 31 | Radio Communications | `IntercomSignalPdu` | 16 | generated | generated | byte-preserving |
| 7 | 32 | Radio Communications | `IntercomControlPdu` | 20 | generated | generated | byte-preserving |
| 7 | 33 | Entity Management | `AggregateStatePdu` | 29 | generated | generated | byte-preserving |
| 7 | 34 | Entity Management | `IsGroupOfPdu` | 15 | generated | generated | byte-preserving |
| 7 | 35 | Entity Management | `TransferOwnershipPdu` | 16 | generated | generated | byte-preserving |
| 7 | 36 | Entity Management | `IsPartOfPdu` | 14 | generated | generated | byte-preserving |
| 7 | 37 | Minefield | `MinefieldStatePdu` | 20 | generated | generated | byte-preserving |
| 7 | 38 | Minefield | `MinefieldQueryPdu` | 18 | generated | generated | byte-preserving |
| 7 | 39 | Minefield | `MinefieldDataPdu` | 22 | generated | generated | byte-preserving |
| 7 | 40 | Minefield | `MinefieldResponseNackPdu` | 13 | generated | generated | byte-preserving |
| 7 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | 15 | generated | generated | byte-preserving |
| 7 | 42 | Synthetic Environment | `GriddedDataPdu` | 23 | generated | generated | byte-preserving |
| 7 | 43 | Synthetic Environment | `PointObjectStatePdu` | 20 | generated | generated | byte-preserving |
| 7 | 44 | Synthetic Environment | `LinearObjectStatePdu` | 17 | generated | generated | byte-preserving |
| 7 | 45 | Synthetic Environment | `ArealObjectStatePdu` | 20 | generated | generated | byte-preserving |
| 7 | 46 | Live Entity | `TSPIPdu` | 11 | generated | generated | byte-preserving |
| 7 | 47 | Live Entity | `AppearancePdu` | 8 | generated | generated | byte-preserving |
| 7 | 48 | Live Entity | `ArticulatedPartsPdu` | 3 | generated | generated | byte-preserving |
| 7 | 49 | Live Entity | `LEFirePdu` | 9 | generated | generated | byte-preserving |
| 7 | 50 | Live Entity | `LEDetonationPdu` | 12 | generated | generated | byte-preserving |
| 7 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | 14 | generated | generated | byte-preserving |
| 7 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | 14 | generated | generated | byte-preserving |
| 7 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | 16 | generated | generated | byte-preserving |
| 7 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | 16 | generated | generated | byte-preserving |
| 7 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | 13 | generated | generated | byte-preserving |
| 7 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | 19 | generated | generated | byte-preserving |
| 7 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | 16 | generated | generated | byte-preserving |
| 7 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | 19 | generated | generated | byte-preserving |
| 7 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | 18 | generated | generated | byte-preserving |
| 7 | 60 | Simulation Management with Reliability | `DataReliablePdu` | 18 | generated | generated | byte-preserving |
| 7 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | 16 | generated | generated | byte-preserving |
| 7 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | 14 | generated | generated | byte-preserving |
| 7 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | 16 | generated | generated | byte-preserving |
| 7 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | 16 | generated | generated | byte-preserving |
| 7 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | 18 | generated | generated | byte-preserving |
| 7 | 66 | Entity Information | `CollisionElasticPdu` | 23 | generated | generated | byte-preserving |
| 7 | 67 | Entity Information | `EntityStateUpdatePdu` | 16 | generated | generated | byte-preserving |
| 7 | 68 | Warfare | `DirectedEnergyFirePdu` | 26 | generated | generated | byte-preserving |
| 7 | 69 | Warfare | `EntityDamageStatusPdu` | 15 | generated | generated | byte-preserving |
| 7 | 70 | Information Operations | `InformationOperationsActionPdu` | 13 | generated | generated | byte-preserving |
| 7 | 71 | Information Operations | `InformationOperationsReportPdu` | 10 | generated | generated | byte-preserving |
| 7 | 72 | Entity Information | `AttributePdu` | 17 | generated | generated | byte-preserving |
