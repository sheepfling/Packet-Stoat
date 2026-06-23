# DIS PDU Catalog

Generated from Open-DIS `dis-description` XML files. This catalog lists known DIS 6 and DIS 7 PDU classes and marks whether fastdis currently implements a body decoder.

A known catalog entry does not imply full body parsing. Alpha 2 intentionally keeps Entity State as the implemented fast path while exposing metadata for the broader DIS message surface.

| DIS | PDU type | Family | Class | Body decoder |
|---:|---:|---|---|---|
| 6 | 1 | Entity Information | `EntityStatePdu` | yes |
| 6 | 2 | Warfare | `FirePdu` | no |
| 6 | 3 | Warfare | `DetonationPdu` | no |
| 6 | 4 | Entity Information | `CollisionPdu` | no |
| 6 | 5 | Logistics | `ServiceRequestPdu` | no |
| 6 | 6 | Logistics | `ResupplyOfferPdu` | no |
| 6 | 7 | Logistics | `ResupplyReceivedPdu` | no |
| 6 | 8 | Logistics | `ResupplyCancelPdu` | no |
| 6 | 9 | Logistics | `RepairCompletePdu` | no |
| 6 | 10 | Logistics | `RepairResponsePdu` | no |
| 6 | 11 | Simulation Management | `CreateEntityPdu` | no |
| 6 | 12 | Simulation Management | `RemoveEntityPdu` | no |
| 6 | 13 | Simulation Management | `StartResumePdu` | no |
| 6 | 14 | Simulation Management | `StopFreezePdu` | no |
| 6 | 15 | Simulation Management | `AcknowledgePdu` | no |
| 6 | 16 | Simulation Management | `ActionRequestPdu` | no |
| 6 | 17 | Simulation Management | `ActionResponsePdu` | no |
| 6 | 18 | Simulation Management | `DataQueryPdu` | no |
| 6 | 19 | Simulation Management | `SetDataPdu` | no |
| 6 | 20 | Simulation Management | `DataPdu` | no |
| 6 | 21 | Simulation Management | `EventReportPdu` | no |
| 6 | 22 | Simulation Management | `CommentPdu` | no |
| 6 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | no |
| 6 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | no |
| 6 | 25 | Radio Communications | `TransmitterPdu` | no |
| 6 | 26 | Radio Communications | `SignalPdu` | no |
| 6 | 27 | Radio Communications | `ReceiverPdu` | no |
| 6 | 28 | Distributed Emission Regeneration | `IffAtcNavAidsLayer1Pdu` | no |
| 6 | 29 | Distributed Emission Regeneration | `UaPdu` | no |
| 6 | 30 | Distributed Emission Regeneration | `SeesPdu` | no |
| 6 | 31 | Radio Communications | `IntercomSignalPdu` | no |
| 6 | 32 | Radio Communications | `IntercomControlPdu` | no |
| 6 | 33 | Entity Management | `AggregateStatePdu` | no |
| 6 | 34 | Entity Management | `IsGroupOfPdu` | no |
| 6 | 35 | Entity Management | `TransferControlRequestPdu` | no |
| 6 | 36 | Entity Management | `IsPartOfPdu` | no |
| 6 | 37 | Minefield | `MinefieldStatePdu` | no |
| 6 | 38 | Minefield | `MinefieldQueryPdu` | no |
| 6 | 39 | Minefield | `MinefieldDataPdu` | no |
| 6 | 40 | Minefield | `MinefieldResponseNackPdu` | no |
| 6 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | no |
| 6 | 42 | Synthetic Environment | `GriddedDataPdu` | no |
| 6 | 43 | Synthetic Environment | `PointObjectStatePdu` | no |
| 6 | 44 | Synthetic Environment | `LinearObjectStatePdu` | no |
| 6 | 45 | Synthetic Environment | `ArealObjectStatePdu` | no |
| 6 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | no |
| 6 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | no |
| 6 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | no |
| 6 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | no |
| 6 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | no |
| 6 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | no |
| 6 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | no |
| 6 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | no |
| 6 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | no |
| 6 | 60 | Simulation Management with Reliability | `DataReliablePdu` | no |
| 6 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | no |
| 6 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | no |
| 6 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | no |
| 6 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | no |
| 6 | 66 | Entity Information | `CollisionElasticPdu` | no |
| 6 | 67 | Entity Information | `EntityStateUpdatePdu` | yes |
| 7 | 1 | Entity Information | `EntityStatePdu` | yes |
| 7 | 2 | Warfare | `FirePdu` | no |
| 7 | 3 | Warfare | `DetonationPdu` | no |
| 7 | 4 | Entity Information | `CollisionPdu` | no |
| 7 | 5 | Logistics | `ServiceRequestPdu` | no |
| 7 | 6 | Logistics | `ResupplyOfferPdu` | no |
| 7 | 7 | Logistics | `ResupplyReceivedPdu` | no |
| 7 | 9 | Logistics | `RepairCompletePdu` | no |
| 7 | 10 | Logistics | `RepairResponsePdu` | no |
| 7 | 11 | Simulation Management | `CreateEntityPdu` | no |
| 7 | 12 | Simulation Management | `RemoveEntityPdu` | no |
| 7 | 13 | Simulation Management | `StartResumePdu` | no |
| 7 | 14 | Simulation Management | `StopFreezePdu` | no |
| 7 | 15 | Simulation Management | `AcknowledgePdu` | no |
| 7 | 16 | Simulation Management | `ActionRequestPdu` | no |
| 7 | 17 | Simulation Management | `ActionResponsePdu` | no |
| 7 | 18 | Simulation Management | `DataQueryPdu` | no |
| 7 | 19 | Simulation Management | `SetDataPdu` | no |
| 7 | 20 | Simulation Management | `DataPdu` | no |
| 7 | 21 | Simulation Management | `EventReportPdu` | no |
| 7 | 22 | Simulation Management | `CommentPdu` | no |
| 7 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | no |
| 7 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | no |
| 7 | 25 | Radio Communications | `TransmitterPdu` | no |
| 7 | 26 | Radio Communications | `SignalPdu` | no |
| 7 | 27 | Radio Communications | `ReceiverPdu` | no |
| 7 | 29 | Distributed Emission Regeneration | `UaPdu` | no |
| 7 | 30 | Distributed Emission Regeneration | `SeesPdu` | no |
| 7 | 31 | Radio Communications | `IntercomSignalPdu` | no |
| 7 | 32 | Radio Communications | `IntercomControlPdu` | no |
| 7 | 36 | Entity Management | `IsPartOfPdu` | no |
| 7 | 37 | Minefield | `MinefieldStatePdu` | no |
| 7 | 40 | Minefield | `MinefieldResponseNackPdu` | no |
| 7 | 43 | Synthetic Environment | `PointObjectStatePdu` | no |
| 7 | 44 | Synthetic Environment | `LinearObjectStatePdu` | no |
| 7 | 45 | Synthetic Environment | `ArealObjectStatePdu` | no |
| 7 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | no |
| 7 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | no |
| 7 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | no |
| 7 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | no |
| 7 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | no |
| 7 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | no |
| 7 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | no |
| 7 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | no |
| 7 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | no |
| 7 | 60 | Simulation Management with Reliability | `DataReliablePdu` | no |
| 7 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | no |
| 7 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | no |
| 7 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | no |
| 7 | 66 | Entity Information | `CollisionElasticPdu` | no |
| 7 | 67 | Entity Information | `EntityStateUpdatePdu` | yes |
| 7 | 68 | Warfare | `DirectedEnergyFirePdu` | no |
| 7 | 69 | Warfare | `EntityDamageStatusPdu` | no |
