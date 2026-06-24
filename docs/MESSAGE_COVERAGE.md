# Message Coverage

This is the generated Alpha 3 message-coverage manifest for fastdis.

Honest current state:

- Every listed DIS 6/7 PDU is cataloged in generated metadata.
- Fixed-header validation is in place for all packets at the shared header layer.
- PDU-specific minimum-length knowledge, typed parsing, and deep fuzzing remain Entity State only.
- Every listed DIS 6/7 PDU has a generated generic packet-view parser, visitor, byte-preserving serializer, and roundtrip guarantee.
- Typed semantic body parsing and deep fuzzing remain Entity State only.

Column definitions:

- `cataloged`: appears in generated DIS 6/7 metadata.
- `header`: shared header parser validates the packet header/declared length path.
- `min`: PDU-specific minimum length is known by typed parser logic.
- `prefix`: a typed body-prefix parser exists.
- `full`: a generated full packet-view parser exists.
- `ser`: a byte-preserving packet-view serializer exists.
- `rt`: generated packet-view parse/serialize roundtrip tests exist.
- `fuzz shallow`: broad header/dispatch/length fuzz coverage exists.
- `fuzz deep`: deep typed-parser fuzz coverage exists.
- `oracle`: independent semantic differential oracle, if any.

| DIS | PDU | Family | Class | cataloged | header | min | prefix | full | ser | rt | fuzz shallow | fuzz deep | oracle |
|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 0 | Protocol Family 0 | `OtherPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 1 | Entity Information | `EntityStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | open-dis-python fixture report |
| 6 | 2 | Warfare | `FirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 3 | Warfare | `DetonationPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 4 | Entity Information | `CollisionPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 5 | Logistics | `ServiceRequestPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 6 | Logistics | `ResupplyOfferPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 7 | Logistics | `ResupplyReceivedPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 8 | Logistics | `ResupplyCancelPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 9 | Logistics | `RepairCompletePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 10 | Logistics | `RepairResponsePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 11 | Simulation Management | `CreateEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 12 | Simulation Management | `RemoveEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 13 | Simulation Management | `StartResumePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 14 | Simulation Management | `StopFreezePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 15 | Simulation Management | `AcknowledgePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 16 | Simulation Management | `ActionRequestPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 17 | Simulation Management | `ActionResponsePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 18 | Simulation Management | `DataQueryPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 19 | Simulation Management | `SetDataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 20 | Simulation Management | `DataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 21 | Simulation Management | `EventReportPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 22 | Simulation Management | `CommentPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 25 | Radio Communications | `TransmitterPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 26 | Radio Communications | `SignalPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 27 | Radio Communications | `ReceiverPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 28 | Distributed Emission Regeneration | `IffAtcNavAidsLayer1Pdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 29 | Distributed Emission Regeneration | `UaPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 31 | Radio Communications | `IntercomSignalPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 32 | Radio Communications | `IntercomControlPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 33 | Entity Management | `AggregateStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 34 | Entity Management | `IsGroupOfPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 35 | Entity Management | `TransferControlRequestPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 36 | Entity Management | `IsPartOfPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 37 | Minefield | `MinefieldStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 38 | Minefield | `MinefieldQueryPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 39 | Minefield | `MinefieldDataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 40 | Minefield | `MinefieldResponseNackPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 42 | Synthetic Environment | `GriddedDataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 46 | Live Entity | `TSPIPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 47 | Live Entity | `AppearancePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 48 | Live Entity | `ArticulatedPartsPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 49 | Live Entity | `LEFirePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 50 | Live Entity | `LEDetonationPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 6 | 66 | Entity Information | `CollisionElasticPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 6 | 67 | Entity Information | `EntityStateUpdatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 0 | Protocol Family 0 | `OtherPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 1 | Entity Information | `EntityStatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes | open-dis-python fixture report |
| 7 | 2 | Warfare | `FirePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 3 | Warfare | `DetonationPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 4 | Entity Information | `CollisionPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 5 | Logistics | `ServiceRequestPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 6 | Logistics | `ResupplyOfferPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 7 | Logistics | `ResupplyReceivedPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 8 | Logistics | `ResupplyCancelPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 9 | Logistics | `RepairCompletePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 10 | Logistics | `RepairResponsePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 11 | Simulation Management | `CreateEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 12 | Simulation Management | `RemoveEntityPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 13 | Simulation Management | `StartResumePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 14 | Simulation Management | `StopFreezePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 15 | Simulation Management | `AcknowledgePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 16 | Simulation Management | `ActionRequestPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 17 | Simulation Management | `ActionResponsePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 18 | Simulation Management | `DataQueryPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 19 | Simulation Management | `SetDataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 20 | Simulation Management | `DataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 21 | Simulation Management | `EventReportPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 22 | Simulation Management | `CommentPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 23 | Distributed Emission Regeneration | `ElectronicEmissionsPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 24 | Distributed Emission Regeneration | `DesignatorPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 25 | Radio Communications | `TransmitterPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 26 | Radio Communications | `SignalPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 27 | Radio Communications | `ReceiverPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 28 | Distributed Emission Regeneration | `IffPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 29 | Distributed Emission Regeneration | `UaPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 30 | Distributed Emission Regeneration | `SeesPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 31 | Radio Communications | `IntercomSignalPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 32 | Radio Communications | `IntercomControlPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 33 | Entity Management | `AggregateStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 34 | Entity Management | `IsGroupOfPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 35 | Entity Management | `TransferOwnershipPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 36 | Entity Management | `IsPartOfPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 37 | Minefield | `MinefieldStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 38 | Minefield | `MinefieldQueryPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 39 | Minefield | `MinefieldDataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 40 | Minefield | `MinefieldResponseNackPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 41 | Synthetic Environment | `EnvironmentalProcessPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 42 | Synthetic Environment | `GriddedDataPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 43 | Synthetic Environment | `PointObjectStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 44 | Synthetic Environment | `LinearObjectStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 45 | Synthetic Environment | `ArealObjectStatePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 46 | Live Entity | `TSPIPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 47 | Live Entity | `AppearancePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 48 | Live Entity | `ArticulatedPartsPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 49 | Live Entity | `LEFirePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 50 | Live Entity | `LEDetonationPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 51 | Simulation Management with Reliability | `CreateEntityReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 52 | Simulation Management with Reliability | `RemoveEntityReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 53 | Simulation Management with Reliability | `StartResumeReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 54 | Simulation Management with Reliability | `StopFreezeReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 55 | Simulation Management with Reliability | `AcknowledgeReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 56 | Simulation Management with Reliability | `ActionRequestReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 57 | Simulation Management with Reliability | `ActionResponseReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 58 | Simulation Management with Reliability | `DataQueryReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 59 | Simulation Management with Reliability | `SetDataReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 60 | Simulation Management with Reliability | `DataReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 61 | Simulation Management with Reliability | `EventReportReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 62 | Simulation Management with Reliability | `CommentReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 63 | Simulation Management with Reliability | `RecordReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 64 | Simulation Management with Reliability | `SetRecordReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 65 | Simulation Management with Reliability | `RecordQueryReliablePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 66 | Entity Information | `CollisionElasticPdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 67 | Entity Information | `EntityStateUpdatePdu` | yes | yes | yes | yes | yes | yes | yes | yes | yes |  |
| 7 | 68 | Warfare | `DirectedEnergyFirePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 69 | Warfare | `EntityDamageStatusPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 70 | Information Operations | `InformationOperationsActionPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 71 | Information Operations | `InformationOperationsReportPdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
| 7 | 72 | Entity Information | `AttributePdu` | yes | yes | no | no | yes | yes | yes | yes | no |  |
