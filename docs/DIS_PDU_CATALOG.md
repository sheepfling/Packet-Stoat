# DIS PDU Catalog

Generated from Open-DIS `dis-description` XML files. This catalog lists known DIS 6 and DIS 7 PDU classes and marks whether fastdis currently implements a body decoder.

A known catalog entry does not imply full body parsing. The current typed fast path covers Entity State, Entity State Update, the first simulation-management lifecycle and reliable tranche, the first Warfare event tranche, the first collision tranche, and the first Protocol Family 0 plus Entity Management tranche while exposing metadata for the broader DIS message surface.

| DIS | PDU type | Family | Class | Body decoder |
|---:|---:|---|---|---|
| 6 | 0 | Protocol Family 0 | `OtherPdu` | yes |
| 6 | 1 | Entity Information | `EntityStatePdu` | yes |
| 6 | 2 | Warfare | `FirePdu` | yes |
| 6 | 3 | Warfare | `DetonationPdu` | yes |
| 6 | 4 | Entity Information | `CollisionPdu` | yes |
| 6 | 5 | Logistics | `ServiceRequestPdu` | yes |
| 6 | 6 | Logistics | `ResupplyOfferPdu` | yes |
| 6 | 7 | Logistics | `ResupplyReceivedPdu` | yes |
| 6 | 8 | Logistics | `ResupplyCancelPdu` | yes |
| 6 | 9 | Logistics | `RepairCompletePdu` | yes |
| 6 | 10 | Logistics | `RepairResponsePdu` | yes |
| 6 | 11 | Simulation Management | `CreateEntityPdu` | yes |
| 6 | 12 | Simulation Management | `RemoveEntityPdu` | yes |
| 6 | 13 | Simulation Management | `StartResumePdu` | yes |
| 6 | 14 | Simulation Management | `StopFreezePdu` | yes |
| 6 | 15 | Simulation Management | `AcknowledgePdu` | yes |
| 6 | 16 | Simulation Management | `ActionRequestPdu` | yes |
| 6 | 17 | Simulation Management | `ActionResponsePdu` | yes |
| 6 | 18 | Simulation Management | `DataQueryPdu` | yes |
| 6 | 19 | Simulation Management | `SetDataPdu` | yes |
| 6 | 20 | Simulation Management | `DataPdu` | yes |
| 6 | 21 | Simulation Management | `EventReportPdu` | yes |
| 6 | 22 | Simulation Management | `CommentPdu` | yes |
| 6 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes |
| 6 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes |
| 6 | 25 | Radio Communications | `TransmitterPdu` | yes |
| 6 | 26 | Radio Communications | `SignalPdu` | yes |
| 6 | 27 | Radio Communications | `ReceiverPdu` | yes |
| 6 | 28 | Distributed Emission Regeneration | `IffAtcNavAidsLayer1Pdu` | yes |
| 6 | 29 | Distributed Emission Regeneration | `UaPdu` | yes |
| 6 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes |
| 6 | 31 | Radio Communications | `IntercomSignalPdu` | yes |
| 6 | 32 | Radio Communications | `IntercomControlPdu` | yes |
| 6 | 33 | Entity Management | `AggregateStatePdu` | yes |
| 6 | 34 | Entity Management | `IsGroupOfPdu` | yes |
| 6 | 35 | Entity Management | `TransferControlRequestPdu` | yes |
| 6 | 36 | Entity Management | `IsPartOfPdu` | yes |
| 6 | 37 | Minefield | `MinefieldStatePdu` | yes |
| 6 | 38 | Minefield | `MinefieldQueryPdu` | yes |
| 6 | 39 | Minefield | `MinefieldDataPdu` | yes |
| 6 | 40 | Minefield | `MinefieldResponseNackPdu` | yes |
| 6 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes |
| 6 | 42 | Synthetic Environment | `GriddedDataPdu` | yes |
| 6 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes |
| 6 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes |
| 6 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes |
| 6 | 46 | Live Entity | `TSPIPdu` | yes |
| 6 | 47 | Live Entity | `AppearancePdu` | yes |
| 6 | 48 | Live Entity | `ArticulatedPartsPdu` | yes |
| 6 | 49 | Live Entity | `LEFirePdu` | yes |
| 6 | 50 | Live Entity | `LEDetonationPdu` | yes |
| 6 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes |
| 6 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes |
| 6 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes |
| 6 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes |
| 6 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes |
| 6 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes |
| 6 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes |
| 6 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes |
| 6 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes |
| 6 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes |
| 6 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes |
| 6 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes |
| 6 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | yes |
| 6 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes |
| 6 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes |
| 6 | 66 | Entity Information | `CollisionElasticPdu` | yes |
| 6 | 67 | Entity Information | `EntityStateUpdatePdu` | yes |
| 7 | 0 | Protocol Family 0 | `OtherPdu` | yes |
| 7 | 1 | Entity Information | `EntityStatePdu` | yes |
| 7 | 2 | Warfare | `FirePdu` | yes |
| 7 | 3 | Warfare | `DetonationPdu` | yes |
| 7 | 4 | Entity Information | `CollisionPdu` | yes |
| 7 | 5 | Logistics | `ServiceRequestPdu` | yes |
| 7 | 6 | Logistics | `ResupplyOfferPdu` | yes |
| 7 | 7 | Logistics | `ResupplyReceivedPdu` | yes |
| 7 | 8 | Logistics | `ResupplyCancelPdu` | yes |
| 7 | 9 | Logistics | `RepairCompletePdu` | yes |
| 7 | 10 | Logistics | `RepairResponsePdu` | yes |
| 7 | 11 | Simulation Management | `CreateEntityPdu` | yes |
| 7 | 12 | Simulation Management | `RemoveEntityPdu` | yes |
| 7 | 13 | Simulation Management | `StartResumePdu` | yes |
| 7 | 14 | Simulation Management | `StopFreezePdu` | yes |
| 7 | 15 | Simulation Management | `AcknowledgePdu` | yes |
| 7 | 16 | Simulation Management | `ActionRequestPdu` | yes |
| 7 | 17 | Simulation Management | `ActionResponsePdu` | yes |
| 7 | 18 | Simulation Management | `DataQueryPdu` | yes |
| 7 | 19 | Simulation Management | `SetDataPdu` | yes |
| 7 | 20 | Simulation Management | `DataPdu` | yes |
| 7 | 21 | Simulation Management | `EventReportPdu` | yes |
| 7 | 22 | Simulation Management | `CommentPdu` | yes |
| 7 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes |
| 7 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes |
| 7 | 25 | Radio Communications | `TransmitterPdu` | yes |
| 7 | 26 | Radio Communications | `SignalPdu` | yes |
| 7 | 27 | Radio Communications | `ReceiverPdu` | yes |
| 7 | 28 | Distributed Emission Regeneration | `IffPdu` | yes |
| 7 | 29 | Distributed Emission Regeneration | `UaPdu` | yes |
| 7 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes |
| 7 | 31 | Radio Communications | `IntercomSignalPdu` | yes |
| 7 | 32 | Radio Communications | `IntercomControlPdu` | yes |
| 7 | 33 | Entity Management | `AggregateStatePdu` | yes |
| 7 | 34 | Entity Management | `IsGroupOfPdu` | yes |
| 7 | 35 | Entity Management | `TransferOwnershipPdu` | yes |
| 7 | 36 | Entity Management | `IsPartOfPdu` | yes |
| 7 | 37 | Minefield | `MinefieldStatePdu` | yes |
| 7 | 38 | Minefield | `MinefieldQueryPdu` | yes |
| 7 | 39 | Minefield | `MinefieldDataPdu` | yes |
| 7 | 40 | Minefield | `MinefieldResponseNackPdu` | yes |
| 7 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes |
| 7 | 42 | Synthetic Environment | `GriddedDataPdu` | yes |
| 7 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes |
| 7 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes |
| 7 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes |
| 7 | 46 | Live Entity | `TSPIPdu` | yes |
| 7 | 47 | Live Entity | `AppearancePdu` | yes |
| 7 | 48 | Live Entity | `ArticulatedPartsPdu` | yes |
| 7 | 49 | Live Entity | `LEFirePdu` | yes |
| 7 | 50 | Live Entity | `LEDetonationPdu` | yes |
| 7 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes |
| 7 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes |
| 7 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes |
| 7 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes |
| 7 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes |
| 7 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes |
| 7 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes |
| 7 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes |
| 7 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes |
| 7 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes |
| 7 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes |
| 7 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes |
| 7 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | yes |
| 7 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes |
| 7 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes |
| 7 | 66 | Entity Information | `CollisionElasticPdu` | yes |
| 7 | 67 | Entity Information | `EntityStateUpdatePdu` | yes |
| 7 | 68 | Warfare | `DirectedEnergyFirePdu` | yes |
| 7 | 69 | Warfare | `EntityDamageStatusPdu` | yes |
| 7 | 70 | Information Operations | `InformationOperationsActionPdu` | yes |
| 7 | 71 | Information Operations | `InformationOperationsReportPdu` | yes |
| 7 | 72 | Entity Information | `AttributePdu` | yes |
