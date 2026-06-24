# Endpoint Coverage

This generated report defines product endpoint behavior for every known DIS 6/7 PDU.

Policy:

- no known PDU may be invisible
- generic behavior is acceptable for early coverage
- Entity State remains the production transform path
- specialized events are added by support level over time

- records: `141`
- missing endpoint behavior: `0`

| DIS | PDU | Class | Support | Python | Unreal | Godot | Lattice Lab |
|---:|---:|---|---|---|---|---|---|
| 6 | 0 | `OtherPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 1 | `EntityStatePdu` | production_supported | state_update | engine_actor_mapping | engine_node_mapping | lattice_entity_mapping |
| 6 | 2 | `FirePdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 6 | 3 | `DetonationPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 6 | 4 | `CollisionPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 6 | 5 | `ServiceRequestPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 6 | `ResupplyOfferPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 7 | `ResupplyReceivedPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 8 | `ResupplyCancelPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 9 | `RepairCompletePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 10 | `RepairResponsePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 11 | `CreateEntityPdu` | endpoint_mapped | typed_event_planned | state_update_planned | state_update_planned | lattice_entity_lifecycle_planned |
| 6 | 12 | `RemoveEntityPdu` | endpoint_mapped | typed_event_planned | state_update_planned | state_update_planned | lattice_entity_lifecycle_planned |
| 6 | 13 | `StartResumePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 14 | `StopFreezePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 15 | `AcknowledgePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 16 | `ActionRequestPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 17 | `ActionResponsePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 18 | `DataQueryPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 19 | `SetDataPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 20 | `DataPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 21 | `EventReportPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 22 | `CommentPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 23 | `ElectronicEmissionsPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 24 | `DesignatorPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 25 | `TransmitterPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 26 | `SignalPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 27 | `ReceiverPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 28 | `IffAtcNavAidsLayer1Pdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 29 | `UaPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 30 | `SeesPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 31 | `IntercomSignalPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 32 | `IntercomControlPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 6 | 33 | `AggregateStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 34 | `IsGroupOfPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 35 | `TransferControlRequestPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 36 | `IsPartOfPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 37 | `MinefieldStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 38 | `MinefieldQueryPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 39 | `MinefieldDataPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 40 | `MinefieldResponseNackPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 41 | `EnvironmentalProcessPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 42 | `GriddedDataPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 43 | `PointObjectStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 44 | `LinearObjectStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 45 | `ArealObjectStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 46 | `TSPIPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 47 | `AppearancePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 48 | `ArticulatedPartsPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 6 | 49 | `LEFirePdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 6 | 50 | `LEDetonationPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 6 | 51 | `CreateEntityReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 52 | `RemoveEntityReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 53 | `StartResumeReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 54 | `StopFreezeReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 55 | `AcknowledgeReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 56 | `ActionRequestReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 57 | `ActionResponseReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 58 | `DataQueryReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 59 | `SetDataReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 60 | `DataReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 61 | `EventReportReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 62 | `CommentReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 63 | `RecordReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 64 | `SetRecordReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 65 | `RecordQueryReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 6 | 66 | `CollisionElasticPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 6 | 67 | `EntityStateUpdatePdu` | endpoint_mapped | typed_event_planned | state_update_planned | state_update_planned | lattice_entity_lifecycle_planned |
| 7 | 0 | `OtherPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 1 | `EntityStatePdu` | production_supported | state_update | engine_actor_mapping | engine_node_mapping | lattice_entity_mapping |
| 7 | 2 | `FirePdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 3 | `DetonationPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 4 | `CollisionPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 5 | `ServiceRequestPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 6 | `ResupplyOfferPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 7 | `ResupplyReceivedPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 8 | `ResupplyCancelPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 9 | `RepairCompletePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 10 | `RepairResponsePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 11 | `CreateEntityPdu` | endpoint_mapped | typed_event_planned | state_update_planned | state_update_planned | lattice_entity_lifecycle_planned |
| 7 | 12 | `RemoveEntityPdu` | endpoint_mapped | typed_event_planned | state_update_planned | state_update_planned | lattice_entity_lifecycle_planned |
| 7 | 13 | `StartResumePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 14 | `StopFreezePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 15 | `AcknowledgePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 16 | `ActionRequestPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 17 | `ActionResponsePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 18 | `DataQueryPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 19 | `SetDataPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 20 | `DataPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 21 | `EventReportPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 22 | `CommentPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 23 | `ElectronicEmissionsPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 24 | `DesignatorPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 25 | `TransmitterPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 26 | `SignalPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 27 | `ReceiverPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 28 | `IffPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 29 | `UaPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 30 | `SeesPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 31 | `IntercomSignalPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 32 | `IntercomControlPdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | communication_event |
| 7 | 33 | `AggregateStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 34 | `IsGroupOfPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 35 | `TransferOwnershipPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 36 | `IsPartOfPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 37 | `MinefieldStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 38 | `MinefieldQueryPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 39 | `MinefieldDataPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 40 | `MinefieldResponseNackPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 41 | `EnvironmentalProcessPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 42 | `GriddedDataPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 43 | `PointObjectStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 44 | `LinearObjectStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 45 | `ArealObjectStatePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 46 | `TSPIPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 47 | `AppearancePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 48 | `ArticulatedPartsPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 49 | `LEFirePdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 50 | `LEDetonationPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 51 | `CreateEntityReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 52 | `RemoveEntityReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 53 | `StartResumeReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 54 | `StopFreezeReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 55 | `AcknowledgeReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 56 | `ActionRequestReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 57 | `ActionResponseReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 58 | `DataQueryReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 59 | `SetDataReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 60 | `DataReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 61 | `EventReportReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 62 | `CommentReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 63 | `RecordReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 64 | `SetRecordReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 65 | `RecordQueryReliablePdu` | cataloged_generic_endpoint | generic_field_event | generic_raw_event | generic_raw_event | simulation_control_event |
| 7 | 66 | `CollisionElasticPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 67 | `EntityStateUpdatePdu` | endpoint_mapped | typed_event_planned | state_update_planned | state_update_planned | lattice_entity_lifecycle_planned |
| 7 | 68 | `DirectedEnergyFirePdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 69 | `EntityDamageStatusPdu` | cataloged_generic_endpoint | generic_field_event | blueprint_event_planned | signal_planned | simulation_event |
| 7 | 70 | `InformationOperationsActionPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 71 | `InformationOperationsReportPdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
| 7 | 72 | `AttributePdu` | cataloged_safe_ingest | generic_field_event | generic_raw_event | generic_raw_event | simulation_pdu_observation |
