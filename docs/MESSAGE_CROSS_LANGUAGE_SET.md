# Cross-Language DIS Message Set

This is the complete, explicit Alpha 2 message coverage table generated from Open-DIS `DIS6.xml` and `DIS7.xml`.

Definitions:

- `catalog`: the language/surface can identify the PDU type/name/family from generated metadata.
- `body`: the language/surface has a typed fastdis body decoder or adapter path.
- `adapter`: Unreal/Godot engine path can consume and apply that message type without custom user glue.

Honest current state: C, C++, Python, Unreal, Godot, and Unity have catalog visibility for every listed DIS6/DIS7 PDU. Typed body/adapter support now covers Entity State, Entity State Update, Acknowledge, the first simulation-management lifecycle tranche, the first simulation-management reliable tranche, the first Warfare event tranche, the first collision tranche, the first Protocol Family 0 plus Entity Management tranche, and the Synthetic Environment tranche on the currently proven deep/runtime surfaces. Unity catalog visibility still does not imply a runtime adapter for every row.

| DIS | PDU | Family | Class | C catalog | C body | C++ catalog | C++ body | Python catalog | Python body | Unreal catalog | Unreal adapter | Godot catalog | Godot adapter | Unity catalog | Unity adapter |
|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 0 | Protocol Family 0 | `OtherPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 1 | Entity Information | `EntityStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 2 | Warfare | `FirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 3 | Warfare | `DetonationPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 4 | Entity Information | `CollisionPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 5 | Logistics | `ServiceRequestPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 6 | Logistics | `ResupplyOfferPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 7 | Logistics | `ResupplyReceivedPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 8 | Logistics | `ResupplyCancelPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 9 | Logistics | `RepairCompletePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 10 | Logistics | `RepairResponsePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 11 | Simulation Management | `CreateEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 12 | Simulation Management | `RemoveEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 13 | Simulation Management | `StartResumePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 14 | Simulation Management | `StopFreezePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 15 | Simulation Management | `AcknowledgePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 16 | Simulation Management | `ActionRequestPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 17 | Simulation Management | `ActionResponsePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 18 | Simulation Management | `DataQueryPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 19 | Simulation Management | `SetDataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 20 | Simulation Management | `DataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 21 | Simulation Management | `EventReportPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 22 | Simulation Management | `CommentPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 25 | Radio Communications | `TransmitterPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 26 | Radio Communications | `SignalPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 27 | Radio Communications | `ReceiverPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 28 | Distributed Emission Regeneration | `IffAtcNavAidsLayer1Pdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 29 | Distributed Emission Regeneration | `UaPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 31 | Radio Communications | `IntercomSignalPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 32 | Radio Communications | `IntercomControlPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 33 | Entity Management | `AggregateStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 34 | Entity Management | `IsGroupOfPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 35 | Entity Management | `TransferControlRequestPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 36 | Entity Management | `IsPartOfPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 37 | Minefield | `MinefieldStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 38 | Minefield | `MinefieldQueryPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 39 | Minefield | `MinefieldDataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 40 | Minefield | `MinefieldResponseNackPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 42 | Synthetic Environment | `GriddedDataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 46 | Live Entity | `TSPIPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 47 | Live Entity | `AppearancePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 48 | Live Entity | `ArticulatedPartsPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 49 | Live Entity | `LEFirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 50 | Live Entity | `LEDetonationPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 66 | Entity Information | `CollisionElasticPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 6 | 67 | Entity Information | `EntityStateUpdatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 0 | Protocol Family 0 | `OtherPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 1 | Entity Information | `EntityStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 2 | Warfare | `FirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 3 | Warfare | `DetonationPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 4 | Entity Information | `CollisionPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 5 | Logistics | `ServiceRequestPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 6 | Logistics | `ResupplyOfferPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 7 | Logistics | `ResupplyReceivedPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 8 | Logistics | `ResupplyCancelPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 9 | Logistics | `RepairCompletePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 10 | Logistics | `RepairResponsePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 11 | Simulation Management | `CreateEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 12 | Simulation Management | `RemoveEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 13 | Simulation Management | `StartResumePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 14 | Simulation Management | `StopFreezePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 15 | Simulation Management | `AcknowledgePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 16 | Simulation Management | `ActionRequestPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 17 | Simulation Management | `ActionResponsePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 18 | Simulation Management | `DataQueryPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 19 | Simulation Management | `SetDataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 20 | Simulation Management | `DataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 21 | Simulation Management | `EventReportPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 22 | Simulation Management | `CommentPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 25 | Radio Communications | `TransmitterPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 26 | Radio Communications | `SignalPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 27 | Radio Communications | `ReceiverPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 28 | Distributed Emission Regeneration | `IffPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 29 | Distributed Emission Regeneration | `UaPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 31 | Radio Communications | `IntercomSignalPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 32 | Radio Communications | `IntercomControlPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 33 | Entity Management | `AggregateStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 34 | Entity Management | `IsGroupOfPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 35 | Entity Management | `TransferOwnershipPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 36 | Entity Management | `IsPartOfPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 37 | Minefield | `MinefieldStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 38 | Minefield | `MinefieldQueryPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 39 | Minefield | `MinefieldDataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 40 | Minefield | `MinefieldResponseNackPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 42 | Synthetic Environment | `GriddedDataPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 46 | Live Entity | `TSPIPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 47 | Live Entity | `AppearancePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 48 | Live Entity | `ArticulatedPartsPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 49 | Live Entity | `LEFirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 50 | Live Entity | `LEDetonationPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 66 | Entity Information | `CollisionElasticPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 67 | Entity Information | `EntityStateUpdatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 68 | Warfare | `DirectedEnergyFirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 69 | Warfare | `EntityDamageStatusPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 70 | Information Operations | `InformationOperationsActionPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 71 | Information Operations | `InformationOperationsReportPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| 7 | 72 | Entity Information | `AttributePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
