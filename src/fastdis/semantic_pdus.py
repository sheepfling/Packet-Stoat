"""Generated slotted semantic DIS PDU parser entry points.

Every standard DIS 6/7 PDU row gets a semantic parser class. Rows without
full domain decoding are represented as explicit semantic observations
with raw-body preservation and diagnostics.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .typed_pdus import TypedPdu, parse_typed_pdu, serialize_typed_pdu


@dataclass(frozen=True, slots=True)
class SemanticPduDescriptor:
    protocol_version: int
    pdu_type: int
    protocol_family: int
    standard_name: str
    standard_class_name: str
    semantic_class: str
    typed_class: str
    family_name: str
    schema_status: str
    catalog_status: str
    declared_fields: tuple[str, ...]
    semantic_level: str
    fully_domain_decoded: bool


@dataclass(frozen=True, slots=True)
class SemanticPdu:
    descriptor: SemanticPduDescriptor
    typed: TypedPdu
    semantic_fields: Mapping[str, object]
    diagnostics: tuple[str, ...]

    @property
    def header(self):
        return self.typed.header

    @property
    def packet(self) -> bytes:
        return self.typed.packet

    @property
    def body(self) -> bytes:
        return self.typed.body

    @property
    def semantic_level(self) -> str:
        return self.descriptor.semantic_level


@dataclass(frozen=True, slots=True)
class Dis6OtherSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EntityStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6FireSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DetonationSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CollisionSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ServiceRequestSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ResupplyOfferSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ResupplyReceivedSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ResupplyCancelSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RepairCompleteSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RepairResponseSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CreateEntitySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RemoveEntitySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StartResumeSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StopFreezeSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AcknowledgeSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionRequestSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionResponseSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataQuerySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SetDataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EventReportSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CommentSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ElectronicEmissionsSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DesignatorSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6TransmitterSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SignalSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ReceiverSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IffAtcNavAidsLayer1SemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6UaSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SEESSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IntercomSignalSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IntercomControlSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AggregateStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IsGroupOfSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6TransferControlRequestSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6IsPartOfSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldQuerySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldDataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6MinefieldResponseNackSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EnvironmentalProcessSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6GriddedDataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6PointObjectStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6LinearObjectStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ArealObjectStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6TSPISemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AppearanceSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ArticulatedPartsSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6LEFireSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6LEDetonationSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CreateEntityReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RemoveEntityReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StartResumeReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6StopFreezeReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6AcknowledgeReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionRequestReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6ActionResponseReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataQueryReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SetDataReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6DataReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EventReportReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CommentReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RecordReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6SetRecordReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6RecordQueryReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6CollisionElasticSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis6EntityStateUpdateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7OtherSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EntityStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7FireSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DetonationSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CollisionSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ServiceRequestSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ResupplyOfferSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ResupplyReceivedSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ResupplyCancelSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RepairCompleteSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RepairResponseSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CreateEntitySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RemoveEntitySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StartResumeSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StopFreezeSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AcknowledgeSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionRequestSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionResponseSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataQuerySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SetDataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EventReportSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CommentSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ElectronicEmissionsSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DesignatorSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7TransmitterSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SignalSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ReceiverSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IffSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7UaSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SEESSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IntercomSignalSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IntercomControlSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AggregateStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IsGroupOfSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7TransferOwnershipSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7IsPartOfSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldQuerySemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldDataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7MinefieldResponseNackSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EnvironmentalProcessSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7GriddedDataSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7PointObjectStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7LinearObjectStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ArealObjectStateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7TSPISemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AppearanceSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ArticulatedPartsSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7LEFireSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7LEDetonationSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CreateEntityReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RemoveEntityReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StartResumeReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7StopFreezeReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AcknowledgeReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionRequestReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7ActionResponseReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataQueryReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SetDataReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DataReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EventReportReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CommentReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RecordReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7SetRecordReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7RecordQueryReliableSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7CollisionElasticSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EntityStateUpdateSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7DirectedEnergyFireSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7EntityDamageStatusSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7InformationOperationsActionSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7InformationOperationsReportSemanticPdu(SemanticPdu):
    pass

@dataclass(frozen=True, slots=True)
class Dis7AttributeSemanticPdu(SemanticPdu):
    pass


SEMANTIC_PDU_DESCRIPTORS: tuple[SemanticPduDescriptor, ...] = (
    SemanticPduDescriptor(6, 0, 0, 'Other', 'OtherPdu', 'Dis6OtherSemanticPdu', 'Dis6OtherPdu', 'Protocol Family 0', 'PRESENT', 'CATALOGED', ('opaquePayload',), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 1, 1, 'Entity State', 'EntityStatePdu', 'Dis6EntityStateSemanticPdu', 'Dis6EntityStatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'forceId', 'numberOfArticulationParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'articulationParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 2, 2, 'Fire', 'FirePdu', 'Dis6FireSemanticPdu', 'Dis6FirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'burstDescriptor', 'velocity', 'rangeToTarget'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 3, 2, 'Detonation', 'DetonationPdu', 'Dis6DetonationSemanticPdu', 'Dis6DetonationPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'burstDescriptor', 'locationInEntityCoordinates', 'detonationResult', 'numberOfArticulationParameters', 'pad', 'articulationParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 4, 1, 'Collision', 'CollisionPdu', 'Dis6CollisionSemanticPdu', 'Dis6CollisionPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 5, 3, 'Service Request', 'ServiceRequestPdu', 'Dis6ServiceRequestSemanticPdu', 'Dis6ServiceRequestPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 6, 3, 'Resupply Offer', 'ResupplyOfferPdu', 'Dis6ResupplyOfferSemanticPdu', 'Dis6ResupplyOfferPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 7, 3, 'Resupply Received', 'ResupplyReceivedPdu', 'Dis6ResupplyReceivedSemanticPdu', 'Dis6ResupplyReceivedPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 8, 3, 'Resupply Cancel', 'ResupplyCancelPdu', 'Dis6ResupplyCancelSemanticPdu', 'Dis6ResupplyCancelPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 9, 3, 'Repair Complete', 'RepairCompletePdu', 'Dis6RepairCompleteSemanticPdu', 'Dis6RepairCompletePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding2'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 10, 3, 'Repair Response', 'RepairResponsePdu', 'Dis6RepairResponseSemanticPdu', 'Dis6RepairResponsePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 11, 5, 'Create Entity', 'CreateEntityPdu', 'Dis6CreateEntitySemanticPdu', 'Dis6CreateEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 12, 5, 'Remove Entity', 'RemoveEntityPdu', 'Dis6RemoveEntitySemanticPdu', 'Dis6RemoveEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 13, 5, 'Start/Resume', 'StartResumePdu', 'Dis6StartResumeSemanticPdu', 'Dis6StartResumePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 14, 5, 'Stop/Freeze', 'StopFreezePdu', 'Dis6StopFreezeSemanticPdu', 'Dis6StopFreezePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'padding1', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 15, 5, 'Acknowledge', 'AcknowledgePdu', 'Dis6AcknowledgeSemanticPdu', 'Dis6AcknowledgePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 16, 5, 'Action Request', 'ActionRequestPdu', 'Dis6ActionRequestSemanticPdu', 'Dis6ActionRequestPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 17, 5, 'Action Response', 'ActionResponsePdu', 'Dis6ActionResponseSemanticPdu', 'Dis6ActionResponsePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requestStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 18, 5, 'Data Query', 'DataQueryPdu', 'Dis6DataQuerySemanticPdu', 'Dis6DataQueryPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 19, 5, 'Set Data', 'SetDataPdu', 'Dis6SetDataSemanticPdu', 'Dis6SetDataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 20, 5, 'Data', 'DataPdu', 'Dis6DataSemanticPdu', 'Dis6DataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 21, 5, 'Event Report', 'EventReportPdu', 'Dis6EventReportSemanticPdu', 'Dis6EventReportPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 22, 5, 'Comment', 'CommentPdu', 'Dis6CommentSemanticPdu', 'Dis6CommentPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 23, 6, 'Electromagnetic Emission', 'ElectronicEmissionsPdu', 'Dis6ElectronicEmissionsSemanticPdu', 'Dis6ElectronicEmissionsPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systems'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 24, 6, 'Designator', 'DesignatorPdu', 'Dis6DesignatorSemanticPdu', 'Dis6DesignatorPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 25, 4, 'Transmitter', 'TransmitterPdu', 'Dis6TransmitterSemanticPdu', 'Dis6TransmitterPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'radioEntityType', 'transmitState', 'inputSource', 'padding1', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 26, 4, 'Signal', 'SignalPdu', 'Dis6SignalSemanticPdu', 'Dis6SignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 27, 4, 'Receiver', 'ReceiverPdu', 'Dis6ReceiverSemanticPdu', 'Dis6ReceiverPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 28, 6, 'IFF/ATC/NAVAIDS', 'IffAtcNavAidsLayer1Pdu', 'Dis6IffAtcNavAidsLayer1SemanticPdu', 'Dis6IffAtcNavAidsLayer1Pdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 29, 6, 'Underwater Acoustic', 'UaPdu', 'Dis6UaSemanticPdu', 'Dis6UaPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 30, 6, 'Supplemental Emission / Entity State', 'SEESPdu', 'Dis6SEESSemanticPdu', 'Dis6SEESPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 31, 4, 'Intercom Signal', 'IntercomSignalPdu', 'Dis6IntercomSignalSemanticPdu', 'Dis6IntercomSignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 32, 4, 'Intercom Control', 'IntercomControlPdu', 'Dis6IntercomControlSemanticPdu', 'Dis6IntercomControlPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 33, 7, 'Aggregate State', 'AggregateStatePdu', 'Dis6AggregateStateSemanticPdu', 'Dis6AggregateStatePdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'aggregateID', 'forceID', 'aggregateState', 'aggregateType', 'formation', 'aggregateMarking', 'dimensions', 'orientation', 'centerOfMass', 'velocity', 'numberOfDisAggregates', 'numberOfDisEntities', 'numberOfSilentAggregateTypes', 'numberOfSilentEntityTypes', 'aggregateIDList', 'entityIDList', 'pad2', 'silentAggregateSystemList', 'silentEntitySystemList', 'numberOfVariableDatumRecords', 'variableDatumList'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 34, 7, 'IsGroupOf', 'IsGroupOfPdu', 'Dis6IsGroupOfSemanticPdu', 'Dis6IsGroupOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'groupEntityID', 'groupedEntityCategory', 'numberOfGroupedEntities', 'pad2', 'latitude', 'longitude', 'groupedEntityDescriptions'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 35, 7, 'Transfer Control', 'TransferControlRequestPdu', 'Dis6TransferControlRequestSemanticPdu', 'Dis6TransferControlRequestPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'recevingEntityID', 'requestID', 'requiredReliabilityService', 'tranferType', 'transferEntityID', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 36, 7, 'IsPartOf', 'IsPartOfPdu', 'Dis6IsPartOfSemanticPdu', 'Dis6IsPartOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 37, 8, 'Minefield State', 'MinefieldStatePdu', 'Dis6MinefieldStateSemanticPdu', 'Dis6MinefieldStatePdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 38, 8, 'Minefield Query', 'MinefieldQueryPdu', 'Dis6MinefieldQuerySemanticPdu', 'Dis6MinefieldQueryPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfPerimeterPoints', 'pad2', 'numberOfSensorTypes', 'dataFilter', 'requestedMineType', 'requestedPerimeterPoints', 'sensorTypes'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 39, 8, 'Minefield Data', 'MinefieldDataPdu', 'Dis6MinefieldDataSemanticPdu', 'Dis6MinefieldDataPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'minefieldSequenceNumbeer', 'requestID', 'pduSequenceNumber', 'numberOfPdus', 'numberOfMinesInThisPdu', 'numberOfSensorTypes', 'pad2', 'dataFilter', 'mineType', 'sensorTypes', 'pad3', 'mineLocation'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 40, 8, 'Minefield Response NACK', 'MinefieldResponseNackPdu', 'Dis6MinefieldResponseNackSemanticPdu', 'Dis6MinefieldResponseNackPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 41, 9, 'Environmental Process', 'EnvironmentalProcessPdu', 'Dis6EnvironmentalProcessSemanticPdu', 'Dis6EnvironmentalProcessPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environementalProcessID', 'environmentType', 'modelType', 'environmentStatus', 'numberOfEnvironmentRecords', 'sequenceNumber', 'environmentRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 42, 9, 'Gridded Data', 'GriddedDataPdu', 'Dis6GriddedDataSemanticPdu', 'Dis6GriddedDataPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environmentalSimulationApplicationID', 'fieldNumber', 'pduNumber', 'pduTotal', 'coordinateSystem', 'numberOfGridAxes', 'constantGrid', 'environmentType', 'orientation', 'sampleTime', 'totalValues', 'vectorDimension', 'padding1', 'padding2', 'gridDataList'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 43, 9, 'Point Object State', 'PointObjectStatePdu', 'Dis6PointObjectStateSemanticPdu', 'Dis6PointObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 44, 9, 'Linear Object State', 'LinearObjectStatePdu', 'Dis6LinearObjectStateSemanticPdu', 'Dis6LinearObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 45, 9, 'Areal Object State', 'ArealObjectStatePdu', 'Dis6ArealObjectStateSemanticPdu', 'Dis6ArealObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 46, 11, 'TSPI', 'TSPIPdu', 'Dis6TSPISemanticPdu', 'Dis6TSPIPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'TSPIFlag', 'entityLocation', 'entityLinearVelocity', 'entityOrientation', 'positionError', 'orientationError', 'deadReckoningParameters', 'measuredSpeed', 'systemSpecificDataLength', 'systemSpecificData'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 47, 11, 'Appearance', 'AppearancePdu', 'Dis6AppearanceSemanticPdu', 'Dis6AppearancePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'appearanceFlags', 'forceId', 'entityType', 'alternateEntityType', 'entityMarking', 'capabilities', 'appearanceFields'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 48, 11, 'Articulated Parts', 'ArticulatedPartsPdu', 'Dis6ArticulatedPartsSemanticPdu', 'Dis6ArticulatedPartsPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'numberOfParameterRecords', 'variableParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 49, 11, 'LE Fire', 'LEFirePdu', 'Dis6LEFireSemanticPdu', 'Dis6LEFirePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'flags', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'location', 'munitionDescriptor', 'velocity', 'range'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 50, 11, 'LE Detonation', 'LEDetonationPdu', 'Dis6LEDetonationSemanticPdu', 'Dis6LEDetonationPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'detonationFlag1', 'detonationFlag2', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'worldLocation', 'velocity', 'munitionOrientation', 'munitionDescriptor', 'entityLocation', 'detonationResult'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 51, 10, 'Create Entity-R', 'CreateEntityReliablePdu', 'Dis6CreateEntityReliableSemanticPdu', 'Dis6CreateEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 52, 10, 'Remove Entity-R', 'RemoveEntityReliablePdu', 'Dis6RemoveEntityReliableSemanticPdu', 'Dis6RemoveEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 53, 10, 'Start/Resume-R', 'StartResumeReliablePdu', 'Dis6StartResumeReliableSemanticPdu', 'Dis6StartResumeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 54, 10, 'Stop/Freeze-R', 'StopFreezeReliablePdu', 'Dis6StopFreezeReliableSemanticPdu', 'Dis6StopFreezeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'requiredReliablityService', 'pad1', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 55, 10, 'Acknowledge-R', 'AcknowledgeReliablePdu', 'Dis6AcknowledgeReliableSemanticPdu', 'Dis6AcknowledgeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 56, 10, 'Action Request-R', 'ActionRequestReliablePdu', 'Dis6ActionRequestReliableSemanticPdu', 'Dis6ActionRequestReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 57, 10, 'Action Response-R', 'ActionResponseReliablePdu', 'Dis6ActionResponseReliableSemanticPdu', 'Dis6ActionResponseReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'responseStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 58, 10, 'Data Query-R', 'DataQueryReliablePdu', 'Dis6DataQueryReliableSemanticPdu', 'Dis6DataQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 59, 10, 'Set Data-R', 'SetDataReliablePdu', 'Dis6SetDataReliableSemanticPdu', 'Dis6SetDataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 60, 10, 'Data-R', 'DataReliablePdu', 'Dis6DataReliableSemanticPdu', 'Dis6DataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 61, 10, 'Event Report-R', 'EventReportReliablePdu', 'Dis6EventReportReliableSemanticPdu', 'Dis6EventReportReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'pad1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 62, 10, 'Comment-R', 'CommentReliablePdu', 'Dis6CommentReliableSemanticPdu', 'Dis6CommentReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 63, 10, 'Record-R', 'RecordReliablePdu', 'Dis6RecordReliableSemanticPdu', 'Dis6RecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'eventType', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 64, 10, 'Set Record-R', 'SetRecordReliablePdu', 'Dis6SetRecordReliableSemanticPdu', 'Dis6SetRecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 65, 10, 'Record Query-R', 'RecordQueryReliablePdu', 'Dis6RecordQueryReliableSemanticPdu', 'Dis6RecordQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 66, 1, 'Collision-Elastic', 'CollisionElasticPdu', 'Dis6CollisionElasticSemanticPdu', 'Dis6CollisionElasticPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'location', 'collisionResultXX', 'collisionResultXY', 'collisionResultXZ', 'collisionResultYY', 'collisionResultYZ', 'collisionResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 67, 1, 'Entity State Update', 'EntityStateUpdatePdu', 'Dis6EntityStateUpdateSemanticPdu', 'Dis6EntityStateUpdatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'padding1', 'numberOfArticulationParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'articulationParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 0, 0, 'Other', 'OtherPdu', 'Dis7OtherSemanticPdu', 'Dis7OtherPdu', 'Protocol Family 0', 'PRESENT', 'CATALOGED', ('opaquePayload',), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 1, 1, 'Entity State', 'EntityStatePdu', 'Dis7EntityStateSemanticPdu', 'Dis7EntityStatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'forceId', 'numberOfVariableParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'variableParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 2, 2, 'Fire', 'FirePdu', 'Dis7FireSemanticPdu', 'Dis7FirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionExpendibleID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'descriptor', 'velocity', 'range'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 3, 2, 'Detonation', 'DetonationPdu', 'Dis7DetonationSemanticPdu', 'Dis7DetonationPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'explodingEntityID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'descriptor', 'locationOfEntityCoordinates', 'detonationResult', 'numberOfVariableParameters', 'pad', 'variableParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 4, 1, 'Collision', 'CollisionPdu', 'Dis7CollisionSemanticPdu', 'Dis7CollisionPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 5, 3, 'Service Request', 'ServiceRequestPdu', 'Dis7ServiceRequestSemanticPdu', 'Dis7ServiceRequestPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 6, 3, 'Resupply Offer', 'ResupplyOfferPdu', 'Dis7ResupplyOfferSemanticPdu', 'Dis7ResupplyOfferPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 7, 3, 'Resupply Received', 'ResupplyReceivedPdu', 'Dis7ResupplyReceivedSemanticPdu', 'Dis7ResupplyReceivedPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 8, 3, 'Resupply Cancel', 'ResupplyCancelPdu', 'Dis7ResupplyCancelSemanticPdu', 'Dis7ResupplyCancelPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 9, 3, 'Repair Complete', 'RepairCompletePdu', 'Dis7RepairCompleteSemanticPdu', 'Dis7RepairCompletePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding4'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 10, 3, 'Repair Response', 'RepairResponsePdu', 'Dis7RepairResponseSemanticPdu', 'Dis7RepairResponsePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 11, 5, 'Create Entity', 'CreateEntityPdu', 'Dis7CreateEntitySemanticPdu', 'Dis7CreateEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 12, 5, 'Remove Entity', 'RemoveEntityPdu', 'Dis7RemoveEntitySemanticPdu', 'Dis7RemoveEntityPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 13, 5, 'Start/Resume', 'StartResumePdu', 'Dis7StartResumeSemanticPdu', 'Dis7StartResumePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 14, 5, 'Stop/Freeze', 'StopFreezePdu', 'Dis7StopFreezeSemanticPdu', 'Dis7StopFreezePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'padding1', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 15, 5, 'Acknowledge', 'AcknowledgePdu', 'Dis7AcknowledgeSemanticPdu', 'Dis7AcknowledgePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 16, 5, 'Action Request', 'ActionRequestPdu', 'Dis7ActionRequestSemanticPdu', 'Dis7ActionRequestPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 17, 5, 'Action Response', 'ActionResponsePdu', 'Dis7ActionResponseSemanticPdu', 'Dis7ActionResponsePdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requestStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 18, 5, 'Data Query', 'DataQueryPdu', 'Dis7DataQuerySemanticPdu', 'Dis7DataQueryPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 19, 5, 'Set Data', 'SetDataPdu', 'Dis7SetDataSemanticPdu', 'Dis7SetDataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 20, 5, 'Data', 'DataPdu', 'Dis7DataSemanticPdu', 'Dis7DataPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 21, 5, 'Event Report', 'EventReportPdu', 'Dis7EventReportSemanticPdu', 'Dis7EventReportPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 22, 5, 'Comment', 'CommentPdu', 'Dis7CommentSemanticPdu', 'Dis7CommentPdu', 'Simulation Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 23, 6, 'Electromagnetic Emission', 'ElectronicEmissionsPdu', 'Dis7ElectronicEmissionsSemanticPdu', 'Dis7ElectronicEmissionsPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systemDataLength', 'numberOfBeams', 'emitterSystem', 'location', 'systems'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 24, 6, 'Designator', 'DesignatorPdu', 'Dis7DesignatorSemanticPdu', 'Dis7DesignatorPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 25, 4, 'Transmitter', 'TransmitterPdu', 'Dis7TransmitterSemanticPdu', 'Dis7TransmitterPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'radioReferenceID', 'radioNumber', 'radioEntityType', 'transmitState', 'inputSource', 'variableTransmitterParameterCount', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 26, 4, 'Signal', 'SignalPdu', 'Dis7SignalSemanticPdu', 'Dis7SignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 27, 4, 'Receiver', 'ReceiverPdu', 'Dis7ReceiverSemanticPdu', 'Dis7ReceiverPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 28, 6, 'IFF', 'IffPdu', 'Dis7IffSemanticPdu', 'Dis7IffPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 29, 6, 'Underwater Acoustic', 'UaPdu', 'Dis7UaSemanticPdu', 'Dis7UaPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 30, 6, 'Supplemental Emission / Entity State', 'SEESPdu', 'Dis7SEESSemanticPdu', 'Dis7SEESPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 31, 4, 'Intercom Signal', 'IntercomSignalPdu', 'Dis7IntercomSignalSemanticPdu', 'Dis7IntercomSignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 32, 4, 'Intercom Control', 'IntercomControlPdu', 'Dis7IntercomControlSemanticPdu', 'Dis7IntercomControlPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 33, 7, 'Aggregate State', 'AggregateStatePdu', 'Dis7AggregateStateSemanticPdu', 'Dis7AggregateStatePdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'aggregateID', 'forceID', 'aggregateState', 'aggregateType', 'formation', 'aggregateMarking', 'dimensions', 'orientation', 'centerOfMass', 'velocity', 'numberOfDisAggregates', 'numberOfDisEntities', 'numberOfSilentAggregateTypes', 'numberOfSilentEntityTypes', 'aggregateIDList', 'entityIDList', 'pad2', 'silentAggregateSystemList', 'silentEntitySystemList', 'numberOfVariableDatumRecords', 'variableDatumList'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 34, 7, 'IsGroupOf', 'IsGroupOfPdu', 'Dis7IsGroupOfSemanticPdu', 'Dis7IsGroupOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'groupEntityID', 'groupedEntityCategory', 'numberOfGroupedEntities', 'pad2', 'latitude', 'longitude', 'groupedEntityDescriptions'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 35, 7, 'Transfer Ownership', 'TransferOwnershipPdu', 'Dis7TransferOwnershipSemanticPdu', 'Dis7TransferOwnershipPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'recevingEntityID', 'requestID', 'requiredReliabilityService', 'tranferType', 'transferEntityID', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 36, 7, 'IsPartOf', 'IsPartOfPdu', 'Dis7IsPartOfSemanticPdu', 'Dis7IsPartOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 37, 8, 'Minefield State', 'MinefieldStatePdu', 'Dis7MinefieldStateSemanticPdu', 'Dis7MinefieldStatePdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 38, 8, 'Minefield Query', 'MinefieldQueryPdu', 'Dis7MinefieldQuerySemanticPdu', 'Dis7MinefieldQueryPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfPerimeterPoints', 'pad2', 'numberOfSensorTypes', 'dataFilter', 'requestedMineType', 'requestedPerimeterPoints', 'sensorTypes'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 39, 8, 'Minefield Data', 'MinefieldDataPdu', 'Dis7MinefieldDataSemanticPdu', 'Dis7MinefieldDataPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'minefieldSequenceNumbeer', 'requestID', 'pduSequenceNumber', 'numberOfPdus', 'numberOfMinesInThisPdu', 'numberOfSensorTypes', 'pad2', 'dataFilter', 'mineType', 'sensorTypes', 'pad3', 'mineLocation'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 40, 8, 'Minefield Response NACK', 'MinefieldResponseNackPdu', 'Dis7MinefieldResponseNackSemanticPdu', 'Dis7MinefieldResponseNackPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 41, 9, 'Environmental Process', 'EnvironmentalProcessPdu', 'Dis7EnvironmentalProcessSemanticPdu', 'Dis7EnvironmentalProcessPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'environementalProcessID', 'environmentType', 'modelType', 'environmentStatus', 'numberOfEnvironmentRecords', 'sequenceNumber', 'environmentRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 42, 9, 'Gridded Data', 'GriddedDataPdu', 'Dis7GriddedDataSemanticPdu', 'Dis7GriddedDataPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'environmentalSimulationApplicationID', 'fieldNumber', 'pduNumber', 'pduTotal', 'coordinateSystem', 'numberOfGridAxes', 'constantGrid', 'environmentType', 'orientation', 'sampleTime', 'totalValues', 'vectorDimension', 'padding1', 'padding2', 'gridDataList'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 43, 9, 'Point Object State', 'PointObjectStatePdu', 'Dis7PointObjectStateSemanticPdu', 'Dis7PointObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 44, 9, 'Linear Object State', 'LinearObjectStatePdu', 'Dis7LinearObjectStateSemanticPdu', 'Dis7LinearObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 45, 9, 'Areal Object State', 'ArealObjectStatePdu', 'Dis7ArealObjectStateSemanticPdu', 'Dis7ArealObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'specificObjectAppearance', 'generalObjectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 46, 11, 'TSPI', 'TSPIPdu', 'Dis7TSPISemanticPdu', 'Dis7TSPIPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'TSPIFlag', 'entityLocation', 'entityLinearVelocity', 'entityOrientation', 'positionError', 'orientationError', 'deadReckoningParameters', 'measuredSpeed', 'systemSpecificDataLength', 'systemSpecificData'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 47, 11, 'Appearance', 'AppearancePdu', 'Dis7AppearanceSemanticPdu', 'Dis7AppearancePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'appearanceFlags', 'forceId', 'entityType', 'alternateEntityType', 'entityMarking', 'capabilities', 'appearanceFields'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 48, 11, 'Articulated Parts', 'ArticulatedPartsPdu', 'Dis7ArticulatedPartsSemanticPdu', 'Dis7ArticulatedPartsPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('liveEntityId', 'numberOfParameterRecords', 'variableParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 49, 11, 'LE Fire', 'LEFirePdu', 'Dis7LEFireSemanticPdu', 'Dis7LEFirePdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'flags', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'location', 'munitionDescriptor', 'velocity', 'range'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 50, 11, 'LE Detonation', 'LEDetonationPdu', 'Dis7LEDetonationSemanticPdu', 'Dis7LEDetonationPdu', 'Live Entity', 'PRESENT', 'CATALOGED', ('firingLiveEntityId', 'detonationFlag1', 'detonationFlag2', 'targetLiveEntityId', 'munitionLiveEntityId', 'eventId', 'worldLocation', 'velocity', 'munitionOrientation', 'munitionDescriptor', 'entityLocation', 'detonationResult'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 51, 10, 'Create Entity-R', 'CreateEntityReliablePdu', 'Dis7CreateEntityReliableSemanticPdu', 'Dis7CreateEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 52, 10, 'Remove Entity-R', 'RemoveEntityReliablePdu', 'Dis7RemoveEntityReliableSemanticPdu', 'Dis7RemoveEntityReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 53, 10, 'Start/Resume-R', 'StartResumeReliablePdu', 'Dis7StartResumeReliableSemanticPdu', 'Dis7StartResumeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 54, 10, 'Stop/Freeze-R', 'StopFreezeReliablePdu', 'Dis7StopFreezeReliableSemanticPdu', 'Dis7StopFreezeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'requiredReliablityService', 'pad1', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 55, 10, 'Acknowledge-R', 'AcknowledgeReliablePdu', 'Dis7AcknowledgeReliableSemanticPdu', 'Dis7AcknowledgeReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 56, 10, 'Action Request-R', 'ActionRequestReliablePdu', 'Dis7ActionRequestReliableSemanticPdu', 'Dis7ActionRequestReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 57, 10, 'Action Response-R', 'ActionResponseReliablePdu', 'Dis7ActionResponseReliableSemanticPdu', 'Dis7ActionResponseReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'responseStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 58, 10, 'Data Query-R', 'DataQueryReliablePdu', 'Dis7DataQueryReliableSemanticPdu', 'Dis7DataQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 59, 10, 'Set Data-R', 'SetDataReliablePdu', 'Dis7SetDataReliableSemanticPdu', 'Dis7SetDataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 60, 10, 'Data-R', 'DataReliablePdu', 'Dis7DataReliableSemanticPdu', 'Dis7DataReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 61, 10, 'Event Report-R', 'EventReportReliablePdu', 'Dis7EventReportReliableSemanticPdu', 'Dis7EventReportReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'pad1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 62, 10, 'Comment-R', 'CommentReliablePdu', 'Dis7CommentReliableSemanticPdu', 'Dis7CommentReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 63, 10, 'Record-R', 'RecordReliablePdu', 'Dis7RecordReliableSemanticPdu', 'Dis7RecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'eventType', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 64, 10, 'Set Record-R', 'SetRecordReliablePdu', 'Dis7SetRecordReliableSemanticPdu', 'Dis7SetRecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 65, 10, 'Record Query-R', 'RecordQueryReliablePdu', 'Dis7RecordQueryReliableSemanticPdu', 'Dis7RecordQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 66, 1, 'Collision-Elastic', 'CollisionElasticPdu', 'Dis7CollisionElasticSemanticPdu', 'Dis7CollisionElasticPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'locationOfImpact', 'collisionIntermediateResultXX', 'collisionIntermediateResultXY', 'collisionIntermediateResultXZ', 'collisionIntermediateResultYY', 'collisionIntermediateResultYZ', 'collisionIntermediateResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 67, 1, 'Entity State Update', 'EntityStateUpdatePdu', 'Dis7EntityStateUpdateSemanticPdu', 'Dis7EntityStateUpdatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'padding1', 'numberOfVariableParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'variableParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 68, 2, 'Directed Energy Fire', 'DirectedEnergyFirePdu', 'Dis7DirectedEnergyFireSemanticPdu', 'Dis7DirectedEnergyFirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionType', 'shotStartTime', 'commulativeShotTime', 'ApertureEmitterLocation', 'apertureDiameter', 'wavelength', 'peakIrradiance', 'pulseRepetitionFrequency', 'pulseWidth', 'flags', 'pulseShape', 'padding1', 'padding2', 'padding3', 'numberOfDERecords', 'dERecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 69, 2, 'Entity Damage Status', 'EntityDamageStatusPdu', 'Dis7EntityDamageStatusSemanticPdu', 'Dis7EntityDamageStatusPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'damagedEntityID', 'padding1', 'padding2', 'numberOfDamageDescription', 'damageDescriptionRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 70, 13, 'Information Operations Action', 'InformationOperationsActionPdu', 'Dis7InformationOperationsActionSemanticPdu', 'Dis7InformationOperationsActionPdu', 'Information Operations', 'PRESENT', 'CATALOGED', ('originatingSimID', 'receivingSimID', 'requestID', 'IOWarfareType', 'IOSimulationSource', 'IOActionType', 'IOActionPhase', 'padding1', 'ioAttackerID', 'ioPrimaryTargetID', 'padding2', 'numberOfIORecords', 'ioRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 71, 13, 'Information Operations Report', 'InformationOperationsReportPdu', 'Dis7InformationOperationsReportSemanticPdu', 'Dis7InformationOperationsReportPdu', 'Information Operations', 'PRESENT', 'CATALOGED', ('originatingSimID', 'ioSimSource', 'ioReportType', 'padding1', 'ioAttackerID', 'ioPrimaryTargetID', 'padding2', 'padding3', 'numberOfIORecords', 'ioRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 72, 1, 'Attribute', 'AttributePdu', 'Dis7AttributeSemanticPdu', 'Dis7AttributePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingSimulationAddress', 'padding1', 'padding2', 'attributeRecordPduType', 'attributeRecordProtocolVersion', 'masterAttributeRecordType', 'actionCode', 'padding3', 'numberAttributeRecordSet'), 'semantic_decoded', True),
)

_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in SEMANTIC_PDU_DESCRIPTORS}
_CLASS_BY_NAME: dict[str, type[SemanticPdu]] = {
    'Dis6OtherSemanticPdu': Dis6OtherSemanticPdu,
    'Dis6EntityStateSemanticPdu': Dis6EntityStateSemanticPdu,
    'Dis6FireSemanticPdu': Dis6FireSemanticPdu,
    'Dis6DetonationSemanticPdu': Dis6DetonationSemanticPdu,
    'Dis6CollisionSemanticPdu': Dis6CollisionSemanticPdu,
    'Dis6ServiceRequestSemanticPdu': Dis6ServiceRequestSemanticPdu,
    'Dis6ResupplyOfferSemanticPdu': Dis6ResupplyOfferSemanticPdu,
    'Dis6ResupplyReceivedSemanticPdu': Dis6ResupplyReceivedSemanticPdu,
    'Dis6ResupplyCancelSemanticPdu': Dis6ResupplyCancelSemanticPdu,
    'Dis6RepairCompleteSemanticPdu': Dis6RepairCompleteSemanticPdu,
    'Dis6RepairResponseSemanticPdu': Dis6RepairResponseSemanticPdu,
    'Dis6CreateEntitySemanticPdu': Dis6CreateEntitySemanticPdu,
    'Dis6RemoveEntitySemanticPdu': Dis6RemoveEntitySemanticPdu,
    'Dis6StartResumeSemanticPdu': Dis6StartResumeSemanticPdu,
    'Dis6StopFreezeSemanticPdu': Dis6StopFreezeSemanticPdu,
    'Dis6AcknowledgeSemanticPdu': Dis6AcknowledgeSemanticPdu,
    'Dis6ActionRequestSemanticPdu': Dis6ActionRequestSemanticPdu,
    'Dis6ActionResponseSemanticPdu': Dis6ActionResponseSemanticPdu,
    'Dis6DataQuerySemanticPdu': Dis6DataQuerySemanticPdu,
    'Dis6SetDataSemanticPdu': Dis6SetDataSemanticPdu,
    'Dis6DataSemanticPdu': Dis6DataSemanticPdu,
    'Dis6EventReportSemanticPdu': Dis6EventReportSemanticPdu,
    'Dis6CommentSemanticPdu': Dis6CommentSemanticPdu,
    'Dis6ElectronicEmissionsSemanticPdu': Dis6ElectronicEmissionsSemanticPdu,
    'Dis6DesignatorSemanticPdu': Dis6DesignatorSemanticPdu,
    'Dis6TransmitterSemanticPdu': Dis6TransmitterSemanticPdu,
    'Dis6SignalSemanticPdu': Dis6SignalSemanticPdu,
    'Dis6ReceiverSemanticPdu': Dis6ReceiverSemanticPdu,
    'Dis6IffAtcNavAidsLayer1SemanticPdu': Dis6IffAtcNavAidsLayer1SemanticPdu,
    'Dis6UaSemanticPdu': Dis6UaSemanticPdu,
    'Dis6SEESSemanticPdu': Dis6SEESSemanticPdu,
    'Dis6IntercomSignalSemanticPdu': Dis6IntercomSignalSemanticPdu,
    'Dis6IntercomControlSemanticPdu': Dis6IntercomControlSemanticPdu,
    'Dis6AggregateStateSemanticPdu': Dis6AggregateStateSemanticPdu,
    'Dis6IsGroupOfSemanticPdu': Dis6IsGroupOfSemanticPdu,
    'Dis6TransferControlRequestSemanticPdu': Dis6TransferControlRequestSemanticPdu,
    'Dis6IsPartOfSemanticPdu': Dis6IsPartOfSemanticPdu,
    'Dis6MinefieldStateSemanticPdu': Dis6MinefieldStateSemanticPdu,
    'Dis6MinefieldQuerySemanticPdu': Dis6MinefieldQuerySemanticPdu,
    'Dis6MinefieldDataSemanticPdu': Dis6MinefieldDataSemanticPdu,
    'Dis6MinefieldResponseNackSemanticPdu': Dis6MinefieldResponseNackSemanticPdu,
    'Dis6EnvironmentalProcessSemanticPdu': Dis6EnvironmentalProcessSemanticPdu,
    'Dis6GriddedDataSemanticPdu': Dis6GriddedDataSemanticPdu,
    'Dis6PointObjectStateSemanticPdu': Dis6PointObjectStateSemanticPdu,
    'Dis6LinearObjectStateSemanticPdu': Dis6LinearObjectStateSemanticPdu,
    'Dis6ArealObjectStateSemanticPdu': Dis6ArealObjectStateSemanticPdu,
    'Dis6TSPISemanticPdu': Dis6TSPISemanticPdu,
    'Dis6AppearanceSemanticPdu': Dis6AppearanceSemanticPdu,
    'Dis6ArticulatedPartsSemanticPdu': Dis6ArticulatedPartsSemanticPdu,
    'Dis6LEFireSemanticPdu': Dis6LEFireSemanticPdu,
    'Dis6LEDetonationSemanticPdu': Dis6LEDetonationSemanticPdu,
    'Dis6CreateEntityReliableSemanticPdu': Dis6CreateEntityReliableSemanticPdu,
    'Dis6RemoveEntityReliableSemanticPdu': Dis6RemoveEntityReliableSemanticPdu,
    'Dis6StartResumeReliableSemanticPdu': Dis6StartResumeReliableSemanticPdu,
    'Dis6StopFreezeReliableSemanticPdu': Dis6StopFreezeReliableSemanticPdu,
    'Dis6AcknowledgeReliableSemanticPdu': Dis6AcknowledgeReliableSemanticPdu,
    'Dis6ActionRequestReliableSemanticPdu': Dis6ActionRequestReliableSemanticPdu,
    'Dis6ActionResponseReliableSemanticPdu': Dis6ActionResponseReliableSemanticPdu,
    'Dis6DataQueryReliableSemanticPdu': Dis6DataQueryReliableSemanticPdu,
    'Dis6SetDataReliableSemanticPdu': Dis6SetDataReliableSemanticPdu,
    'Dis6DataReliableSemanticPdu': Dis6DataReliableSemanticPdu,
    'Dis6EventReportReliableSemanticPdu': Dis6EventReportReliableSemanticPdu,
    'Dis6CommentReliableSemanticPdu': Dis6CommentReliableSemanticPdu,
    'Dis6RecordReliableSemanticPdu': Dis6RecordReliableSemanticPdu,
    'Dis6SetRecordReliableSemanticPdu': Dis6SetRecordReliableSemanticPdu,
    'Dis6RecordQueryReliableSemanticPdu': Dis6RecordQueryReliableSemanticPdu,
    'Dis6CollisionElasticSemanticPdu': Dis6CollisionElasticSemanticPdu,
    'Dis6EntityStateUpdateSemanticPdu': Dis6EntityStateUpdateSemanticPdu,
    'Dis7OtherSemanticPdu': Dis7OtherSemanticPdu,
    'Dis7EntityStateSemanticPdu': Dis7EntityStateSemanticPdu,
    'Dis7FireSemanticPdu': Dis7FireSemanticPdu,
    'Dis7DetonationSemanticPdu': Dis7DetonationSemanticPdu,
    'Dis7CollisionSemanticPdu': Dis7CollisionSemanticPdu,
    'Dis7ServiceRequestSemanticPdu': Dis7ServiceRequestSemanticPdu,
    'Dis7ResupplyOfferSemanticPdu': Dis7ResupplyOfferSemanticPdu,
    'Dis7ResupplyReceivedSemanticPdu': Dis7ResupplyReceivedSemanticPdu,
    'Dis7ResupplyCancelSemanticPdu': Dis7ResupplyCancelSemanticPdu,
    'Dis7RepairCompleteSemanticPdu': Dis7RepairCompleteSemanticPdu,
    'Dis7RepairResponseSemanticPdu': Dis7RepairResponseSemanticPdu,
    'Dis7CreateEntitySemanticPdu': Dis7CreateEntitySemanticPdu,
    'Dis7RemoveEntitySemanticPdu': Dis7RemoveEntitySemanticPdu,
    'Dis7StartResumeSemanticPdu': Dis7StartResumeSemanticPdu,
    'Dis7StopFreezeSemanticPdu': Dis7StopFreezeSemanticPdu,
    'Dis7AcknowledgeSemanticPdu': Dis7AcknowledgeSemanticPdu,
    'Dis7ActionRequestSemanticPdu': Dis7ActionRequestSemanticPdu,
    'Dis7ActionResponseSemanticPdu': Dis7ActionResponseSemanticPdu,
    'Dis7DataQuerySemanticPdu': Dis7DataQuerySemanticPdu,
    'Dis7SetDataSemanticPdu': Dis7SetDataSemanticPdu,
    'Dis7DataSemanticPdu': Dis7DataSemanticPdu,
    'Dis7EventReportSemanticPdu': Dis7EventReportSemanticPdu,
    'Dis7CommentSemanticPdu': Dis7CommentSemanticPdu,
    'Dis7ElectronicEmissionsSemanticPdu': Dis7ElectronicEmissionsSemanticPdu,
    'Dis7DesignatorSemanticPdu': Dis7DesignatorSemanticPdu,
    'Dis7TransmitterSemanticPdu': Dis7TransmitterSemanticPdu,
    'Dis7SignalSemanticPdu': Dis7SignalSemanticPdu,
    'Dis7ReceiverSemanticPdu': Dis7ReceiverSemanticPdu,
    'Dis7IffSemanticPdu': Dis7IffSemanticPdu,
    'Dis7UaSemanticPdu': Dis7UaSemanticPdu,
    'Dis7SEESSemanticPdu': Dis7SEESSemanticPdu,
    'Dis7IntercomSignalSemanticPdu': Dis7IntercomSignalSemanticPdu,
    'Dis7IntercomControlSemanticPdu': Dis7IntercomControlSemanticPdu,
    'Dis7AggregateStateSemanticPdu': Dis7AggregateStateSemanticPdu,
    'Dis7IsGroupOfSemanticPdu': Dis7IsGroupOfSemanticPdu,
    'Dis7TransferOwnershipSemanticPdu': Dis7TransferOwnershipSemanticPdu,
    'Dis7IsPartOfSemanticPdu': Dis7IsPartOfSemanticPdu,
    'Dis7MinefieldStateSemanticPdu': Dis7MinefieldStateSemanticPdu,
    'Dis7MinefieldQuerySemanticPdu': Dis7MinefieldQuerySemanticPdu,
    'Dis7MinefieldDataSemanticPdu': Dis7MinefieldDataSemanticPdu,
    'Dis7MinefieldResponseNackSemanticPdu': Dis7MinefieldResponseNackSemanticPdu,
    'Dis7EnvironmentalProcessSemanticPdu': Dis7EnvironmentalProcessSemanticPdu,
    'Dis7GriddedDataSemanticPdu': Dis7GriddedDataSemanticPdu,
    'Dis7PointObjectStateSemanticPdu': Dis7PointObjectStateSemanticPdu,
    'Dis7LinearObjectStateSemanticPdu': Dis7LinearObjectStateSemanticPdu,
    'Dis7ArealObjectStateSemanticPdu': Dis7ArealObjectStateSemanticPdu,
    'Dis7TSPISemanticPdu': Dis7TSPISemanticPdu,
    'Dis7AppearanceSemanticPdu': Dis7AppearanceSemanticPdu,
    'Dis7ArticulatedPartsSemanticPdu': Dis7ArticulatedPartsSemanticPdu,
    'Dis7LEFireSemanticPdu': Dis7LEFireSemanticPdu,
    'Dis7LEDetonationSemanticPdu': Dis7LEDetonationSemanticPdu,
    'Dis7CreateEntityReliableSemanticPdu': Dis7CreateEntityReliableSemanticPdu,
    'Dis7RemoveEntityReliableSemanticPdu': Dis7RemoveEntityReliableSemanticPdu,
    'Dis7StartResumeReliableSemanticPdu': Dis7StartResumeReliableSemanticPdu,
    'Dis7StopFreezeReliableSemanticPdu': Dis7StopFreezeReliableSemanticPdu,
    'Dis7AcknowledgeReliableSemanticPdu': Dis7AcknowledgeReliableSemanticPdu,
    'Dis7ActionRequestReliableSemanticPdu': Dis7ActionRequestReliableSemanticPdu,
    'Dis7ActionResponseReliableSemanticPdu': Dis7ActionResponseReliableSemanticPdu,
    'Dis7DataQueryReliableSemanticPdu': Dis7DataQueryReliableSemanticPdu,
    'Dis7SetDataReliableSemanticPdu': Dis7SetDataReliableSemanticPdu,
    'Dis7DataReliableSemanticPdu': Dis7DataReliableSemanticPdu,
    'Dis7EventReportReliableSemanticPdu': Dis7EventReportReliableSemanticPdu,
    'Dis7CommentReliableSemanticPdu': Dis7CommentReliableSemanticPdu,
    'Dis7RecordReliableSemanticPdu': Dis7RecordReliableSemanticPdu,
    'Dis7SetRecordReliableSemanticPdu': Dis7SetRecordReliableSemanticPdu,
    'Dis7RecordQueryReliableSemanticPdu': Dis7RecordQueryReliableSemanticPdu,
    'Dis7CollisionElasticSemanticPdu': Dis7CollisionElasticSemanticPdu,
    'Dis7EntityStateUpdateSemanticPdu': Dis7EntityStateUpdateSemanticPdu,
    'Dis7DirectedEnergyFireSemanticPdu': Dis7DirectedEnergyFireSemanticPdu,
    'Dis7EntityDamageStatusSemanticPdu': Dis7EntityDamageStatusSemanticPdu,
    'Dis7InformationOperationsActionSemanticPdu': Dis7InformationOperationsActionSemanticPdu,
    'Dis7InformationOperationsReportSemanticPdu': Dis7InformationOperationsReportSemanticPdu,
    'Dis7AttributeSemanticPdu': Dis7AttributeSemanticPdu,
}


def _entity_id(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    site, application, entity = struct.unpack_from('>HHH', body, offset)
    return ({'site': int(site), 'application': int(application), 'entity': int(entity)}, offset + 6)


def _event_id(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    site, application, event_number = struct.unpack_from('>HHH', body, offset)
    return ({'site': int(site), 'application': int(application), 'event_number': int(event_number)}, offset + 6)


def _entity_type(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    kind, domain, country, category, subcategory, specific, extra = struct.unpack_from('>BBHBBBB', body, offset)
    return ({'kind': int(kind), 'domain': int(domain), 'country': int(country), 'category': int(category), 'subcategory': int(subcategory), 'specific': int(specific), 'extra': int(extra)}, offset + 8)


def _decode_other_pdu(typed: TypedPdu) -> Mapping[str, object]:
    return MappingProxyType({'opaque_payload_bytes': typed.body})


def _supply_quantity(body: bytes, offset: int) -> tuple[dict[str, object], int]:
    supply_type, offset = _entity_type(body, offset)
    quantity = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    return ({'supply_type': supply_type, 'quantity': quantity}, offset)


def _simulation_address(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    site, application = struct.unpack_from('>HH', body, offset)
    return ({'site': int(site), 'application': int(application)}, offset + 4)


def _object_type_dis6(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    entity_kind, domain, country, category, subcategory = struct.unpack_from('>BBHBB', body, offset)
    return ({'entity_kind': int(entity_kind), 'domain': int(domain), 'country': int(country), 'category': int(category), 'subcategory': int(subcategory)}, offset + 6)


def _object_type_dis7(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    domain, object_kind, category, subcategory = struct.unpack_from('>BBBB', body, offset)
    return ({'domain': int(domain), 'object_kind': int(object_kind), 'category': int(category), 'subcategory': int(subcategory)}, offset + 4)


def _relationship(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    nature, position = struct.unpack_from('>HH', body, offset)
    return ({'nature': int(nature), 'position': int(position)}, offset + 4)


def _named_location(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    station_name, station_number = struct.unpack_from('>HH', body, offset)
    return ({'station_name': int(station_name), 'station_number': int(station_number)}, offset + 4)


def _minefield_identifier_dis7(body: bytes, offset: int) -> tuple[dict[str, object], int]:
    simulation_address, offset = _simulation_address(body, offset)
    minefield_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    return ({'simulation_address': simulation_address, 'minefield_number': minefield_number}, offset)


def _aggregate_id(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    site, application, aggregate_id = struct.unpack_from('>HHH', body, offset)
    return ({'site': int(site), 'application': int(application), 'aggregate_id': int(aggregate_id)}, offset + 6)


def _aggregate_marking(body: bytes, offset: int) -> tuple[dict[str, object], int]:
    character_set = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    characters = body[offset:offset + 31]
    if len(characters) != 31:
        raise ValueError('expected aggregate-marking bytes')
    offset += 31
    return ({'character_set': character_set, 'characters': characters}, offset)


def _eight_byte_chunks(body: bytes, offset: int, count: int) -> tuple[tuple[bytes, ...], int]:
    items = []
    for _ in range(count):
        item = body[offset:offset + 8]
        if len(item) != 8:
            raise ValueError('expected eight-byte chunk')
        items.append(item)
        offset += 8
    return (tuple(items), offset)


def _two_byte_chunks(body: bytes, offset: int, count: int) -> tuple[tuple[bytes, ...], int]:
    items = []
    for _ in range(count):
        item = body[offset:offset + 2]
        if len(item) != 2:
            raise ValueError('expected two-byte chunk')
        items.append(item)
        offset += 2
    return (tuple(items), offset)


def _linear_segment_parameter_dis6(body: bytes, offset: int) -> tuple[dict[str, object], int]:
    segment_number = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    segment_appearance = body[offset:offset + 6]
    offset += 6
    location, offset = _vec3d(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    segment_length, segment_width, segment_height, segment_depth, pad1 = struct.unpack_from('>HHHHI', body, offset)
    offset += 12
    return ({'segment_number': segment_number, 'segment_appearance': segment_appearance, 'location': location, 'orientation': orientation, 'segment_length': int(segment_length), 'segment_width': int(segment_width), 'segment_height': int(segment_height), 'segment_depth': int(segment_depth), 'pad1': int(pad1)}, offset)


def _linear_segment_parameter_dis7(body: bytes, offset: int) -> tuple[dict[str, object], int]:
    segment_number = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    segment_modification = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    general_segment_appearance = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    specific_segment_appearance = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    segment_location, offset = _vec3d(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    segment_orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    segment_length, segment_width, segment_height, segment_depth = struct.unpack_from('>ffff', body, offset)
    offset += 16
    padding = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    return ({'segment_number': segment_number, 'segment_modification': segment_modification, 'general_segment_appearance': general_segment_appearance, 'specific_segment_appearance': specific_segment_appearance, 'segment_location': segment_location, 'segment_orientation': segment_orientation, 'segment_length': float(segment_length), 'segment_width': float(segment_width), 'segment_height': float(segment_height), 'segment_depth': float(segment_depth), 'padding': padding}, offset)


def _vec3f(body: bytes, offset: int) -> tuple[dict[str, float], int]:
    x, y, z = struct.unpack_from('>fff', body, offset)
    return ({'x': float(x), 'y': float(y), 'z': float(z)}, offset + 12)


def _vec2f(body: bytes, offset: int) -> tuple[dict[str, float], int]:
    x, y = struct.unpack_from('>ff', body, offset)
    return ({'x': float(x), 'y': float(y)}, offset + 8)


def _vec3d(body: bytes, offset: int) -> tuple[dict[str, float], int]:
    x, y, z = struct.unpack_from('>ddd', body, offset)
    return ({'x': float(x), 'y': float(y), 'z': float(z)}, offset + 24)


def _clock_time(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    hour, time_past_hour = struct.unpack_from('>II', body, offset)
    return ({'hour': int(hour), 'time_past_hour': int(time_past_hour)}, offset + 8)


def _munition_descriptor(body: bytes, offset: int) -> tuple[dict[str, object], int]:
    munition_type, offset = _entity_type(body, offset)
    warhead, fuse, quantity, rate = struct.unpack_from('>HHHH', body, offset)
    return ({'munition_type': munition_type, 'warhead': int(warhead), 'fuse': int(fuse), 'quantity': int(quantity), 'rate': int(rate)}, offset + 8)


def _radio_entity_type(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    entity_kind, domain, country, category, nomenclature_version, nomenclature = struct.unpack_from('>BBHBBH', body, offset)
    return ({'entity_kind': int(entity_kind), 'domain': int(domain), 'country': int(country), 'category': int(category), 'nomenclature_version': int(nomenclature_version), 'nomenclature': int(nomenclature)}, offset + 8)


def _modulation_type_dis6(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    spread_spectrum, major, detail, system = struct.unpack_from('>HHHH', body, offset)
    return ({'spread_spectrum': int(spread_spectrum), 'major': int(major), 'detail': int(detail), 'system': int(system)}, offset + 8)


def _modulation_type_dis7(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    spread_spectrum, major_modulation, detail, radio_system = struct.unpack_from('>HHHH', body, offset)
    return ({'spread_spectrum': int(spread_spectrum), 'major_modulation': int(major_modulation), 'detail': int(detail), 'radio_system': int(radio_system)}, offset + 8)


def _decode_create_remove_entity(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
    })


def _decode_create_remove_entity_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'request_id': request_id,
    })


def _decode_start_resume(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    real_world_time, offset = _clock_time(body, offset)
    simulation_time, offset = _clock_time(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'real_world_time': real_world_time,
        'simulation_time': simulation_time,
        'request_id': request_id,
    })


def _decode_stop_freeze(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    real_world_time, offset = _clock_time(body, offset)
    reason = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    frozen_behavior = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'real_world_time': real_world_time,
        'reason': reason,
        'frozen_behavior': frozen_behavior,
        'padding1': padding1,
        'request_id': request_id,
    })


def _decode_acknowledge(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    acknowledge_flag = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    response_flag = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'acknowledge_flag': acknowledge_flag,
        'response_flag': response_flag,
        'request_id': request_id,
    })


def _decode_start_resume_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    real_world_time, offset = _clock_time(body, offset)
    simulation_time, offset = _clock_time(body, offset)
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'real_world_time': real_world_time,
        'simulation_time': simulation_time,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'request_id': request_id,
    })


def _decode_stop_freeze_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    real_world_time, offset = _clock_time(body, offset)
    reason = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    frozen_behavior = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    required_reliablity_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'real_world_time': real_world_time,
        'reason': reason,
        'frozen_behavior': frozen_behavior,
        'required_reliablity_service': required_reliablity_service,
        'pad1': pad1,
        'request_id': request_id,
    })


def _decode_acknowledge_reliable(typed: TypedPdu) -> Mapping[str, object]:
    return _decode_acknowledge(typed)


def _decode_action_request(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    action_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'action_id': action_id,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_action_response(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    request_status = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'request_status': request_status,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_action_request_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    action_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'request_id': request_id,
        'action_id': action_id,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_action_response_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    response_status = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'response_status': response_status,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_data_query(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    time_interval, offset = _clock_time(body, offset)
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'time_interval': time_interval,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_set_data(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    padding1 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'padding1': padding1,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_event_report(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    event_type = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    padding1 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'event_type': event_type,
        'padding1': padding1,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_comment(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_data_query_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    time_interval, offset = _clock_time(body, offset)
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'request_id': request_id,
        'time_interval': time_interval,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_set_data_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'request_id': request_id,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_data_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_event_report_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    event_type = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    pad1 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_fixed_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    datum_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'event_type': event_type,
        'pad1': pad1,
        'number_of_fixed_datum_records': number_of_fixed_datum_records,
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'datum_record_bytes': datum_record_bytes,
    })


def _decode_comment_reliable(typed: TypedPdu) -> Mapping[str, object]:
    return _decode_comment(typed)


def _decode_set_record_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_record_sets = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    record_set_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'number_of_record_sets': number_of_record_sets,
        'record_set_bytes': record_set_bytes,
    })


def _decode_record_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    event_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_record_sets = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    record_set_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'event_type': event_type,
        'number_of_record_sets': number_of_record_sets,
        'record_set_bytes': record_set_bytes,
    })


def _decode_information_operations_action_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_sim_id, offset = _entity_id(body, offset)
    receiving_sim_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    io_warfare_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    io_simulation_source = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    io_action_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    io_action_phase = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding1 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    io_attacker_id, offset = _entity_id(body, offset)
    io_primary_target_id, offset = _entity_id(body, offset)
    padding2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_io_records = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    io_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_sim_id': originating_sim_id,
        'receiving_sim_id': receiving_sim_id,
        'request_id': request_id,
        'io_warfare_type': io_warfare_type,
        'io_simulation_source': io_simulation_source,
        'io_action_type': io_action_type,
        'io_action_phase': io_action_phase,
        'padding1': padding1,
        'io_attacker_id': io_attacker_id,
        'io_primary_target_id': io_primary_target_id,
        'padding2': padding2,
        'number_of_io_records': number_of_io_records,
        'io_record_bytes': io_record_bytes,
    })


def _decode_information_operations_report_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_sim_id, offset = _entity_id(body, offset)
    io_sim_source = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    io_report_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding1 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    io_attacker_id, offset = _entity_id(body, offset)
    io_primary_target_id, offset = _entity_id(body, offset)
    padding2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding3 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_io_records = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    io_record_bytes = body[offset:]
    return MappingProxyType({
        'originating_sim_id': originating_sim_id,
        'io_sim_source': io_sim_source,
        'io_report_type': io_report_type,
        'padding1': padding1,
        'io_attacker_id': io_attacker_id,
        'io_primary_target_id': io_primary_target_id,
        'padding2': padding2,
        'padding3': padding3,
        'number_of_io_records': number_of_io_records,
        'io_record_bytes': io_record_bytes,
    })


def _decode_record_query_reliable(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    event_type = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    time, offset = _clock_time(body, offset)
    number_of_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    record_id_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'required_reliability_service': required_reliability_service,
        'pad1': pad1,
        'pad2': pad2,
        'event_type': event_type,
        'time': time,
        'number_of_records': number_of_records,
        'record_id_bytes': record_id_bytes,
    })


def _decode_attribute_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_simulation_address, offset = _simulation_address(body, offset)
    padding1 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    padding2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    attribute_record_pdu_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    attribute_record_protocol_version = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    master_attribute_record_type = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    action_code = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding3 = int(struct.unpack_from('>b', body, offset)[0])
    offset += 1
    number_attribute_record_set = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    attribute_record_sets_bytes = body[offset:]
    return MappingProxyType({
        'originating_simulation_address': originating_simulation_address,
        'padding1': padding1,
        'padding2': padding2,
        'attribute_record_pdu_type': attribute_record_pdu_type,
        'attribute_record_protocol_version': attribute_record_protocol_version,
        'master_attribute_record_type': master_attribute_record_type,
        'action_code': action_code,
        'padding3': padding3,
        'number_attribute_record_set': number_attribute_record_set,
        'attribute_record_sets_bytes': attribute_record_sets_bytes,
    })


def _decode_signal_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    entity_id, offset = _entity_id(body, offset)
    radio_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    encoding_scheme = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    tdl_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    sample_rate = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    data_length = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    samples = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    data_bytes = body[offset:]
    return MappingProxyType({
        'entity_id': entity_id,
        'radio_id': radio_id,
        'encoding_scheme': encoding_scheme,
        'tdl_type': tdl_type,
        'sample_rate': sample_rate,
        'data_length': data_length,
        'samples': samples,
        'data_bytes': data_bytes,
    })


def _decode_signal_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    encoding_scheme = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    tdl_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    sample_rate = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    data_length = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    samples = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    data_bytes = body[offset:]
    return MappingProxyType({
        'encoding_scheme': encoding_scheme,
        'tdl_type': tdl_type,
        'sample_rate': sample_rate,
        'data_length': data_length,
        'samples': samples,
        'data_bytes': data_bytes,
    })


def _decode_intercom_signal_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    entity_id, offset = _entity_id(body, offset)
    communications_device_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    encoding_scheme = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    tdl_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    sample_rate = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    data_length = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    samples = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    data_bytes = body[offset:]
    return MappingProxyType({
        'entity_id': entity_id,
        'communications_device_id': communications_device_id,
        'encoding_scheme': encoding_scheme,
        'tdl_type': tdl_type,
        'sample_rate': sample_rate,
        'data_length': data_length,
        'samples': samples,
        'data_bytes': data_bytes,
    })


def _decode_intercom_signal_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    entity_id, offset = _entity_id(body, offset)
    communications_device_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    encoding_scheme = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    tdl_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    sample_rate = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    data_length = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    samples = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    data_bytes = body[offset:]
    return MappingProxyType({
        'entity_id': entity_id,
        'communications_device_id': communications_device_id,
        'encoding_scheme': encoding_scheme,
        'tdl_type': tdl_type,
        'sample_rate': sample_rate,
        'data_length': data_length,
        'samples': samples,
        'data_bytes': data_bytes,
    })


def _decode_intercom_control(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    control_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    communications_channel_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    source_entity_id, offset = _entity_id(body, offset)
    source_communications_device_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    source_line_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    transmit_priority = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    transmit_line_state = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    command = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    master_entity_id, offset = _entity_id(body, offset)
    master_communications_device_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    intercom_parameters_length = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    intercom_parameters_bytes = body[offset:]
    return MappingProxyType({
        'control_type': control_type,
        'communications_channel_type': communications_channel_type,
        'source_entity_id': source_entity_id,
        'source_communications_device_id': source_communications_device_id,
        'source_line_id': source_line_id,
        'transmit_priority': transmit_priority,
        'transmit_line_state': transmit_line_state,
        'command': command,
        'master_entity_id': master_entity_id,
        'master_communications_device_id': master_communications_device_id,
        'intercom_parameters_length': intercom_parameters_length,
        'intercom_parameters_bytes': intercom_parameters_bytes,
    })


def _decode_receiver_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    entity_id, offset = _entity_id(body, offset)
    radio_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    receiver_state = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    received_power = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    transmitter_entity_id, offset = _entity_id(body, offset)
    transmitter_radio_id = int(struct.unpack_from('>H', body, offset)[0])
    return MappingProxyType({
        'entity_id': entity_id,
        'radio_id': radio_id,
        'receiver_state': receiver_state,
        'padding1': padding1,
        'received_power': received_power,
        'transmitter_entity_id': transmitter_entity_id,
        'transmitter_radio_id': transmitter_radio_id,
    })


def _decode_receiver_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    receiver_state = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    received_power = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    transmitter_entity_id, offset = _entity_id(body, offset)
    transmitter_radio_id = int(struct.unpack_from('>H', body, offset)[0])
    return MappingProxyType({
        'receiver_state': receiver_state,
        'padding1': padding1,
        'received_power': received_power,
        'transmitter_entity_id': transmitter_entity_id,
        'transmitter_radio_id': transmitter_radio_id,
    })


def _decode_transmitter_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    entity_id, offset = _entity_id(body, offset)
    radio_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    radio_entity_type, offset = _radio_entity_type(body, offset)
    transmit_state = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    input_source = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    antenna_location, offset = _vec3d(body, offset)
    relative_antenna_location, offset = _vec3f(body, offset)
    antenna_pattern_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    antenna_pattern_count = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    frequency = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    transmit_frequency_bandwidth = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    power = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    modulation_type, offset = _modulation_type_dis6(body, offset)
    crypto_system = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    crypto_key_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    modulation_parameter_count = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding3 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    variable_payload_bytes = body[offset:]
    return MappingProxyType({
        'entity_id': entity_id,
        'radio_id': radio_id,
        'radio_entity_type': radio_entity_type,
        'transmit_state': transmit_state,
        'input_source': input_source,
        'padding1': padding1,
        'antenna_location': antenna_location,
        'relative_antenna_location': relative_antenna_location,
        'antenna_pattern_type': antenna_pattern_type,
        'antenna_pattern_count': antenna_pattern_count,
        'frequency': frequency,
        'transmit_frequency_bandwidth': transmit_frequency_bandwidth,
        'power': power,
        'modulation_type': modulation_type,
        'crypto_system': crypto_system,
        'crypto_key_id': crypto_key_id,
        'modulation_parameter_count': modulation_parameter_count,
        'padding2': padding2,
        'padding3': padding3,
        'variable_payload_bytes': variable_payload_bytes,
    })


def _decode_transmitter_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    radio_reference_id, offset = _entity_id(body, offset)
    radio_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    radio_entity_type, offset = _entity_type(body, offset)
    transmit_state = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    input_source = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    variable_transmitter_parameter_count = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    antenna_location, offset = _vec3d(body, offset)
    relative_antenna_location, offset = _vec3f(body, offset)
    antenna_pattern_type = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    antenna_pattern_count = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    frequency = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    transmit_frequency_bandwidth = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    power = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    modulation_type, offset = _modulation_type_dis7(body, offset)
    crypto_system = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    crypto_key_id = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    modulation_parameter_count = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding3 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    variable_payload_bytes = body[offset:]
    return MappingProxyType({
        'radio_reference_id': radio_reference_id,
        'radio_number': radio_number,
        'radio_entity_type': radio_entity_type,
        'transmit_state': transmit_state,
        'input_source': input_source,
        'variable_transmitter_parameter_count': variable_transmitter_parameter_count,
        'antenna_location': antenna_location,
        'relative_antenna_location': relative_antenna_location,
        'antenna_pattern_type': antenna_pattern_type,
        'antenna_pattern_count': antenna_pattern_count,
        'frequency': frequency,
        'transmit_frequency_bandwidth': transmit_frequency_bandwidth,
        'power': power,
        'modulation_type': modulation_type,
        'crypto_system': crypto_system,
        'crypto_key_id': crypto_key_id,
        'modulation_parameter_count': modulation_parameter_count,
        'padding2': padding2,
        'padding3': padding3,
        'variable_payload_bytes': variable_payload_bytes,
    })


def _decode_designator(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    designating_entity_id, offset = _entity_id(body, offset)
    code_name = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    designated_entity_id, offset = _entity_id(body, offset)
    designator_code = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    designator_power = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    designator_wavelength = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    designator_spot_wrt_designated, offset = _vec3f(body, offset)
    designator_spot_location, offset = _vec3d(body, offset)
    dead_reckoning_algorithm = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    entity_linear_acceleration, offset = _vec3f(body, offset)
    return MappingProxyType({
        'designating_entity_id': designating_entity_id,
        'code_name': code_name,
        'designated_entity_id': designated_entity_id,
        'designator_code': designator_code,
        'designator_power': designator_power,
        'designator_wavelength': designator_wavelength,
        'designator_spot_wrt_designated': designator_spot_wrt_designated,
        'designator_spot_location': designator_spot_location,
        'dead_reckoning_algorithm': dead_reckoning_algorithm,
        'padding1': padding1,
        'padding2': padding2,
        'entity_linear_acceleration': entity_linear_acceleration,
    })


def _decode_emitter_system_dis6(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    emitter_name, function, emitter_id_number = struct.unpack_from('>HBB', body, offset)
    return ({'emitter_name': int(emitter_name), 'function': int(function), 'emitter_id_number': int(emitter_id_number)}, offset + 4)


def _decode_emitter_system_dis7(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    emitter_name, emitter_function, emitter_id_number = struct.unpack_from('>HBB', body, offset)
    return ({'emitter_name': int(emitter_name), 'emitter_function': int(emitter_function), 'emitter_id_number': int(emitter_id_number)}, offset + 4)


def _decode_system_id_dis6(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    system_type, system_name, system_mode, change_options = struct.unpack_from('>HHBB', body, offset)
    return ({'system_type': int(system_type), 'system_name': int(system_name), 'system_mode': int(system_mode), 'change_options': int(change_options)}, offset + 6)


def _decode_system_identifier_dis7(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    system_type, system_name, system_mode, change_options = struct.unpack_from('>HHBB', body, offset)
    return ({'system_type': int(system_type), 'system_name': int(system_name), 'system_mode': int(system_mode), 'change_options': int(change_options)}, offset + 6)


def _decode_iff_fundamental_data_dis6(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    system_status, alternate_parameter4, information_layers, modifier = struct.unpack_from('>BBBB', body, offset)
    offset += 4
    parameter1, parameter2, parameter3, parameter4, parameter5, parameter6 = struct.unpack_from('>HHHHHH', body, offset)
    offset += 12
    return ({'system_status': int(system_status), 'alternate_parameter4': int(alternate_parameter4), 'information_layers': int(information_layers), 'modifier': int(modifier), 'parameter1': int(parameter1), 'parameter2': int(parameter2), 'parameter3': int(parameter3), 'parameter4': int(parameter4), 'parameter5': int(parameter5), 'parameter6': int(parameter6)}, offset)


def _decode_fundamental_operational_data_dis7(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    system_status, data_field1, information_layers, data_field2 = struct.unpack_from('>BBBB', body, offset)
    offset += 4
    parameter1, parameter2, parameter3, parameter4, parameter5, parameter6 = struct.unpack_from('>HHHHHH', body, offset)
    offset += 12
    return ({'system_status': int(system_status), 'data_field1': int(data_field1), 'information_layers': int(information_layers), 'data_field2': int(data_field2), 'parameter1': int(parameter1), 'parameter2': int(parameter2), 'parameter3': int(parameter3), 'parameter4': int(parameter4), 'parameter5': int(parameter5), 'parameter6': int(parameter6)}, offset)


def _decode_shaft_rpms_dis6(body: bytes, offset: int) -> tuple[dict[str, float], int]:
    current_shaft_rpms, ordered_shaft_rpms = struct.unpack_from('>hh', body, offset)
    offset += 4
    shaft_rpm_rate_of_change = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    return ({'current_shaft_rpms': int(current_shaft_rpms), 'ordered_shaft_rpms': int(ordered_shaft_rpms), 'shaft_rpm_rate_of_change': shaft_rpm_rate_of_change}, offset)


def _decode_apa_data_dis6(body: bytes, offset: int) -> tuple[dict[str, int], int]:
    parameter_index = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    parameter_value = int(struct.unpack_from('>h', body, offset)[0])
    offset += 2
    return ({'parameter_index': parameter_index, 'parameter_value': parameter_value}, offset)


def _decode_electromagnetic_emission_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    emitting_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    state_update_indicator = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_systems = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding_for_emissions_pdu = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    systems_bytes = body[offset:]
    return MappingProxyType({
        'emitting_entity_id': emitting_entity_id,
        'event_id': event_id,
        'state_update_indicator': state_update_indicator,
        'number_of_systems': number_of_systems,
        'padding_for_emissions_pdu': padding_for_emissions_pdu,
        'systems_bytes': systems_bytes,
    })


def _decode_electromagnetic_emission_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    emitting_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    state_update_indicator = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_systems = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding_for_emissions_pdu = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    system_data_length = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_beams = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    emitter_system, offset = _decode_emitter_system_dis7(body, offset)
    location, offset = _vec3f(body, offset)
    systems_bytes = body[offset:]
    return MappingProxyType({
        'emitting_entity_id': emitting_entity_id,
        'event_id': event_id,
        'state_update_indicator': state_update_indicator,
        'number_of_systems': number_of_systems,
        'padding_for_emissions_pdu': padding_for_emissions_pdu,
        'system_data_length': system_data_length,
        'number_of_beams': number_of_beams,
        'emitter_system': emitter_system,
        'location': location,
        'systems_bytes': systems_bytes,
    })


def _decode_iff_atc_navaids_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    emitting_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    location, offset = _vec3f(body, offset)
    system_id, offset = _decode_system_id_dis6(body, offset)
    pad2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    fundamental_parameters, offset = _decode_iff_fundamental_data_dis6(body, offset)
    return MappingProxyType({
        'emitting_entity_id': emitting_entity_id,
        'event_id': event_id,
        'location': location,
        'system_id': system_id,
        'pad2': pad2,
        'fundamental_parameters': fundamental_parameters,
    })


def _decode_iff_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    emitting_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    location, offset = _vec3f(body, offset)
    system_id, offset = _decode_system_identifier_dis7(body, offset)
    pad2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    fundamental_parameters, offset = _decode_fundamental_operational_data_dis7(body, offset)
    return MappingProxyType({
        'emitting_entity_id': emitting_entity_id,
        'event_id': event_id,
        'location': location,
        'system_id': system_id,
        'pad2': pad2,
        'fundamental_parameters': fundamental_parameters,
    })


def _decode_tspi_live_entity(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    live_entity_id, offset = _entity_id(body, offset)
    tspi_flag = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    live_entity_state_bytes = body[offset:]
    return MappingProxyType({
        'live_entity_id': live_entity_id,
        'tspi_flag': tspi_flag,
        'live_entity_state_bytes': live_entity_state_bytes,
    })


def _decode_live_entity_appearance(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    live_entity_id, offset = _entity_id(body, offset)
    appearance_flags = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    appearance_payload_bytes = body[offset:]
    return MappingProxyType({
        'live_entity_id': live_entity_id,
        'appearance_flags': appearance_flags,
        'force_id': force_id,
        'appearance_payload_bytes': appearance_payload_bytes,
    })


def _decode_live_entity_articulated_parts(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    live_entity_id, offset = _entity_id(body, offset)
    number_of_parameter_records = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    variable_parameter_bytes = body[offset:]
    return MappingProxyType({
        'live_entity_id': live_entity_id,
        'number_of_parameter_records': number_of_parameter_records,
        'variable_parameter_bytes': variable_parameter_bytes,
    })


def _decode_live_entity_fire(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    firing_live_entity_id, offset = _entity_id(body, offset)
    flags = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    target_live_entity_id, offset = _entity_id(body, offset)
    munition_live_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    live_entity_fire_bytes = body[offset:]
    return MappingProxyType({
        'firing_live_entity_id': firing_live_entity_id,
        'flags': flags,
        'target_live_entity_id': target_live_entity_id,
        'munition_live_entity_id': munition_live_entity_id,
        'event_id': event_id,
        'live_entity_fire_bytes': live_entity_fire_bytes,
    })


def _decode_live_entity_detonation(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    firing_live_entity_id, offset = _entity_id(body, offset)
    detonation_flag1 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    detonation_flag2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    target_live_entity_id, offset = _entity_id(body, offset)
    munition_live_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    live_entity_detonation_bytes = body[offset:]
    return MappingProxyType({
        'firing_live_entity_id': firing_live_entity_id,
        'detonation_flag1': detonation_flag1,
        'detonation_flag2': detonation_flag2,
        'target_live_entity_id': target_live_entity_id,
        'munition_live_entity_id': munition_live_entity_id,
        'event_id': event_id,
        'live_entity_detonation_bytes': live_entity_detonation_bytes,
    })


def _decode_service_request(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    requesting_entity_id, offset = _entity_id(body, offset)
    servicing_entity_id, offset = _entity_id(body, offset)
    service_type_requested = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_supply_types = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    service_request_padding = int(struct.unpack_from('>h', body, offset)[0])
    offset += 2
    supplies = []
    for _ in range(number_of_supply_types):
        item, offset = _supply_quantity(body, offset)
        supplies.append(item)
    return MappingProxyType({
        'requesting_entity_id': requesting_entity_id,
        'servicing_entity_id': servicing_entity_id,
        'service_type_requested': service_type_requested,
        'number_of_supply_types': number_of_supply_types,
        'service_request_padding': service_request_padding,
        'supplies': tuple(supplies),
    })


def _decode_resupply_offer_or_received(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    receiving_entity_id, offset = _entity_id(body, offset)
    supplying_entity_id, offset = _entity_id(body, offset)
    number_of_supply_types = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    next_three = body[offset:offset + 3]
    if len(next_three) != 3:
        raise ValueError('expected logistics padding bytes')
    padding_short_be = int(struct.unpack('>h', next_three[:2])[0])
    padding_short_tail = int(struct.unpack('>h', next_three[1:])[0])
    if next_three[2] == 0 and padding_short_be == 0:
        padding1 = padding_short_be
        padding2 = int(next_three[2])
    else:
        padding1 = int(next_three[0])
        padding2 = padding_short_tail
    offset += 3
    supplies = []
    for _ in range(number_of_supply_types):
        item, offset = _supply_quantity(body, offset)
        supplies.append(item)
    return MappingProxyType({
        'receiving_entity_id': receiving_entity_id,
        'supplying_entity_id': supplying_entity_id,
        'number_of_supply_types': number_of_supply_types,
        'padding1': padding1,
        'padding2': padding2,
        'supplies': tuple(supplies),
    })


def _decode_resupply_cancel(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    receiving_entity_id, offset = _entity_id(body, offset)
    supplying_entity_id, offset = _entity_id(body, offset)
    return MappingProxyType({
        'receiving_entity_id': receiving_entity_id,
        'supplying_entity_id': supplying_entity_id,
    })


def _decode_repair_complete(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    receiving_entity_id, offset = _entity_id(body, offset)
    repairing_entity_id, offset = _entity_id(body, offset)
    repair = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding = int(struct.unpack_from('>h', body, offset)[0])
    offset += 2
    return MappingProxyType({
        'receiving_entity_id': receiving_entity_id,
        'repairing_entity_id': repairing_entity_id,
        'repair': repair,
        'padding': padding,
    })


def _decode_repair_response(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    receiving_entity_id, offset = _entity_id(body, offset)
    repairing_entity_id, offset = _entity_id(body, offset)
    repair_result = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    next_three = body[offset:offset + 3]
    if len(next_three) != 3:
        raise ValueError('expected repair-response padding bytes')
    if next_three[2] == 0:
        padding1 = int(struct.unpack('>h', next_three[:2])[0])
        padding2 = int(next_three[2])
    else:
        padding1 = int(next_three[0])
        padding2 = int(struct.unpack('>h', next_three[1:])[0])
    offset += 3
    return MappingProxyType({
        'receiving_entity_id': receiving_entity_id,
        'repairing_entity_id': repairing_entity_id,
        'repair_result': repair_result,
        'padding1': padding1,
        'padding2': padding2,
    })


def _decode_is_group_of_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    group_entity_id, offset = _entity_id(body, offset)
    grouped_entity_category = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_grouped_entities = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad2 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    latitude = float(struct.unpack_from('>d', body, offset)[0])
    offset += 8
    longitude = float(struct.unpack_from('>d', body, offset)[0])
    offset += 8
    grouped_entity_descriptions_bytes = body[offset:]
    return MappingProxyType({
        'group_entity_id': group_entity_id,
        'grouped_entity_category': grouped_entity_category,
        'number_of_grouped_entities': number_of_grouped_entities,
        'pad2': pad2,
        'latitude': latitude,
        'longitude': longitude,
        'grouped_entity_descriptions_bytes': grouped_entity_descriptions_bytes,
    })


def _decode_aggregate_state_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    aggregate_id, offset = _aggregate_id(body, offset)
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    aggregate_state = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    aggregate_type, offset = _entity_type(body, offset)
    formation = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    aggregate_marking, offset = _aggregate_marking(body, offset)
    dimensions, offset = _vec3f(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    center_of_mass, offset = _vec3d(body, offset)
    velocity, offset = _vec3f(body, offset)
    number_of_dis_aggregates = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_dis_entities = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_silent_aggregate_types = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_silent_entity_types = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    aggregate_id_list = []
    for _ in range(number_of_dis_aggregates):
        item, offset = _aggregate_id(body, offset)
        aggregate_id_list.append(item)
    entity_id_list = []
    for _ in range(number_of_dis_entities):
        item, offset = _entity_id(body, offset)
        entity_id_list.append(item)
    aligned_offset = (offset + 3) & ~3
    pad2_bytes = body[offset:aligned_offset]
    offset = aligned_offset
    silent_aggregate_system_list = []
    for _ in range(number_of_silent_aggregate_types):
        item, offset = _entity_type(body, offset)
        silent_aggregate_system_list.append(item)
    silent_entity_system_list = []
    for _ in range(number_of_silent_entity_types):
        item, offset = _entity_type(body, offset)
        silent_entity_system_list.append(item)
    number_of_variable_datum_records = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    variable_datum_bytes = body[offset:]
    return MappingProxyType({
        'aggregate_id': aggregate_id,
        'force_id': force_id,
        'aggregate_state': aggregate_state,
        'aggregate_type': aggregate_type,
        'formation': formation,
        'aggregate_marking': aggregate_marking,
        'dimensions': dimensions,
        'orientation': orientation,
        'center_of_mass': center_of_mass,
        'velocity': velocity,
        'number_of_dis_aggregates': number_of_dis_aggregates,
        'number_of_dis_entities': number_of_dis_entities,
        'number_of_silent_aggregate_types': number_of_silent_aggregate_types,
        'number_of_silent_entity_types': number_of_silent_entity_types,
        'aggregate_id_list': tuple(aggregate_id_list),
        'entity_id_list': tuple(entity_id_list),
        'pad2_bytes': pad2_bytes,
        'silent_aggregate_system_list': tuple(silent_aggregate_system_list),
        'silent_entity_system_list': tuple(silent_entity_system_list),
        'number_of_variable_datum_records': number_of_variable_datum_records,
        'variable_datum_bytes': variable_datum_bytes,
    })


def _decode_transfer_control_request(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    required_reliability_service = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    transfer_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    transfer_entity_id, offset = _entity_id(body, offset)
    number_of_record_sets = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    record_sets_bytes = body[offset:]
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'request_id': request_id,
        'required_reliability_service': required_reliability_service,
        'transfer_type': transfer_type,
        'transfer_entity_id': transfer_entity_id,
        'number_of_record_sets': number_of_record_sets,
        'record_sets_bytes': record_sets_bytes,
    })


def _decode_is_part_of(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    originating_entity_id, offset = _entity_id(body, offset)
    receiving_entity_id, offset = _entity_id(body, offset)
    relationship, offset = _relationship(body, offset)
    part_location, offset = _vec3f(body, offset)
    named_location_id, offset = _named_location(body, offset)
    part_entity_type, offset = _entity_type(body, offset)
    return MappingProxyType({
        'originating_entity_id': originating_entity_id,
        'receiving_entity_id': receiving_entity_id,
        'relationship': relationship,
        'part_location': part_location,
        'named_location_id': named_location_id,
        'part_entity_type': part_entity_type,
    })


def _decode_minefield_response_nack(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    minefield_id, offset = _entity_id(body, offset)
    requesting_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_missing_pdus = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    missing_pdu_sequence_numbers, offset = _eight_byte_chunks(body, offset, number_of_missing_pdus)
    return MappingProxyType({
        'minefield_id': minefield_id,
        'requesting_entity_id': requesting_entity_id,
        'request_id': request_id,
        'number_of_missing_pdus': number_of_missing_pdus,
        'missing_pdu_sequence_numbers': missing_pdu_sequence_numbers,
    })


def _decode_minefield_state_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    minefield_id, offset = _entity_id(body, offset)
    minefield_sequence = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_perimeter_points = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    minefield_type, offset = _entity_type(body, offset)
    number_of_mine_types = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    minefield_location, offset = _vec3d(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    minefield_orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    appearance = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    protocol_mode = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    perimeter_points = []
    for _ in range(number_of_perimeter_points):
        point, offset = _vec2f(body, offset)
        perimeter_points.append(point)
    mine_types = []
    for _ in range(number_of_mine_types):
        mine_type, offset = _entity_type(body, offset)
        mine_types.append(mine_type)
    return MappingProxyType({
        'minefield_id': minefield_id,
        'minefield_sequence': minefield_sequence,
        'force_id': force_id,
        'number_of_perimeter_points': number_of_perimeter_points,
        'minefield_type': minefield_type,
        'number_of_mine_types': number_of_mine_types,
        'minefield_location': minefield_location,
        'minefield_orientation': minefield_orientation,
        'appearance': appearance,
        'protocol_mode': protocol_mode,
        'perimeter_points': tuple(perimeter_points),
        'mine_types': tuple(mine_types),
    })


def _decode_minefield_query_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    minefield_id, offset = _entity_id(body, offset)
    requesting_entity_id, offset = _entity_id(body, offset)
    request_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_perimeter_points = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_sensor_types = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    data_filter = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    requested_mine_type, offset = _entity_type(body, offset)
    requested_perimeter_points = []
    for _ in range(number_of_perimeter_points):
        point, offset = _vec2f(body, offset)
        requested_perimeter_points.append(point)
    sensor_types, offset = _two_byte_chunks(body, offset, number_of_sensor_types)
    return MappingProxyType({
        'minefield_id': minefield_id,
        'requesting_entity_id': requesting_entity_id,
        'request_id': request_id,
        'number_of_perimeter_points': number_of_perimeter_points,
        'pad2': pad2,
        'number_of_sensor_types': number_of_sensor_types,
        'data_filter': data_filter,
        'requested_mine_type': requested_mine_type,
        'requested_perimeter_points': tuple(requested_perimeter_points),
        'sensor_types': sensor_types,
    })


def _decode_minefield_data_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    minefield_id, offset = _entity_id(body, offset)
    requesting_entity_id, offset = _entity_id(body, offset)
    minefield_sequence_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    request_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pdu_sequence_number = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_pdus = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_mines_in_this_pdu = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_sensor_types = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    data_filter = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    mine_type, offset = _entity_type(body, offset)
    sensor_types, offset = _two_byte_chunks(body, offset, number_of_sensor_types)
    pad3 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    mine_locations = []
    for _ in range(number_of_mines_in_this_pdu):
        location, offset = _vec3f(body, offset)
        mine_locations.append(location)
    return MappingProxyType({
        'minefield_id': minefield_id,
        'requesting_entity_id': requesting_entity_id,
        'minefield_sequence_number': minefield_sequence_number,
        'request_id': request_id,
        'pdu_sequence_number': pdu_sequence_number,
        'number_of_pdus': number_of_pdus,
        'number_of_mines_in_this_pdu': number_of_mines_in_this_pdu,
        'number_of_sensor_types': number_of_sensor_types,
        'pad2': pad2,
        'data_filter': data_filter,
        'mine_type': mine_type,
        'sensor_types': sensor_types,
        'pad3': pad3,
        'mine_locations': tuple(mine_locations),
    })


def _decode_minefield_state_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    minefield_id, offset = _minefield_identifier_dis7(body, offset)
    minefield_sequence = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_perimeter_points = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    minefield_type, offset = _entity_type(body, offset)
    number_of_mine_types = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    minefield_location, offset = _vec3d(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    minefield_orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    appearance = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    protocol_mode = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    perimeter_points = []
    for _ in range(number_of_perimeter_points):
        point, offset = _vec2f(body, offset)
        perimeter_points.append(point)
    mine_types = []
    for _ in range(number_of_mine_types):
        mine_type, offset = _entity_type(body, offset)
        mine_types.append(mine_type)
    return MappingProxyType({
        'minefield_id': minefield_id,
        'minefield_sequence': minefield_sequence,
        'force_id': force_id,
        'number_of_perimeter_points': number_of_perimeter_points,
        'minefield_type': minefield_type,
        'number_of_mine_types': number_of_mine_types,
        'minefield_location': minefield_location,
        'minefield_orientation': minefield_orientation,
        'appearance': appearance,
        'protocol_mode': protocol_mode,
        'perimeter_points': tuple(perimeter_points),
        'mine_types': tuple(mine_types),
    })


def _decode_environmental_process_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    environmental_process_id, offset = _entity_id(body, offset)
    environment_type, offset = _entity_type(body, offset)
    model_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    environment_status = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_environment_records = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    sequence_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    environment_records_bytes = body[offset:]
    return MappingProxyType({
        'environmental_process_id': environmental_process_id,
        'environment_type': environment_type,
        'model_type': model_type,
        'environment_status': environment_status,
        'number_of_environment_records': number_of_environment_records,
        'sequence_number': sequence_number,
        'environment_records_bytes': environment_records_bytes,
    })


def _decode_gridded_data_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    environmental_simulation_application_id, offset = _entity_id(body, offset)
    field_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pdu_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    pdu_total = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    coordinate_system = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_grid_axes = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    constant_grid = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    environment_type, offset = _entity_type(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    sample_time = int(struct.unpack_from('>q', body, offset)[0])
    offset += 8
    total_values = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    vector_dimension = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding2 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    grid_data_bytes = body[offset:]
    return MappingProxyType({
        'environmental_simulation_application_id': environmental_simulation_application_id,
        'field_number': field_number,
        'pdu_number': pdu_number,
        'pdu_total': pdu_total,
        'coordinate_system': coordinate_system,
        'number_of_grid_axes': number_of_grid_axes,
        'constant_grid': constant_grid,
        'environment_type': environment_type,
        'orientation': orientation,
        'sample_time': sample_time,
        'total_values': total_values,
        'vector_dimension': vector_dimension,
        'padding1': padding1,
        'padding2': padding2,
        'grid_data_bytes': grid_data_bytes,
    })


def _decode_point_object_state_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    object_id, offset = _entity_id(body, offset)
    referenced_object_id, offset = _entity_id(body, offset)
    update_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    modifications = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    object_type, offset = _object_type_dis6(body, offset)
    object_location, offset = _vec3d(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    object_orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    object_appearance = float(struct.unpack_from('>d', body, offset)[0])
    offset += 8
    requester_id, offset = _simulation_address(body, offset)
    receiving_id, offset = _simulation_address(body, offset)
    pad2 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    return MappingProxyType({
        'object_id': object_id,
        'referenced_object_id': referenced_object_id,
        'update_number': update_number,
        'force_id': force_id,
        'modifications': modifications,
        'object_type': object_type,
        'object_location': object_location,
        'object_orientation': object_orientation,
        'object_appearance': object_appearance,
        'requester_id': requester_id,
        'receiving_id': receiving_id,
        'pad2': pad2,
    })


def _decode_point_object_state_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    object_id, offset = _entity_id(body, offset)
    referenced_object_id, offset = _entity_id(body, offset)
    update_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    modifications = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    object_type, offset = _object_type_dis7(body, offset)
    object_location, offset = _vec3d(body, offset)
    psi, theta, phi = struct.unpack_from('>fff', body, offset)
    object_orientation = {'psi': float(psi), 'theta': float(theta), 'phi': float(phi)}
    offset += 12
    object_appearance = float(struct.unpack_from('>d', body, offset)[0])
    offset += 8
    requester_id, offset = _simulation_address(body, offset)
    receiving_id, offset = _simulation_address(body, offset)
    pad2 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    return MappingProxyType({
        'object_id': object_id,
        'referenced_object_id': referenced_object_id,
        'update_number': update_number,
        'force_id': force_id,
        'modifications': modifications,
        'object_type': object_type,
        'object_location': object_location,
        'object_orientation': object_orientation,
        'object_appearance': object_appearance,
        'requester_id': requester_id,
        'receiving_id': receiving_id,
        'pad2': pad2,
    })


def _decode_linear_object_state_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    object_id, offset = _entity_id(body, offset)
    referenced_object_id, offset = _entity_id(body, offset)
    update_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_segments = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    requester_id, offset = _simulation_address(body, offset)
    receiving_id, offset = _simulation_address(body, offset)
    object_type, offset = _object_type_dis6(body, offset)
    linear_segment_parameters = []
    for _ in range(number_of_segments):
        segment, offset = _linear_segment_parameter_dis6(body, offset)
        linear_segment_parameters.append(segment)
    return MappingProxyType({
        'object_id': object_id,
        'referenced_object_id': referenced_object_id,
        'update_number': update_number,
        'force_id': force_id,
        'number_of_segments': number_of_segments,
        'requester_id': requester_id,
        'receiving_id': receiving_id,
        'object_type': object_type,
        'linear_segment_parameters': tuple(linear_segment_parameters),
    })


def _decode_linear_object_state_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    object_id, offset = _entity_id(body, offset)
    referenced_object_id, offset = _entity_id(body, offset)
    update_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_segments = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    requester_id, offset = _simulation_address(body, offset)
    receiving_id, offset = _simulation_address(body, offset)
    object_type, offset = _object_type_dis7(body, offset)
    linear_segment_parameters = []
    for _ in range(number_of_segments):
        segment, offset = _linear_segment_parameter_dis7(body, offset)
        linear_segment_parameters.append(segment)
    return MappingProxyType({
        'object_id': object_id,
        'referenced_object_id': referenced_object_id,
        'update_number': update_number,
        'force_id': force_id,
        'number_of_segments': number_of_segments,
        'requester_id': requester_id,
        'receiving_id': receiving_id,
        'object_type': object_type,
        'linear_segment_parameters': tuple(linear_segment_parameters),
    })


def _decode_areal_object_state_dis6(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    object_id, offset = _entity_id(body, offset)
    referenced_object_id, offset = _entity_id(body, offset)
    update_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    modifications = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    object_type, offset = _entity_type(body, offset)
    object_appearance = body[offset:offset + 6]
    offset += 6
    number_of_points = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    requester_id, offset = _simulation_address(body, offset)
    receiving_id, offset = _simulation_address(body, offset)
    object_locations = []
    for _ in range(number_of_points):
        point, offset = _vec3d(body, offset)
        object_locations.append(point)
    return MappingProxyType({
        'object_id': object_id,
        'referenced_object_id': referenced_object_id,
        'update_number': update_number,
        'force_id': force_id,
        'modifications': modifications,
        'object_type': object_type,
        'object_appearance': object_appearance,
        'number_of_points': number_of_points,
        'requester_id': requester_id,
        'receiving_id': receiving_id,
        'object_locations': tuple(object_locations),
    })


def _decode_areal_object_state_dis7(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    object_id, offset = _entity_id(body, offset)
    referenced_object_id, offset = _entity_id(body, offset)
    update_number = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    force_id = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    modifications = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    object_type, offset = _entity_type(body, offset)
    specific_object_appearance = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    general_object_appearance = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_points = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    requester_id, offset = _simulation_address(body, offset)
    receiving_id, offset = _simulation_address(body, offset)
    object_locations = []
    for _ in range(number_of_points):
        point, offset = _vec3d(body, offset)
        object_locations.append(point)
    return MappingProxyType({
        'object_id': object_id,
        'referenced_object_id': referenced_object_id,
        'update_number': update_number,
        'force_id': force_id,
        'modifications': modifications,
        'object_type': object_type,
        'specific_object_appearance': specific_object_appearance,
        'general_object_appearance': general_object_appearance,
        'number_of_points': number_of_points,
        'requester_id': requester_id,
        'receiving_id': receiving_id,
        'object_locations': tuple(object_locations),
    })


def _decode_underwater_acoustic(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    emitting_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    state_change_indicator = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    pad = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    passive_parameter_index = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    propulsion_plant_configuration = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_shafts = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_apas = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    number_of_ua_emitter_systems = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    shaft_rpms = []
    for _ in range(number_of_shafts):
        record, offset = _decode_shaft_rpms_dis6(body, offset)
        shaft_rpms.append(record)
    apa_data = []
    for _ in range(number_of_apas):
        record, offset = _decode_apa_data_dis6(body, offset)
        apa_data.append(record)
    emitter_systems_bytes = body[offset:]
    return MappingProxyType({
        'emitting_entity_id': emitting_entity_id,
        'event_id': event_id,
        'state_change_indicator': state_change_indicator,
        'pad': pad,
        'passive_parameter_index': passive_parameter_index,
        'propulsion_plant_configuration': propulsion_plant_configuration,
        'number_of_shafts': number_of_shafts,
        'number_of_apas': number_of_apas,
        'number_of_ua_emitter_systems': number_of_ua_emitter_systems,
        'shaft_rpms': tuple(shaft_rpms),
        'apa_data': tuple(apa_data),
        'emitter_systems_bytes': emitter_systems_bytes,
    })


def _decode_sees(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    orginating_entity_id, offset = _entity_id(body, offset)
    infrared_signature_representation_index = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    acoustic_signature_representation_index = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    radar_cross_section_signature_representation_index = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_propulsion_systems = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_vectoring_nozzle_systems = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    propulsion_system_data = []
    for _ in range(number_of_propulsion_systems):
        power_setting = float(struct.unpack_from('>f', body, offset)[0])
        offset += 4
        engine_rpm = float(struct.unpack_from('>f', body, offset)[0])
        offset += 4
        propulsion_system_data.append({'power_setting': power_setting, 'engine_rpm': engine_rpm})
    vectoring_system_data = []
    for _ in range(number_of_vectoring_nozzle_systems):
        horizontal_deflection_angle = float(struct.unpack_from('>f', body, offset)[0])
        offset += 4
        vertical_deflection_angle = float(struct.unpack_from('>f', body, offset)[0])
        offset += 4
        vectoring_system_data.append({'horizontal_deflection_angle': horizontal_deflection_angle, 'vertical_deflection_angle': vertical_deflection_angle})
    return MappingProxyType({
        'orginating_entity_id': orginating_entity_id,
        'infrared_signature_representation_index': infrared_signature_representation_index,
        'acoustic_signature_representation_index': acoustic_signature_representation_index,
        'radar_cross_section_signature_representation_index': radar_cross_section_signature_representation_index,
        'number_of_propulsion_systems': number_of_propulsion_systems,
        'number_of_vectoring_nozzle_systems': number_of_vectoring_nozzle_systems,
        'propulsion_system_data': tuple(propulsion_system_data),
        'vectoring_system_data': tuple(vectoring_system_data),
    })


def _decode_fire(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    firing_entity_id, offset = _entity_id(body, offset)
    target_entity_id, offset = _entity_id(body, offset)
    munition_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    fire_mission_index = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    world_location, offset = _vec3d(body, offset)
    munition_descriptor, offset = _munition_descriptor(body, offset)
    velocity, offset = _vec3f(body, offset)
    range_to_target_m = float(struct.unpack_from('>f', body, offset)[0])
    return MappingProxyType({
        'firing_entity_id': firing_entity_id,
        'target_entity_id': target_entity_id,
        'munition_entity_id': munition_entity_id,
        'event_id': event_id,
        'fire_mission_index': fire_mission_index,
        'world_location': world_location,
        'munition_descriptor': munition_descriptor,
        'velocity': velocity,
        'range_to_target_m': range_to_target_m,
    })


def _decode_collision(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    issuing_entity_id, offset = _entity_id(body, offset)
    colliding_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    collision_type = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    velocity, offset = _vec3f(body, offset)
    mass_kg = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    location, offset = _vec3f(body, offset)
    return MappingProxyType({
        'issuing_entity_id': issuing_entity_id,
        'colliding_entity_id': colliding_entity_id,
        'event_id': event_id,
        'collision_type': collision_type,
        'padding': padding,
        'velocity': velocity,
        'mass_kg': mass_kg,
        'location': location,
    })


def _decode_detonation(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    firing_entity_id, offset = _entity_id(body, offset)
    target_entity_id, offset = _entity_id(body, offset)
    exploding_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    velocity, offset = _vec3f(body, offset)
    world_location, offset = _vec3d(body, offset)
    munition_descriptor, offset = _munition_descriptor(body, offset)
    location_in_entity_coordinates, offset = _vec3f(body, offset)
    detonation_result = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    variable_parameter_count = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    variable_parameter_bytes = body[offset:]
    return MappingProxyType({
        'firing_entity_id': firing_entity_id,
        'target_entity_id': target_entity_id,
        'exploding_entity_id': exploding_entity_id,
        'event_id': event_id,
        'velocity': velocity,
        'world_location': world_location,
        'munition_descriptor': munition_descriptor,
        'location_in_entity_coordinates': location_in_entity_coordinates,
        'detonation_result': detonation_result,
        'variable_parameter_count': variable_parameter_count,
        'padding': padding,
        'variable_parameter_bytes': variable_parameter_bytes,
    })


def _decode_directed_energy_fire(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    firing_entity_id, offset = _entity_id(body, offset)
    target_entity_id, offset = _entity_id(body, offset)
    munition_type, offset = _entity_type(body, offset)
    shot_start_time, offset = _clock_time(body, offset)
    cumulative_shot_time_s = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    aperture_emitter_location, offset = _vec3f(body, offset)
    aperture_diameter_m = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    wavelength_m = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    peak_irradiance_w_m2 = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    pulse_repetition_frequency_hz = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    pulse_width = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    flags = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    pulse_shape = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding1 = int(struct.unpack_from('>B', body, offset)[0])
    offset += 1
    padding2 = int(struct.unpack_from('>I', body, offset)[0])
    offset += 4
    padding3 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_de_records = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    de_record_bytes = body[offset:]
    return MappingProxyType({
        'firing_entity_id': firing_entity_id,
        'target_entity_id': target_entity_id,
        'munition_type': munition_type,
        'shot_start_time': shot_start_time,
        'cumulative_shot_time_s': cumulative_shot_time_s,
        'aperture_emitter_location': aperture_emitter_location,
        'aperture_diameter_m': aperture_diameter_m,
        'wavelength_m': wavelength_m,
        'peak_irradiance_w_m2': peak_irradiance_w_m2,
        'pulse_repetition_frequency_hz': pulse_repetition_frequency_hz,
        'pulse_width': pulse_width,
        'flags': flags,
        'pulse_shape': pulse_shape,
        'padding1': padding1,
        'padding2': padding2,
        'padding3': padding3,
        'number_of_de_records': number_of_de_records,
        'de_record_bytes': de_record_bytes,
    })


def _decode_collision_elastic(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    issuing_entity_id, offset = _entity_id(body, offset)
    colliding_entity_id, offset = _entity_id(body, offset)
    event_id, offset = _event_id(body, offset)
    padding = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    contact_velocity, offset = _vec3f(body, offset)
    mass_kg = float(struct.unpack_from('>f', body, offset)[0])
    offset += 4
    location, offset = _vec3f(body, offset)
    tensor = struct.unpack_from('>ffffff', body, offset)
    offset += 24
    unit_surface_normal, offset = _vec3f(body, offset)
    coefficient_of_restitution = float(struct.unpack_from('>f', body, offset)[0])
    return MappingProxyType({
        'issuing_entity_id': issuing_entity_id,
        'colliding_entity_id': colliding_entity_id,
        'event_id': event_id,
        'padding': padding,
        'contact_velocity': contact_velocity,
        'mass_kg': mass_kg,
        'location': location,
        'collision_tensor': {
            'xx': float(tensor[0]),
            'xy': float(tensor[1]),
            'xz': float(tensor[2]),
            'yy': float(tensor[3]),
            'yz': float(tensor[4]),
            'zz': float(tensor[5]),
        },
        'unit_surface_normal': unit_surface_normal,
        'coefficient_of_restitution': coefficient_of_restitution,
    })


def _decode_entity_damage_status(typed: TypedPdu) -> Mapping[str, object]:
    body = typed.body
    offset = 0
    firing_entity_id, offset = _entity_id(body, offset)
    target_entity_id, offset = _entity_id(body, offset)
    damaged_entity_id, offset = _entity_id(body, offset)
    padding1 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    padding2 = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    number_of_damage_description = int(struct.unpack_from('>H', body, offset)[0])
    offset += 2
    damage_description_record_bytes = body[offset:]
    return MappingProxyType({
        'firing_entity_id': firing_entity_id,
        'target_entity_id': target_entity_id,
        'damaged_entity_id': damaged_entity_id,
        'padding1': padding1,
        'padding2': padding2,
        'number_of_damage_description': number_of_damage_description,
        'damage_description_record_bytes': damage_description_record_bytes,
    })


_SEMANTIC_DECODERS = {
    (6, 0): _decode_other_pdu,
    (6, 11): _decode_create_remove_entity,
    (6, 12): _decode_create_remove_entity,
    (6, 13): _decode_start_resume,
    (6, 14): _decode_stop_freeze,
    (6, 15): _decode_acknowledge,
    (6, 16): _decode_action_request,
    (6, 17): _decode_action_response,
    (6, 18): _decode_data_query,
    (6, 19): _decode_set_data,
    (6, 20): _decode_set_data,
    (6, 21): _decode_event_report,
    (6, 22): _decode_comment,
    (6, 23): _decode_electromagnetic_emission_dis6,
    (6, 24): _decode_designator,
    (6, 5): _decode_service_request,
    (6, 6): _decode_resupply_offer_or_received,
    (6, 7): _decode_resupply_offer_or_received,
    (6, 8): _decode_resupply_cancel,
    (6, 9): _decode_repair_complete,
    (6, 10): _decode_repair_response,
    (6, 33): _decode_aggregate_state_dis6,
    (6, 34): _decode_is_group_of_dis6,
    (6, 35): _decode_transfer_control_request,
    (7, 35): _decode_transfer_control_request,
    (6, 36): _decode_is_part_of,
    (6, 37): _decode_minefield_state_dis6,
    (6, 38): _decode_minefield_query_dis6,
    (6, 39): _decode_minefield_data_dis6,
    (7, 39): _decode_minefield_data_dis6,
    (6, 40): _decode_minefield_response_nack,
    (6, 41): _decode_environmental_process_dis6,
    (7, 41): _decode_environmental_process_dis6,
    (6, 42): _decode_gridded_data_dis6,
    (7, 42): _decode_gridded_data_dis6,
    (6, 43): _decode_point_object_state_dis6,
    (6, 44): _decode_linear_object_state_dis6,
    (6, 45): _decode_areal_object_state_dis6,
    (6, 46): _decode_tspi_live_entity,
    (6, 47): _decode_live_entity_appearance,
    (6, 48): _decode_live_entity_articulated_parts,
    (6, 49): _decode_live_entity_fire,
    (6, 50): _decode_live_entity_detonation,
    (6, 25): _decode_transmitter_dis6,
    (6, 26): _decode_signal_dis6,
    (6, 27): _decode_receiver_dis6,
    (6, 28): _decode_iff_atc_navaids_dis6,
    (6, 29): _decode_underwater_acoustic,
    (6, 30): _decode_sees,
    (6, 2): _decode_fire,
    (6, 3): _decode_detonation,
    (6, 4): _decode_collision,
    (6, 31): _decode_intercom_signal_dis6,
    (6, 32): _decode_intercom_control,
    (6, 51): _decode_create_remove_entity_reliable,
    (6, 52): _decode_create_remove_entity_reliable,
    (6, 53): _decode_start_resume_reliable,
    (6, 54): _decode_stop_freeze_reliable,
    (6, 55): _decode_acknowledge_reliable,
    (6, 56): _decode_action_request_reliable,
    (6, 57): _decode_action_response_reliable,
    (6, 58): _decode_data_query_reliable,
    (6, 59): _decode_set_data_reliable,
    (6, 60): _decode_data_reliable,
    (6, 61): _decode_event_report_reliable,
    (6, 62): _decode_comment_reliable,
    (6, 63): _decode_record_reliable,
    (6, 64): _decode_set_record_reliable,
    (6, 65): _decode_record_query_reliable,
    (6, 66): _decode_collision_elastic,
    (7, 0): _decode_other_pdu,
    (7, 11): _decode_create_remove_entity,
    (7, 12): _decode_create_remove_entity,
    (7, 13): _decode_start_resume,
    (7, 14): _decode_stop_freeze,
    (7, 15): _decode_acknowledge,
    (7, 16): _decode_action_request,
    (7, 17): _decode_action_response,
    (7, 18): _decode_data_query,
    (7, 19): _decode_set_data,
    (7, 20): _decode_set_data,
    (7, 21): _decode_event_report,
    (7, 22): _decode_comment,
    (7, 23): _decode_electromagnetic_emission_dis7,
    (7, 24): _decode_designator,
    (7, 5): _decode_service_request,
    (7, 6): _decode_resupply_offer_or_received,
    (7, 7): _decode_resupply_offer_or_received,
    (7, 8): _decode_resupply_cancel,
    (7, 9): _decode_repair_complete,
    (7, 10): _decode_repair_response,
    (7, 33): _decode_aggregate_state_dis6,
    (7, 34): _decode_is_group_of_dis6,
    (7, 36): _decode_is_part_of,
    (7, 37): _decode_minefield_state_dis7,
    (7, 38): _decode_minefield_query_dis6,
    (7, 40): _decode_minefield_response_nack,
    (7, 43): _decode_point_object_state_dis7,
    (7, 44): _decode_linear_object_state_dis7,
    (7, 45): _decode_areal_object_state_dis7,
    (7, 46): _decode_tspi_live_entity,
    (7, 47): _decode_live_entity_appearance,
    (7, 48): _decode_live_entity_articulated_parts,
    (7, 49): _decode_live_entity_fire,
    (7, 50): _decode_live_entity_detonation,
    (7, 25): _decode_transmitter_dis7,
    (7, 26): _decode_signal_dis7,
    (7, 27): _decode_receiver_dis7,
    (7, 28): _decode_iff_dis7,
    (7, 29): _decode_underwater_acoustic,
    (7, 30): _decode_sees,
    (7, 2): _decode_fire,
    (7, 3): _decode_detonation,
    (7, 4): _decode_collision,
    (7, 31): _decode_intercom_signal_dis7,
    (7, 32): _decode_intercom_control,
    (7, 51): _decode_create_remove_entity_reliable,
    (7, 52): _decode_create_remove_entity_reliable,
    (7, 53): _decode_start_resume_reliable,
    (7, 54): _decode_stop_freeze_reliable,
    (7, 55): _decode_acknowledge_reliable,
    (7, 56): _decode_action_request_reliable,
    (7, 57): _decode_action_response_reliable,
    (7, 58): _decode_data_query_reliable,
    (7, 59): _decode_set_data_reliable,
    (7, 60): _decode_data_reliable,
    (7, 61): _decode_event_report_reliable,
    (7, 62): _decode_comment_reliable,
    (7, 63): _decode_record_reliable,
    (7, 64): _decode_set_record_reliable,
    (7, 65): _decode_record_query_reliable,
    (7, 66): _decode_collision_elastic,
    (7, 68): _decode_directed_energy_fire,
    (7, 69): _decode_entity_damage_status,
    (7, 70): _decode_information_operations_action_dis7,
    (7, 71): _decode_information_operations_report_dis7,
    (7, 72): _decode_attribute_dis7,
}


def find_semantic_pdu_descriptor(protocol_version: int, pdu_type: int) -> SemanticPduDescriptor | None:
    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))


def _semantic_fields(descriptor: SemanticPduDescriptor, typed: TypedPdu) -> tuple[Mapping[str, object], str | None]:
    fields = {
        'protocol_version': typed.header[0],
        'exercise_id': typed.header[1],
        'pdu_type': typed.header[2],
        'protocol_family': typed.header[3],
        'timestamp': typed.header[4],
        'declared_length': typed.header[5],
        'standard_name': descriptor.standard_name,
        'standard_class_name': descriptor.standard_class_name,
        'schema_status': descriptor.schema_status,
        'catalog_status': descriptor.catalog_status,
        'declared_fields': descriptor.declared_fields,
        'raw_body_size': len(typed.body),
        'raw_body': typed.body,
        'typed_parse_level': typed.parse_level,
        'fully_domain_decoded': descriptor.fully_domain_decoded,
    }
    decoder = _SEMANTIC_DECODERS.get((typed.header[0], typed.header[2]))
    if decoder is not None:
        try:
            decoded_fields = decoder(typed)
        except (IndexError, ValueError, struct.error) as exc:
            fields['semantic_decode_status'] = 'decode_error'
            fields['semantic_decode_error'] = str(exc)
            fields['semantic_decode_error_type'] = type(exc).__name__
            return MappingProxyType(fields), f'semantic decoder failed: {type(exc).__name__}: {exc}'
        fields['semantic_decode_status'] = 'decoded'
        fields.update(decoded_fields)
    elif descriptor.semantic_level == 'semantic_decoded':
        fields['semantic_decode_status'] = 'decoded'
    elif descriptor.semantic_level == 'semantic_prefix':
        fields['semantic_prefix_available'] = True
        fields['semantic_decode_status'] = 'prefix'
    else:
        fields['semantic_decode_status'] = 'observation'
    return MappingProxyType(fields), None


def _diagnostics(descriptor: SemanticPduDescriptor, *, decode_error: str | None = None) -> tuple[str, ...]:
    if decode_error is not None:
        return (decode_error, f'schema_status={descriptor.schema_status}')
    if descriptor.semantic_level == 'semantic_decoded':
        return ('full domain decode available',)
    if descriptor.semantic_level == 'semantic_prefix':
        return ('semantic prefix parser available',)
    return (
        'semantic observation parser: full domain semantics not yet implemented',
        f'schema_status={descriptor.schema_status}',
    )


def parse_semantic_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> SemanticPdu | None:
    typed = parse_typed_pdu(data, strict=strict)
    if typed is None:
        return None
    descriptor = find_semantic_pdu_descriptor(typed.header[0], typed.header[2])
    if descriptor is None:
        if strict:
            raise ValueError(f'unknown DIS PDU type {typed.header[2]} for protocol version {typed.header[0]}')
        return None
    cls = _CLASS_BY_NAME[descriptor.semantic_class]
    semantic_fields, decode_error = _semantic_fields(descriptor, typed)
    return cls(
        descriptor=descriptor,
        typed=typed,
        semantic_fields=semantic_fields,
        diagnostics=_diagnostics(descriptor, decode_error=decode_error),
    )


def serialize_semantic_pdu(view: SemanticPdu) -> bytes:
    if not isinstance(view, SemanticPdu):
        raise TypeError('serialize_semantic_pdu expects a SemanticPdu')
    return serialize_typed_pdu(view.typed)


def parse_many_semantic(packets: list[bytes] | tuple[bytes, ...], *, strict: bool = False) -> list[SemanticPdu]:
    out: list[SemanticPdu] = []
    for packet in packets:
        view = parse_semantic_pdu(packet, strict=strict)
        if view is not None:
            out.append(view)
    return out


SEMANTIC_PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_semantic_pdu for item in SEMANTIC_PDU_DESCRIPTORS}
SEMANTIC_PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_semantic_pdu for item in SEMANTIC_PDU_DESCRIPTORS}
