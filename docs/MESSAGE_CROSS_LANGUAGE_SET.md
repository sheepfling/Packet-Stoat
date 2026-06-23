# Cross-Language DIS Message Set

This is the complete, explicit Alpha 2 message coverage table generated from Open-DIS `DIS6.xml` and `DIS7.xml`.

Definitions:

- `catalog`: the language/surface can identify the PDU type/name/family from generated metadata.
- `body`: the language/surface has a typed fastdis body decoder or adapter path.
- `adapter`: Unreal/Godot engine path can consume and apply that message type without custom user glue.

Honest current state: C, C++, Python, Unreal, and Godot have catalog visibility for every listed DIS6/DIS7 PDU. Typed body/adapter support is Entity State only. Unity has no adapter yet.

| DIS | PDU | Family | Class | C catalog | C body | C++ catalog | C++ body | Python catalog | Python body | Unreal catalog | Unreal adapter | Godot catalog | Godot adapter | Unity catalog | Unity adapter |
|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 1 | Entity Information | `EntityStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | no | no |
| 6 | 2 | Warfare | `FirePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 3 | Warfare | `DetonationPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 4 | Entity Information | `CollisionPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 5 | Logistics | `ServiceRequestPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 6 | Logistics | `ResupplyOfferPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 7 | Logistics | `ResupplyReceivedPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 8 | Logistics | `ResupplyCancelPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 9 | Logistics | `RepairCompletePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 10 | Logistics | `RepairResponsePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 11 | Simulation Management | `CreateEntityPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 12 | Simulation Management | `RemoveEntityPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 13 | Simulation Management | `StartResumePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 14 | Simulation Management | `StopFreezePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 15 | Simulation Management | `AcknowledgePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 16 | Simulation Management | `ActionRequestPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 17 | Simulation Management | `ActionResponsePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 18 | Simulation Management | `DataQueryPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 19 | Simulation Management | `SetDataPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 20 | Simulation Management | `DataPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 21 | Simulation Management | `EventReportPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 22 | Simulation Management | `CommentPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 25 | Radio Communications | `TransmitterPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 26 | Radio Communications | `SignalPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 27 | Radio Communications | `ReceiverPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 28 | Distributed Emission Regeneration | `IffAtcNavAidsLayer1Pdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 29 | Distributed Emission Regeneration | `UaPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 31 | Radio Communications | `IntercomSignalPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 32 | Radio Communications | `IntercomControlPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 33 | Entity Management | `AggregateStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 34 | Entity Management | `IsGroupOfPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 35 | Entity Management | `TransferControlRequestPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 36 | Entity Management | `IsPartOfPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 37 | Minefield | `MinefieldStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 38 | Minefield | `MinefieldQueryPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 39 | Minefield | `MinefieldDataPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 40 | Minefield | `MinefieldResponseNackPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 42 | Synthetic Environment | `GriddedDataPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 66 | Entity Information | `CollisionElasticPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 6 | 67 | Entity Information | `EntityStateUpdatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | no | no |
| 7 | 1 | Entity Information | `EntityStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | no | no |
| 7 | 2 | Warfare | `FirePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 3 | Warfare | `DetonationPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 4 | Entity Information | `CollisionPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 5 | Logistics | `ServiceRequestPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 6 | Logistics | `ResupplyOfferPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 7 | Logistics | `ResupplyReceivedPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 9 | Logistics | `RepairCompletePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 10 | Logistics | `RepairResponsePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 11 | Simulation Management | `CreateEntityPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 12 | Simulation Management | `RemoveEntityPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 13 | Simulation Management | `StartResumePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 14 | Simulation Management | `StopFreezePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 15 | Simulation Management | `AcknowledgePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 16 | Simulation Management | `ActionRequestPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 17 | Simulation Management | `ActionResponsePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 18 | Simulation Management | `DataQueryPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 19 | Simulation Management | `SetDataPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 20 | Simulation Management | `DataPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 21 | Simulation Management | `EventReportPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 22 | Simulation Management | `CommentPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 25 | Radio Communications | `TransmitterPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 26 | Radio Communications | `SignalPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 27 | Radio Communications | `ReceiverPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 28 | Distributed Emission Regeneration | `IffPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 29 | Distributed Emission Regeneration | `UaPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 31 | Radio Communications | `IntercomSignalPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 32 | Radio Communications | `IntercomControlPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 36 | Entity Management | `IsPartOfPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 37 | Minefield | `MinefieldStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 40 | Minefield | `MinefieldResponseNackPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 66 | Entity Information | `CollisionElasticPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 67 | Entity Information | `EntityStateUpdatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | no | no |
| 7 | 68 | Warfare | `DirectedEnergyFirePdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
| 7 | 69 | Warfare | `EntityDamageStatusPdu` | yes | no | yes | no | yes | no | yes | no | yes | no | no | no |
