"""Generated slotted typed DIS PDU envelope parsers.

Every standard DIS 6/7 PDU row gets a concrete typed class. Schema-backed
rows also expose declared field names as a lightweight structural field
mapping, while all rows preserve raw packet bytes for byte-for-byte
serialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from . import _fallback


HeaderTuple = tuple[int, int, int, int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class TypedPduDescriptor:
    protocol_version: int
    pdu_type: int
    protocol_family: int
    standard_name: str
    standard_class_name: str
    parser_class: str
    family_name: str
    schema_status: str
    catalog_status: str
    declared_fields: tuple[str, ...]
    parse_level: str


@dataclass(frozen=True, slots=True)
class TypedPdu:
    descriptor: TypedPduDescriptor
    header: HeaderTuple
    packet: bytes
    fields: Mapping[str, object]

    @property
    def body(self) -> bytes:
        return self.packet[12:self.header[5]]

    @property
    def parse_level(self) -> str:
        return self.descriptor.parse_level


@dataclass(frozen=True, slots=True)
class Dis6OtherPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EntityStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6FirePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DetonationPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CollisionPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ServiceRequestPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ResupplyOfferPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ResupplyReceivedPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ResupplyCancelPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RepairCompletePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RepairResponsePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CreateEntityPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RemoveEntityPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StartResumePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StopFreezePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AcknowledgePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionRequestPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionResponsePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataQueryPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SetDataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EventReportPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CommentPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ElectronicEmissionsPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DesignatorPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6TransmitterPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SignalPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ReceiverPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IffAtcNavAidsLayer1Pdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6UaPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SEESPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IntercomSignalPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IntercomControlPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AggregateStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IsGroupOfPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6TransferControlRequestPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IsPartOfPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldQueryPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldDataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldResponseNackPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EnvironmentalProcessPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6GriddedDataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6PointObjectStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6LinearObjectStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ArealObjectStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6TSPIPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AppearancePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ArticulatedPartsPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6LEFirePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6LEDetonationPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CreateEntityReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RemoveEntityReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StartResumeReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StopFreezeReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AcknowledgeReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionRequestReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionResponseReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataQueryReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SetDataReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EventReportReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CommentReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RecordReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SetRecordReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RecordQueryReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CollisionElasticPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EntityStateUpdatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7OtherPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EntityStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7FirePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DetonationPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CollisionPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ServiceRequestPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ResupplyOfferPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ResupplyReceivedPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ResupplyCancelPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RepairCompletePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RepairResponsePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CreateEntityPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RemoveEntityPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StartResumePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StopFreezePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AcknowledgePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionRequestPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionResponsePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataQueryPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SetDataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EventReportPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CommentPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ElectronicEmissionsPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DesignatorPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7TransmitterPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SignalPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ReceiverPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IffPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7UaPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SEESPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IntercomSignalPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IntercomControlPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AggregateStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IsGroupOfPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7TransferOwnershipPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IsPartOfPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldQueryPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldDataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldResponseNackPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EnvironmentalProcessPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7GriddedDataPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7PointObjectStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7LinearObjectStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ArealObjectStatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7TSPIPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AppearancePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ArticulatedPartsPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7LEFirePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7LEDetonationPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CreateEntityReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RemoveEntityReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StartResumeReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StopFreezeReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AcknowledgeReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionRequestReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionResponseReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataQueryReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SetDataReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EventReportReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CommentReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RecordReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SetRecordReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RecordQueryReliablePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CollisionElasticPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EntityStateUpdatePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DirectedEnergyFirePdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EntityDamageStatusPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7InformationOperationsActionPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7InformationOperationsReportPdu(TypedPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AttributePdu(TypedPdu):
    pass


TYPED_PDU_DESCRIPTORS: tuple[TypedPduDescriptor, ...] = (
    TypedPduDescriptor(6, 0, 0, 'Other', 'OtherPdu', 'Dis6OtherPdu', 'Protocol Family 0', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'typed_envelope'),
    TypedPduDescriptor(6, 1, 1, 'Entity State', 'EntityStatePdu', 'Dis6EntityStatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'forceId', 'numberOfArticulationParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'articulationParameters'), 'typed_semantic_prefix'),
    TypedPduDescriptor(6, 2, 2, 'Fire', 'FirePdu', 'Dis6FirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'burstDescriptor', 'velocity', 'rangeToTarget'), 'typed_structural'),
    TypedPduDescriptor(6, 3, 2, 'Detonation', 'DetonationPdu', 'Dis6DetonationPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'burstDescriptor', 'locationInEntityCoordinates', 'detonationResult', 'numberOfArticulationParameters', 'pad', 'articulationParameters'), 'typed_structural'),
    TypedPduDescriptor(6, 4, 1, 'Collision', 'CollisionPdu', 'Dis6CollisionPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location'), 'typed_structural'),
    TypedPduDescriptor(6, 5, 3, 'Service Request', 'ServiceRequestPdu', 'Dis6ServiceRequestPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies'), 'typed_structural'),
    TypedPduDescriptor(6, 6, 3, 'Resupply Offer', 'ResupplyOfferPdu', 'Dis6ResupplyOfferPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'typed_structural'),
    TypedPduDescriptor(6, 7, 3, 'Resupply Received', 'ResupplyReceivedPdu', 'Dis6ResupplyReceivedPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'typed_structural'),
    TypedPduDescriptor(6, 8, 3, 'Resupply Cancel', 'ResupplyCancelPdu', 'Dis6ResupplyCancelPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID'), 'typed_structural'),
    TypedPduDescriptor(6, 9, 3, 'Repair Complete', 'RepairCompletePdu', 'Dis6RepairCompletePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding2'), 'typed_structural'),
    TypedPduDescriptor(6, 10, 3, 'Repair Response', 'RepairResponsePdu', 'Dis6RepairResponsePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2'), 'typed_structural'),
    TypedPduDescriptor(6, 11, 5, 'Create Entity', 'CreateEntityPdu', 'Dis6CreateEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 12, 5, 'Remove Entity', 'RemoveEntityPdu', 'Dis6RemoveEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 13, 5, 'Start/Resume', 'StartResumePdu', 'Dis6StartResumePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 14, 5, 'Stop/Freeze', 'StopFreezePdu', 'Dis6StopFreezePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'padding1', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 15, 5, 'Acknowledge', 'AcknowledgePdu', 'Dis6AcknowledgePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 16, 5, 'Action Request', 'ActionRequestPdu', 'Dis6ActionRequestPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 17, 5, 'Action Response', 'ActionResponsePdu', 'Dis6ActionResponsePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requestStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 18, 5, 'Data Query', 'DataQueryPdu', 'Dis6DataQueryPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 19, 5, 'Set Data', 'SetDataPdu', 'Dis6SetDataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 20, 5, 'Data', 'DataPdu', 'Dis6DataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 21, 5, 'Event Report', 'EventReportPdu', 'Dis6EventReportPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 22, 5, 'Comment', 'CommentPdu', 'Dis6CommentPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(6, 23, 6, 'Electromagnetic Emission', 'ElectronicEmissionsPdu', 'Dis6ElectronicEmissionsPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systems'), 'typed_structural'),
    TypedPduDescriptor(6, 24, 6, 'Designator', 'DesignatorPdu', 'Dis6DesignatorPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration'), 'typed_structural'),
    TypedPduDescriptor(6, 25, 4, 'Transmitter', 'TransmitterPdu', 'Dis6TransmitterPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'radioEntityType', 'transmitState', 'inputSource', 'padding1', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList'), 'typed_structural'),
    TypedPduDescriptor(6, 26, 4, 'Signal', 'SignalPdu', 'Dis6SignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'typed_structural'),
    TypedPduDescriptor(6, 27, 4, 'Receiver', 'ReceiverPdu', 'Dis6ReceiverPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId'), 'typed_structural'),
    TypedPduDescriptor(6, 28, 6, 'IFF/ATC/NAVAIDS', 'IffAtcNavAidsLayer1Pdu', 'Dis6IffAtcNavAidsLayer1Pdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters'), 'typed_structural'),
    TypedPduDescriptor(6, 29, 6, 'Underwater Acoustic', 'UaPdu', 'Dis6UaPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems'), 'typed_structural'),
    TypedPduDescriptor(6, 30, 6, 'Supplemental Emission / Entity State', 'SEESPdu', 'Dis6SEESPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData'), 'typed_structural'),
    TypedPduDescriptor(6, 31, 4, 'Intercom Signal', 'IntercomSignalPdu', 'Dis6IntercomSignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'typed_structural'),
    TypedPduDescriptor(6, 32, 4, 'Intercom Control', 'IntercomControlPdu', 'Dis6IntercomControlPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters'), 'typed_structural'),
    TypedPduDescriptor(6, 33, 7, 'Aggregate State', 'AggregateStatePdu', 'Dis6AggregateStatePdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'aggregateID', 'forceID', 'aggregateState', 'aggregateType', 'formation', 'aggregateMarking', 'dimensions', 'orientation', 'centerOfMass', 'velocity', 'numberOfDisAggregates', 'numberOfDisEntities', 'numberOfSilentAggregateTypes', 'numberOfSilentEntityTypes', 'aggregateIDList', 'entityIDList', 'pad2', 'silentAggregateSystemList', 'silentEntitySystemList', 'numberOfVariableDatumRecords', 'variableDatumList'), 'typed_structural'),
    TypedPduDescriptor(6, 34, 7, 'IsGroupOf', 'IsGroupOfPdu', 'Dis6IsGroupOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'groupEntityID', 'groupedEntityCategory', 'numberOfGroupedEntities', 'pad2', 'latitude', 'longitude', 'groupedEntityDescriptions'), 'typed_structural'),
    TypedPduDescriptor(6, 35, 7, 'Transfer Control', 'TransferControlRequestPdu', 'Dis6TransferControlRequestPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'recevingEntityID', 'requestID', 'requiredReliabilityService', 'tranferType', 'transferEntityID', 'numberOfRecordSets', 'recordSets'), 'typed_structural'),
    TypedPduDescriptor(6, 36, 7, 'IsPartOf', 'IsPartOfPdu', 'Dis6IsPartOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType'), 'typed_structural'),
    TypedPduDescriptor(6, 37, 8, 'Minefield State', 'MinefieldStatePdu', 'Dis6MinefieldStatePdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType'), 'typed_structural'),
    TypedPduDescriptor(6, 38, 8, 'Minefield Query', 'MinefieldQueryPdu', 'Dis6MinefieldQueryPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfPerimeterPoints', 'pad2', 'numberOfSensorTypes', 'dataFilter', 'requestedMineType', 'requestedPerimeterPoints', 'sensorTypes'), 'typed_structural'),
    TypedPduDescriptor(6, 39, 8, 'Minefield Data', 'MinefieldDataPdu', 'Dis6MinefieldDataPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'minefieldSequenceNumbeer', 'requestID', 'pduSequenceNumber', 'numberOfPdus', 'numberOfMinesInThisPdu', 'numberOfSensorTypes', 'pad2', 'dataFilter', 'mineType', 'sensorTypes', 'pad3', 'mineLocation'), 'typed_structural'),
    TypedPduDescriptor(6, 40, 8, 'Minefield Response NACK', 'MinefieldResponseNackPdu', 'Dis6MinefieldResponseNackPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers'), 'typed_structural'),
    TypedPduDescriptor(6, 41, 9, 'Environmental Process', 'EnvironmentalProcessPdu', 'Dis6EnvironmentalProcessPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environementalProcessID', 'environmentType', 'modelType', 'environmentStatus', 'numberOfEnvironmentRecords', 'sequenceNumber', 'environmentRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 42, 9, 'Gridded Data', 'GriddedDataPdu', 'Dis6GriddedDataPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environmentalSimulationApplicationID', 'fieldNumber', 'pduNumber', 'pduTotal', 'coordinateSystem', 'numberOfGridAxes', 'constantGrid', 'environmentType', 'orientation', 'sampleTime', 'totalValues', 'vectorDimension', 'padding1', 'padding2', 'gridDataList'), 'typed_structural'),
    TypedPduDescriptor(6, 43, 9, 'Point Object State', 'PointObjectStatePdu', 'Dis6PointObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2'), 'typed_structural'),
    TypedPduDescriptor(6, 44, 9, 'Linear Object State', 'LinearObjectStatePdu', 'Dis6LinearObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters'), 'typed_structural'),
    TypedPduDescriptor(6, 45, 9, 'Areal Object State', 'ArealObjectStatePdu', 'Dis6ArealObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation'), 'typed_structural'),
    TypedPduDescriptor(6, 46, 11, 'TSPI', 'TSPIPdu', 'Dis6TSPIPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'TSPIFlag', 'entityLocation', 'entityLinearVelocity', 'entityOrientation', 'positionError', 'orientationError', 'deadReckoningParameters', 'measuredSpeed', 'systemSpecificDataLength', 'systemSpecificData'), 'typed_structural'),
    TypedPduDescriptor(6, 47, 11, 'Appearance', 'AppearancePdu', 'Dis6AppearancePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'appearanceFlags', 'forceId', 'entityType', 'alternateEntityType', 'entityMarking', 'capabilities', 'appearanceFields'), 'typed_structural'),
    TypedPduDescriptor(6, 48, 11, 'Articulated Parts', 'ArticulatedPartsPdu', 'Dis6ArticulatedPartsPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'numberOfParameterRecords', 'variableParameters'), 'typed_structural'),
    TypedPduDescriptor(6, 49, 11, 'LE Fire', 'LEFirePdu', 'Dis6LEFirePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'flags', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'location', 'munitionDescriptor', 'velocity', 'range'), 'typed_structural'),
    TypedPduDescriptor(6, 50, 11, 'LE Detonation', 'LEDetonationPdu', 'Dis6LEDetonationPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'detonationFlag1', 'detonationFlag2', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'worldLocation', 'velocity', 'munitionOrientation', 'munitionDescriptor', 'entityLocation', 'detonationResult'), 'typed_structural'),
    TypedPduDescriptor(6, 51, 10, 'Create Entity-R', 'CreateEntityReliablePdu', 'Dis6CreateEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 52, 10, 'Remove Entity-R', 'RemoveEntityReliablePdu', 'Dis6RemoveEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 53, 10, 'Start/Resume-R', 'StartResumeReliablePdu', 'Dis6StartResumeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 54, 10, 'Stop/Freeze-R', 'StopFreezeReliablePdu', 'Dis6StopFreezeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'requiredReliablityService', 'pad1', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 55, 10, 'Acknowledge-R', 'AcknowledgeReliablePdu', 'Dis6AcknowledgeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(6, 56, 10, 'Action Request-R', 'ActionRequestReliablePdu', 'Dis6ActionRequestReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 57, 10, 'Action Response-R', 'ActionResponseReliablePdu', 'Dis6ActionResponseReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'responseStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 58, 10, 'Data Query-R', 'DataQueryReliablePdu', 'Dis6DataQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 59, 10, 'Set Data-R', 'SetDataReliablePdu', 'Dis6SetDataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 60, 10, 'Data-R', 'DataReliablePdu', 'Dis6DataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 61, 10, 'Event Report-R', 'EventReportReliablePdu', 'Dis6EventReportReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'pad1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 62, 10, 'Comment-R', 'CommentReliablePdu', 'Dis6CommentReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(6, 63, 10, 'Record-R', 'RecordReliablePdu', 'Dis6RecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'eventType', 'numberOfRecordSets', 'recordSets'), 'typed_structural'),
    TypedPduDescriptor(6, 64, 10, 'Set Record-R', 'SetRecordReliablePdu', 'Dis6SetRecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfRecordSets', 'recordSets'), 'typed_structural'),
    TypedPduDescriptor(6, 65, 10, 'Record Query-R', 'RecordQueryReliablePdu', 'Dis6RecordQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs'), 'typed_structural'),
    TypedPduDescriptor(6, 66, 1, 'Collision-Elastic', 'CollisionElasticPdu', 'Dis6CollisionElasticPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'location', 'collisionResultXX', 'collisionResultXY', 'collisionResultXZ', 'collisionResultYY', 'collisionResultYZ', 'collisionResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution'), 'typed_structural'),
    TypedPduDescriptor(6, 67, 1, 'Entity State Update', 'EntityStateUpdatePdu', 'Dis6EntityStateUpdatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'padding1', 'numberOfArticulationParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'articulationParameters'), 'typed_semantic_prefix'),
    TypedPduDescriptor(7, 0, 0, 'Other', 'OtherPdu', 'Dis7OtherPdu', 'Protocol Family 0', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'typed_envelope'),
    TypedPduDescriptor(7, 1, 1, 'Entity State', 'EntityStatePdu', 'Dis7EntityStatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'forceId', 'numberOfVariableParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'variableParameters'), 'typed_semantic_prefix'),
    TypedPduDescriptor(7, 2, 2, 'Fire', 'FirePdu', 'Dis7FirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionExpendibleID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'descriptor', 'velocity', 'range'), 'typed_structural'),
    TypedPduDescriptor(7, 3, 2, 'Detonation', 'DetonationPdu', 'Dis7DetonationPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'explodingEntityID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'descriptor', 'locationOfEntityCoordinates', 'detonationResult', 'numberOfVariableParameters', 'pad', 'variableParameters'), 'typed_structural'),
    TypedPduDescriptor(7, 4, 1, 'Collision', 'CollisionPdu', 'Dis7CollisionPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location'), 'typed_structural'),
    TypedPduDescriptor(7, 5, 3, 'Service Request', 'ServiceRequestPdu', 'Dis7ServiceRequestPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies'), 'typed_structural'),
    TypedPduDescriptor(7, 6, 3, 'Resupply Offer', 'ResupplyOfferPdu', 'Dis7ResupplyOfferPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'typed_structural'),
    TypedPduDescriptor(7, 7, 3, 'Resupply Received', 'ResupplyReceivedPdu', 'Dis7ResupplyReceivedPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'typed_structural'),
    TypedPduDescriptor(7, 8, 3, 'Resupply Cancel', 'ResupplyCancelPdu', 'Dis7ResupplyCancelPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID'), 'typed_structural'),
    TypedPduDescriptor(7, 9, 3, 'Repair Complete', 'RepairCompletePdu', 'Dis7RepairCompletePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding4'), 'typed_structural'),
    TypedPduDescriptor(7, 10, 3, 'Repair Response', 'RepairResponsePdu', 'Dis7RepairResponsePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2'), 'typed_structural'),
    TypedPduDescriptor(7, 11, 5, 'Create Entity', 'CreateEntityPdu', 'Dis7CreateEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 12, 5, 'Remove Entity', 'RemoveEntityPdu', 'Dis7RemoveEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 13, 5, 'Start/Resume', 'StartResumePdu', 'Dis7StartResumePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 14, 5, 'Stop/Freeze', 'StopFreezePdu', 'Dis7StopFreezePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'padding1', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 15, 5, 'Acknowledge', 'AcknowledgePdu', 'Dis7AcknowledgePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 16, 5, 'Action Request', 'ActionRequestPdu', 'Dis7ActionRequestPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 17, 5, 'Action Response', 'ActionResponsePdu', 'Dis7ActionResponsePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requestStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 18, 5, 'Data Query', 'DataQueryPdu', 'Dis7DataQueryPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 19, 5, 'Set Data', 'SetDataPdu', 'Dis7SetDataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 20, 5, 'Data', 'DataPdu', 'Dis7DataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 21, 5, 'Event Report', 'EventReportPdu', 'Dis7EventReportPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 22, 5, 'Comment', 'CommentPdu', 'Dis7CommentPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'typed_structural'),
    TypedPduDescriptor(7, 23, 6, 'Electromagnetic Emission', 'ElectronicEmissionsPdu', 'Dis7ElectronicEmissionsPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systemDataLength', 'numberOfBeams', 'emitterSystem', 'location', 'systems'), 'typed_structural'),
    TypedPduDescriptor(7, 24, 6, 'Designator', 'DesignatorPdu', 'Dis7DesignatorPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration'), 'typed_structural'),
    TypedPduDescriptor(7, 25, 4, 'Transmitter', 'TransmitterPdu', 'Dis7TransmitterPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'radioReferenceID', 'radioNumber', 'radioEntityType', 'transmitState', 'inputSource', 'variableTransmitterParameterCount', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList'), 'typed_structural'),
    TypedPduDescriptor(7, 26, 4, 'Signal', 'SignalPdu', 'Dis7SignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'typed_structural'),
    TypedPduDescriptor(7, 27, 4, 'Receiver', 'ReceiverPdu', 'Dis7ReceiverPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId'), 'typed_structural'),
    TypedPduDescriptor(7, 28, 6, 'IFF', 'IffPdu', 'Dis7IffPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters'), 'typed_structural'),
    TypedPduDescriptor(7, 29, 6, 'Underwater Acoustic', 'UaPdu', 'Dis7UaPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems'), 'typed_structural'),
    TypedPduDescriptor(7, 30, 6, 'Supplemental Emission / Entity State', 'SEESPdu', 'Dis7SEESPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData'), 'typed_structural'),
    TypedPduDescriptor(7, 31, 4, 'Intercom Signal', 'IntercomSignalPdu', 'Dis7IntercomSignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'typed_structural'),
    TypedPduDescriptor(7, 32, 4, 'Intercom Control', 'IntercomControlPdu', 'Dis7IntercomControlPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters'), 'typed_structural'),
    TypedPduDescriptor(7, 33, 7, 'Aggregate State', 'AggregateStatePdu', 'Dis7AggregateStatePdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'aggregateID', 'forceID', 'aggregateState', 'aggregateType', 'formation', 'aggregateMarking', 'dimensions', 'orientation', 'centerOfMass', 'velocity', 'numberOfDisAggregates', 'numberOfDisEntities', 'numberOfSilentAggregateTypes', 'numberOfSilentEntityTypes', 'aggregateIDList', 'entityIDList', 'pad2', 'silentAggregateSystemList', 'silentEntitySystemList', 'numberOfVariableDatumRecords', 'variableDatumList'), 'typed_structural'),
    TypedPduDescriptor(7, 34, 7, 'IsGroupOf', 'IsGroupOfPdu', 'Dis7IsGroupOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'groupEntityID', 'groupedEntityCategory', 'numberOfGroupedEntities', 'pad2', 'latitude', 'longitude', 'groupedEntityDescriptions'), 'typed_structural'),
    TypedPduDescriptor(7, 35, 7, 'Transfer Ownership', 'TransferOwnershipPdu', 'Dis7TransferOwnershipPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'recevingEntityID', 'requestID', 'requiredReliabilityService', 'tranferType', 'transferEntityID', 'numberOfRecordSets', 'recordSets'), 'typed_structural'),
    TypedPduDescriptor(7, 36, 7, 'IsPartOf', 'IsPartOfPdu', 'Dis7IsPartOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType'), 'typed_structural'),
    TypedPduDescriptor(7, 37, 8, 'Minefield State', 'MinefieldStatePdu', 'Dis7MinefieldStatePdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType'), 'typed_structural'),
    TypedPduDescriptor(7, 38, 8, 'Minefield Query', 'MinefieldQueryPdu', 'Dis7MinefieldQueryPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfPerimeterPoints', 'pad2', 'numberOfSensorTypes', 'dataFilter', 'requestedMineType', 'requestedPerimeterPoints', 'sensorTypes'), 'typed_structural'),
    TypedPduDescriptor(7, 39, 8, 'Minefield Data', 'MinefieldDataPdu', 'Dis7MinefieldDataPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'minefieldSequenceNumbeer', 'requestID', 'pduSequenceNumber', 'numberOfPdus', 'numberOfMinesInThisPdu', 'numberOfSensorTypes', 'pad2', 'dataFilter', 'mineType', 'sensorTypes', 'pad3', 'mineLocation'), 'typed_structural'),
    TypedPduDescriptor(7, 40, 8, 'Minefield Response NACK', 'MinefieldResponseNackPdu', 'Dis7MinefieldResponseNackPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers'), 'typed_structural'),
    TypedPduDescriptor(7, 41, 9, 'Environmental Process', 'EnvironmentalProcessPdu', 'Dis7EnvironmentalProcessPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'environementalProcessID', 'environmentType', 'modelType', 'environmentStatus', 'numberOfEnvironmentRecords', 'sequenceNumber', 'environmentRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 42, 9, 'Gridded Data', 'GriddedDataPdu', 'Dis7GriddedDataPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'environmentalSimulationApplicationID', 'fieldNumber', 'pduNumber', 'pduTotal', 'coordinateSystem', 'numberOfGridAxes', 'constantGrid', 'environmentType', 'orientation', 'sampleTime', 'totalValues', 'vectorDimension', 'padding1', 'padding2', 'gridDataList'), 'typed_structural'),
    TypedPduDescriptor(7, 43, 9, 'Point Object State', 'PointObjectStatePdu', 'Dis7PointObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2'), 'typed_structural'),
    TypedPduDescriptor(7, 44, 9, 'Linear Object State', 'LinearObjectStatePdu', 'Dis7LinearObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters'), 'typed_structural'),
    TypedPduDescriptor(7, 45, 9, 'Areal Object State', 'ArealObjectStatePdu', 'Dis7ArealObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'specificObjectAppearance', 'generalObjectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation'), 'typed_structural'),
    TypedPduDescriptor(7, 46, 11, 'TSPI', 'TSPIPdu', 'Dis7TSPIPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'TSPIFlag', 'entityLocation', 'entityLinearVelocity', 'entityOrientation', 'positionError', 'orientationError', 'deadReckoningParameters', 'measuredSpeed', 'systemSpecificDataLength', 'systemSpecificData'), 'typed_structural'),
    TypedPduDescriptor(7, 47, 11, 'Appearance', 'AppearancePdu', 'Dis7AppearancePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'appearanceFlags', 'forceId', 'entityType', 'alternateEntityType', 'entityMarking', 'capabilities', 'appearanceFields'), 'typed_structural'),
    TypedPduDescriptor(7, 48, 11, 'Articulated Parts', 'ArticulatedPartsPdu', 'Dis7ArticulatedPartsPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'numberOfParameterRecords', 'variableParameters'), 'typed_structural'),
    TypedPduDescriptor(7, 49, 11, 'LE Fire', 'LEFirePdu', 'Dis7LEFirePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'flags', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'location', 'munitionDescriptor', 'velocity', 'range'), 'typed_structural'),
    TypedPduDescriptor(7, 50, 11, 'LE Detonation', 'LEDetonationPdu', 'Dis7LEDetonationPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'detonationFlag1', 'detonationFlag2', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'worldLocation', 'velocity', 'munitionOrientation', 'munitionDescriptor', 'entityLocation', 'detonationResult'), 'typed_structural'),
    TypedPduDescriptor(7, 51, 10, 'Create Entity-R', 'CreateEntityReliablePdu', 'Dis7CreateEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 52, 10, 'Remove Entity-R', 'RemoveEntityReliablePdu', 'Dis7RemoveEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 53, 10, 'Start/Resume-R', 'StartResumeReliablePdu', 'Dis7StartResumeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 54, 10, 'Stop/Freeze-R', 'StopFreezeReliablePdu', 'Dis7StopFreezeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'requiredReliablityService', 'pad1', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 55, 10, 'Acknowledge-R', 'AcknowledgeReliablePdu', 'Dis7AcknowledgeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'typed_structural'),
    TypedPduDescriptor(7, 56, 10, 'Action Request-R', 'ActionRequestReliablePdu', 'Dis7ActionRequestReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 57, 10, 'Action Response-R', 'ActionResponseReliablePdu', 'Dis7ActionResponseReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'responseStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 58, 10, 'Data Query-R', 'DataQueryReliablePdu', 'Dis7DataQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 59, 10, 'Set Data-R', 'SetDataReliablePdu', 'Dis7SetDataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 60, 10, 'Data-R', 'DataReliablePdu', 'Dis7DataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 61, 10, 'Event Report-R', 'EventReportReliablePdu', 'Dis7EventReportReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'pad1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 62, 10, 'Comment-R', 'CommentReliablePdu', 'Dis7CommentReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 63, 10, 'Record-R', 'RecordReliablePdu', 'Dis7RecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'eventType', 'numberOfRecordSets', 'recordSets'), 'typed_structural'),
    TypedPduDescriptor(7, 64, 10, 'Set Record-R', 'SetRecordReliablePdu', 'Dis7SetRecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfRecordSets', 'recordSets'), 'typed_structural'),
    TypedPduDescriptor(7, 65, 10, 'Record Query-R', 'RecordQueryReliablePdu', 'Dis7RecordQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs'), 'typed_structural'),
    TypedPduDescriptor(7, 66, 1, 'Collision-Elastic', 'CollisionElasticPdu', 'Dis7CollisionElasticPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'locationOfImpact', 'collisionIntermediateResultXX', 'collisionIntermediateResultXY', 'collisionIntermediateResultXZ', 'collisionIntermediateResultYY', 'collisionIntermediateResultYZ', 'collisionIntermediateResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution'), 'typed_structural'),
    TypedPduDescriptor(7, 67, 1, 'Entity State Update', 'EntityStateUpdatePdu', 'Dis7EntityStateUpdatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'padding1', 'numberOfVariableParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'variableParameters'), 'typed_semantic_prefix'),
    TypedPduDescriptor(7, 68, 2, 'Directed Energy Fire', 'DirectedEnergyFirePdu', 'Dis7DirectedEnergyFirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionType', 'shotStartTime', 'commulativeShotTime', 'ApertureEmitterLocation', 'apertureDiameter', 'wavelength', 'peakIrradiance', 'pulseRepetitionFrequency', 'pulseWidth', 'flags', 'pulseShape', 'padding1', 'padding2', 'padding3', 'numberOfDERecords', 'dERecords'), 'typed_structural'),
    TypedPduDescriptor(7, 69, 2, 'Entity Damage Status', 'EntityDamageStatusPdu', 'Dis7EntityDamageStatusPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'damagedEntityID', 'padding1', 'padding2', 'numberOfDamageDescription', 'damageDescriptionRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 70, 13, 'Information Operations Action', 'InformationOperationsActionPdu', 'Dis7InformationOperationsActionPdu', 'Information Operations', 'PRESENT', 'CATALOGED', ('originatingSimID', 'receivingSimID', 'requestID', 'IOWarfareType', 'IOSimulationSource', 'IOActionType', 'IOActionPhase', 'padding1', 'ioAttackerID', 'ioPrimaryTargetID', 'padding2', 'numberOfIORecords', 'ioRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 71, 13, 'Information Operations Report', 'InformationOperationsReportPdu', 'Dis7InformationOperationsReportPdu', 'Information Operations', 'PRESENT', 'CATALOGED', ('originatingSimID', 'ioSimSource', 'ioReportType', 'padding1', 'ioAttackerID', 'ioPrimaryTargetID', 'padding2', 'padding3', 'numberOfIORecords', 'ioRecords'), 'typed_structural'),
    TypedPduDescriptor(7, 72, 1, 'Attribute', 'AttributePdu', 'Dis7AttributePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingSimulationAddress', 'padding1', 'padding2', 'attributeRecordPduType', 'attributeRecordProtocolVersion', 'masterAttributeRecordType', 'actionCode', 'padding3', 'numberAttributeRecordSet'), 'typed_structural'),
)

_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in TYPED_PDU_DESCRIPTORS}
_CLASS_BY_NAME: dict[str, type[TypedPdu]] = {
    'Dis6OtherPdu': Dis6OtherPdu,
    'Dis6EntityStatePdu': Dis6EntityStatePdu,
    'Dis6FirePdu': Dis6FirePdu,
    'Dis6DetonationPdu': Dis6DetonationPdu,
    'Dis6CollisionPdu': Dis6CollisionPdu,
    'Dis6ServiceRequestPdu': Dis6ServiceRequestPdu,
    'Dis6ResupplyOfferPdu': Dis6ResupplyOfferPdu,
    'Dis6ResupplyReceivedPdu': Dis6ResupplyReceivedPdu,
    'Dis6ResupplyCancelPdu': Dis6ResupplyCancelPdu,
    'Dis6RepairCompletePdu': Dis6RepairCompletePdu,
    'Dis6RepairResponsePdu': Dis6RepairResponsePdu,
    'Dis6CreateEntityPdu': Dis6CreateEntityPdu,
    'Dis6RemoveEntityPdu': Dis6RemoveEntityPdu,
    'Dis6StartResumePdu': Dis6StartResumePdu,
    'Dis6StopFreezePdu': Dis6StopFreezePdu,
    'Dis6AcknowledgePdu': Dis6AcknowledgePdu,
    'Dis6ActionRequestPdu': Dis6ActionRequestPdu,
    'Dis6ActionResponsePdu': Dis6ActionResponsePdu,
    'Dis6DataQueryPdu': Dis6DataQueryPdu,
    'Dis6SetDataPdu': Dis6SetDataPdu,
    'Dis6DataPdu': Dis6DataPdu,
    'Dis6EventReportPdu': Dis6EventReportPdu,
    'Dis6CommentPdu': Dis6CommentPdu,
    'Dis6ElectronicEmissionsPdu': Dis6ElectronicEmissionsPdu,
    'Dis6DesignatorPdu': Dis6DesignatorPdu,
    'Dis6TransmitterPdu': Dis6TransmitterPdu,
    'Dis6SignalPdu': Dis6SignalPdu,
    'Dis6ReceiverPdu': Dis6ReceiverPdu,
    'Dis6IffAtcNavAidsLayer1Pdu': Dis6IffAtcNavAidsLayer1Pdu,
    'Dis6UaPdu': Dis6UaPdu,
    'Dis6SEESPdu': Dis6SEESPdu,
    'Dis6IntercomSignalPdu': Dis6IntercomSignalPdu,
    'Dis6IntercomControlPdu': Dis6IntercomControlPdu,
    'Dis6AggregateStatePdu': Dis6AggregateStatePdu,
    'Dis6IsGroupOfPdu': Dis6IsGroupOfPdu,
    'Dis6TransferControlRequestPdu': Dis6TransferControlRequestPdu,
    'Dis6IsPartOfPdu': Dis6IsPartOfPdu,
    'Dis6MinefieldStatePdu': Dis6MinefieldStatePdu,
    'Dis6MinefieldQueryPdu': Dis6MinefieldQueryPdu,
    'Dis6MinefieldDataPdu': Dis6MinefieldDataPdu,
    'Dis6MinefieldResponseNackPdu': Dis6MinefieldResponseNackPdu,
    'Dis6EnvironmentalProcessPdu': Dis6EnvironmentalProcessPdu,
    'Dis6GriddedDataPdu': Dis6GriddedDataPdu,
    'Dis6PointObjectStatePdu': Dis6PointObjectStatePdu,
    'Dis6LinearObjectStatePdu': Dis6LinearObjectStatePdu,
    'Dis6ArealObjectStatePdu': Dis6ArealObjectStatePdu,
    'Dis6TSPIPdu': Dis6TSPIPdu,
    'Dis6AppearancePdu': Dis6AppearancePdu,
    'Dis6ArticulatedPartsPdu': Dis6ArticulatedPartsPdu,
    'Dis6LEFirePdu': Dis6LEFirePdu,
    'Dis6LEDetonationPdu': Dis6LEDetonationPdu,
    'Dis6CreateEntityReliablePdu': Dis6CreateEntityReliablePdu,
    'Dis6RemoveEntityReliablePdu': Dis6RemoveEntityReliablePdu,
    'Dis6StartResumeReliablePdu': Dis6StartResumeReliablePdu,
    'Dis6StopFreezeReliablePdu': Dis6StopFreezeReliablePdu,
    'Dis6AcknowledgeReliablePdu': Dis6AcknowledgeReliablePdu,
    'Dis6ActionRequestReliablePdu': Dis6ActionRequestReliablePdu,
    'Dis6ActionResponseReliablePdu': Dis6ActionResponseReliablePdu,
    'Dis6DataQueryReliablePdu': Dis6DataQueryReliablePdu,
    'Dis6SetDataReliablePdu': Dis6SetDataReliablePdu,
    'Dis6DataReliablePdu': Dis6DataReliablePdu,
    'Dis6EventReportReliablePdu': Dis6EventReportReliablePdu,
    'Dis6CommentReliablePdu': Dis6CommentReliablePdu,
    'Dis6RecordReliablePdu': Dis6RecordReliablePdu,
    'Dis6SetRecordReliablePdu': Dis6SetRecordReliablePdu,
    'Dis6RecordQueryReliablePdu': Dis6RecordQueryReliablePdu,
    'Dis6CollisionElasticPdu': Dis6CollisionElasticPdu,
    'Dis6EntityStateUpdatePdu': Dis6EntityStateUpdatePdu,
    'Dis7OtherPdu': Dis7OtherPdu,
    'Dis7EntityStatePdu': Dis7EntityStatePdu,
    'Dis7FirePdu': Dis7FirePdu,
    'Dis7DetonationPdu': Dis7DetonationPdu,
    'Dis7CollisionPdu': Dis7CollisionPdu,
    'Dis7ServiceRequestPdu': Dis7ServiceRequestPdu,
    'Dis7ResupplyOfferPdu': Dis7ResupplyOfferPdu,
    'Dis7ResupplyReceivedPdu': Dis7ResupplyReceivedPdu,
    'Dis7ResupplyCancelPdu': Dis7ResupplyCancelPdu,
    'Dis7RepairCompletePdu': Dis7RepairCompletePdu,
    'Dis7RepairResponsePdu': Dis7RepairResponsePdu,
    'Dis7CreateEntityPdu': Dis7CreateEntityPdu,
    'Dis7RemoveEntityPdu': Dis7RemoveEntityPdu,
    'Dis7StartResumePdu': Dis7StartResumePdu,
    'Dis7StopFreezePdu': Dis7StopFreezePdu,
    'Dis7AcknowledgePdu': Dis7AcknowledgePdu,
    'Dis7ActionRequestPdu': Dis7ActionRequestPdu,
    'Dis7ActionResponsePdu': Dis7ActionResponsePdu,
    'Dis7DataQueryPdu': Dis7DataQueryPdu,
    'Dis7SetDataPdu': Dis7SetDataPdu,
    'Dis7DataPdu': Dis7DataPdu,
    'Dis7EventReportPdu': Dis7EventReportPdu,
    'Dis7CommentPdu': Dis7CommentPdu,
    'Dis7ElectronicEmissionsPdu': Dis7ElectronicEmissionsPdu,
    'Dis7DesignatorPdu': Dis7DesignatorPdu,
    'Dis7TransmitterPdu': Dis7TransmitterPdu,
    'Dis7SignalPdu': Dis7SignalPdu,
    'Dis7ReceiverPdu': Dis7ReceiverPdu,
    'Dis7IffPdu': Dis7IffPdu,
    'Dis7UaPdu': Dis7UaPdu,
    'Dis7SEESPdu': Dis7SEESPdu,
    'Dis7IntercomSignalPdu': Dis7IntercomSignalPdu,
    'Dis7IntercomControlPdu': Dis7IntercomControlPdu,
    'Dis7AggregateStatePdu': Dis7AggregateStatePdu,
    'Dis7IsGroupOfPdu': Dis7IsGroupOfPdu,
    'Dis7TransferOwnershipPdu': Dis7TransferOwnershipPdu,
    'Dis7IsPartOfPdu': Dis7IsPartOfPdu,
    'Dis7MinefieldStatePdu': Dis7MinefieldStatePdu,
    'Dis7MinefieldQueryPdu': Dis7MinefieldQueryPdu,
    'Dis7MinefieldDataPdu': Dis7MinefieldDataPdu,
    'Dis7MinefieldResponseNackPdu': Dis7MinefieldResponseNackPdu,
    'Dis7EnvironmentalProcessPdu': Dis7EnvironmentalProcessPdu,
    'Dis7GriddedDataPdu': Dis7GriddedDataPdu,
    'Dis7PointObjectStatePdu': Dis7PointObjectStatePdu,
    'Dis7LinearObjectStatePdu': Dis7LinearObjectStatePdu,
    'Dis7ArealObjectStatePdu': Dis7ArealObjectStatePdu,
    'Dis7TSPIPdu': Dis7TSPIPdu,
    'Dis7AppearancePdu': Dis7AppearancePdu,
    'Dis7ArticulatedPartsPdu': Dis7ArticulatedPartsPdu,
    'Dis7LEFirePdu': Dis7LEFirePdu,
    'Dis7LEDetonationPdu': Dis7LEDetonationPdu,
    'Dis7CreateEntityReliablePdu': Dis7CreateEntityReliablePdu,
    'Dis7RemoveEntityReliablePdu': Dis7RemoveEntityReliablePdu,
    'Dis7StartResumeReliablePdu': Dis7StartResumeReliablePdu,
    'Dis7StopFreezeReliablePdu': Dis7StopFreezeReliablePdu,
    'Dis7AcknowledgeReliablePdu': Dis7AcknowledgeReliablePdu,
    'Dis7ActionRequestReliablePdu': Dis7ActionRequestReliablePdu,
    'Dis7ActionResponseReliablePdu': Dis7ActionResponseReliablePdu,
    'Dis7DataQueryReliablePdu': Dis7DataQueryReliablePdu,
    'Dis7SetDataReliablePdu': Dis7SetDataReliablePdu,
    'Dis7DataReliablePdu': Dis7DataReliablePdu,
    'Dis7EventReportReliablePdu': Dis7EventReportReliablePdu,
    'Dis7CommentReliablePdu': Dis7CommentReliablePdu,
    'Dis7RecordReliablePdu': Dis7RecordReliablePdu,
    'Dis7SetRecordReliablePdu': Dis7SetRecordReliablePdu,
    'Dis7RecordQueryReliablePdu': Dis7RecordQueryReliablePdu,
    'Dis7CollisionElasticPdu': Dis7CollisionElasticPdu,
    'Dis7EntityStateUpdatePdu': Dis7EntityStateUpdatePdu,
    'Dis7DirectedEnergyFirePdu': Dis7DirectedEnergyFirePdu,
    'Dis7EntityDamageStatusPdu': Dis7EntityDamageStatusPdu,
    'Dis7InformationOperationsActionPdu': Dis7InformationOperationsActionPdu,
    'Dis7InformationOperationsReportPdu': Dis7InformationOperationsReportPdu,
    'Dis7AttributePdu': Dis7AttributePdu,
}


def find_typed_pdu_descriptor(protocol_version: int, pdu_type: int) -> TypedPduDescriptor | None:
    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))


def _field_map(descriptor: TypedPduDescriptor, header: HeaderTuple, packet: bytes) -> Mapping[str, object]:
    values: dict[str, object] = {
        'protocolVersion': header[0],
        'exerciseID': header[1],
        'pduType': header[2],
        'protocolFamily': header[3],
        'timestamp': header[4],
        'length': header[5],
        'status': header[6],
        'padding': header[7],
        'rawBody': packet[12:header[5]],
    }
    for name in descriptor.declared_fields:
        values.setdefault(name, None)
    return MappingProxyType(values)


def parse_typed_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> TypedPdu | None:
    header = _fallback.parse_header(data, strict=strict)
    if header is None:
        return None
    descriptor = find_typed_pdu_descriptor(header[0], header[2])
    if descriptor is None:
        if strict:
            raise ValueError(f'unknown DIS PDU type {header[2]} for protocol version {header[0]}')
        return None
    packet = bytes(memoryview(data).cast('B')[:header[5]])
    cls = _CLASS_BY_NAME[descriptor.parser_class]
    return cls(descriptor=descriptor, header=header, packet=packet, fields=_field_map(descriptor, header, packet))


def serialize_typed_pdu(view: TypedPdu) -> bytes:
    if not isinstance(view, TypedPdu):
        raise TypeError('serialize_typed_pdu expects a TypedPdu')
    return bytes(view.packet)


def parse_many_typed(packets: list[bytes] | tuple[bytes, ...], *, strict: bool = False) -> list[TypedPdu]:
    out: list[TypedPdu] = []
    for packet in packets:
        view = parse_typed_pdu(packet, strict=strict)
        if view is not None:
            out.append(view)
    return out


TYPED_PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_typed_pdu for item in TYPED_PDU_DESCRIPTORS}
TYPED_PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_typed_pdu for item in TYPED_PDU_DESCRIPTORS}
