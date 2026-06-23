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
    SemanticPduDescriptor(6, 0, 0, 'Other', 'OtherPdu', 'Dis6OtherSemanticPdu', 'Dis6OtherPdu', 'Protocol Family 0', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(6, 1, 1, 'Entity State', 'EntityStatePdu', 'Dis6EntityStateSemanticPdu', 'Dis6EntityStatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'forceId', 'numberOfArticulationParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'articulationParameters'), 'semantic_prefix', True),
    SemanticPduDescriptor(6, 2, 2, 'Fire', 'FirePdu', 'Dis6FireSemanticPdu', 'Dis6FirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'burstDescriptor', 'velocity', 'rangeToTarget'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 3, 2, 'Detonation', 'DetonationPdu', 'Dis6DetonationSemanticPdu', 'Dis6DetonationPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'burstDescriptor', 'locationInEntityCoordinates', 'detonationResult', 'numberOfArticulationParameters', 'pad', 'articulationParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 4, 1, 'Collision', 'CollisionPdu', 'Dis6CollisionSemanticPdu', 'Dis6CollisionPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 5, 3, 'Service Request', 'ServiceRequestPdu', 'Dis6ServiceRequestSemanticPdu', 'Dis6ServiceRequestPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 6, 3, 'Resupply Offer', 'ResupplyOfferPdu', 'Dis6ResupplyOfferSemanticPdu', 'Dis6ResupplyOfferPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 7, 3, 'Resupply Received', 'ResupplyReceivedPdu', 'Dis6ResupplyReceivedSemanticPdu', 'Dis6ResupplyReceivedPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 8, 3, 'Resupply Cancel', 'ResupplyCancelPdu', 'Dis6ResupplyCancelSemanticPdu', 'Dis6ResupplyCancelPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 9, 3, 'Repair Complete', 'RepairCompletePdu', 'Dis6RepairCompleteSemanticPdu', 'Dis6RepairCompletePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding2'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 10, 3, 'Repair Response', 'RepairResponsePdu', 'Dis6RepairResponseSemanticPdu', 'Dis6RepairResponsePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2'), 'semantic_observation', False),
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
    SemanticPduDescriptor(6, 23, 6, 'Electromagnetic Emission', 'ElectronicEmissionsPdu', 'Dis6ElectronicEmissionsSemanticPdu', 'Dis6ElectronicEmissionsPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systems'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 24, 6, 'Designator', 'DesignatorPdu', 'Dis6DesignatorSemanticPdu', 'Dis6DesignatorPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 25, 4, 'Transmitter', 'TransmitterPdu', 'Dis6TransmitterSemanticPdu', 'Dis6TransmitterPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'radioEntityType', 'transmitState', 'inputSource', 'padding1', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 26, 4, 'Signal', 'SignalPdu', 'Dis6SignalSemanticPdu', 'Dis6SignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 27, 4, 'Receiver', 'ReceiverPdu', 'Dis6ReceiverSemanticPdu', 'Dis6ReceiverPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 28, 6, 'IFF/ATC/NAVAIDS', 'IffAtcNavAidsLayer1Pdu', 'Dis6IffAtcNavAidsLayer1SemanticPdu', 'Dis6IffAtcNavAidsLayer1Pdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 29, 6, 'Underwater Acoustic', 'UaPdu', 'Dis6UaSemanticPdu', 'Dis6UaPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 30, 6, 'Supplemental Emission / Entity State', 'SEESPdu', 'Dis6SEESSemanticPdu', 'Dis6SEESPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 31, 4, 'Intercom Signal', 'IntercomSignalPdu', 'Dis6IntercomSignalSemanticPdu', 'Dis6IntercomSignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 32, 4, 'Intercom Control', 'IntercomControlPdu', 'Dis6IntercomControlSemanticPdu', 'Dis6IntercomControlPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 33, 7, 'Aggregate State', 'AggregateStatePdu', 'Dis6AggregateStateSemanticPdu', 'Dis6AggregateStatePdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'aggregateID', 'forceID', 'aggregateState', 'aggregateType', 'formation', 'aggregateMarking', 'dimensions', 'orientation', 'centerOfMass', 'velocity', 'numberOfDisAggregates', 'numberOfDisEntities', 'numberOfSilentAggregateTypes', 'numberOfSilentEntityTypes', 'aggregateIDList', 'entityIDList', 'pad2', 'silentAggregateSystemList', 'silentEntitySystemList', 'numberOfVariableDatumRecords', 'variableDatumList'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 34, 7, 'IsGroupOf', 'IsGroupOfPdu', 'Dis6IsGroupOfSemanticPdu', 'Dis6IsGroupOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'groupEntityID', 'groupedEntityCategory', 'numberOfGroupedEntities', 'pad2', 'latitude', 'longitude', 'groupedEntityDescriptions'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 35, 7, 'Transfer Control', 'TransferControlRequestPdu', 'Dis6TransferControlRequestSemanticPdu', 'Dis6TransferControlRequestPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'recevingEntityID', 'requestID', 'requiredReliabilityService', 'tranferType', 'transferEntityID', 'numberOfRecordSets', 'recordSets'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 36, 7, 'IsPartOf', 'IsPartOfPdu', 'Dis6IsPartOfSemanticPdu', 'Dis6IsPartOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 37, 8, 'Minefield State', 'MinefieldStatePdu', 'Dis6MinefieldStateSemanticPdu', 'Dis6MinefieldStatePdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 38, 8, 'Minefield Query', 'MinefieldQueryPdu', 'Dis6MinefieldQuerySemanticPdu', 'Dis6MinefieldQueryPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfPerimeterPoints', 'pad2', 'numberOfSensorTypes', 'dataFilter', 'requestedMineType', 'requestedPerimeterPoints', 'sensorTypes'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 39, 8, 'Minefield Data', 'MinefieldDataPdu', 'Dis6MinefieldDataSemanticPdu', 'Dis6MinefieldDataPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'minefieldSequenceNumbeer', 'requestID', 'pduSequenceNumber', 'numberOfPdus', 'numberOfMinesInThisPdu', 'numberOfSensorTypes', 'pad2', 'dataFilter', 'mineType', 'sensorTypes', 'pad3', 'mineLocation'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 40, 8, 'Minefield Response NACK', 'MinefieldResponseNackPdu', 'Dis6MinefieldResponseNackSemanticPdu', 'Dis6MinefieldResponseNackPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 41, 9, 'Environmental Process', 'EnvironmentalProcessPdu', 'Dis6EnvironmentalProcessSemanticPdu', 'Dis6EnvironmentalProcessPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environementalProcessID', 'environmentType', 'modelType', 'environmentStatus', 'numberOfEnvironmentRecords', 'sequenceNumber', 'environmentRecords'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 42, 9, 'Gridded Data', 'GriddedDataPdu', 'Dis6GriddedDataSemanticPdu', 'Dis6GriddedDataPdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environmentalSimulationApplicationID', 'fieldNumber', 'pduNumber', 'pduTotal', 'coordinateSystem', 'numberOfGridAxes', 'constantGrid', 'environmentType', 'orientation', 'sampleTime', 'totalValues', 'vectorDimension', 'padding1', 'padding2', 'gridDataList'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 43, 9, 'Point Object State', 'PointObjectStatePdu', 'Dis6PointObjectStateSemanticPdu', 'Dis6PointObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 44, 9, 'Linear Object State', 'LinearObjectStatePdu', 'Dis6LinearObjectStateSemanticPdu', 'Dis6LinearObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 45, 9, 'Areal Object State', 'ArealObjectStatePdu', 'Dis6ArealObjectStateSemanticPdu', 'Dis6ArealObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation'), 'semantic_observation', False),
    SemanticPduDescriptor(6, 46, 11, 'TSPI', 'TSPIPdu', 'Dis6TSPISemanticPdu', 'Dis6TSPIPdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(6, 47, 11, 'Appearance', 'AppearancePdu', 'Dis6AppearanceSemanticPdu', 'Dis6AppearancePdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(6, 48, 11, 'Articulated Parts', 'ArticulatedPartsPdu', 'Dis6ArticulatedPartsSemanticPdu', 'Dis6ArticulatedPartsPdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(6, 49, 11, 'LE Fire', 'LEFirePdu', 'Dis6LEFireSemanticPdu', 'Dis6LEFirePdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(6, 50, 11, 'LE Detonation', 'LEDetonationPdu', 'Dis6LEDetonationSemanticPdu', 'Dis6LEDetonationPdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
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
    SemanticPduDescriptor(6, 63, 10, 'Record-R', 'RecordReliablePdu', 'Dis6RecordReliableSemanticPdu', 'Dis6RecordReliablePdu', 'Simulation Management with Reliability', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(6, 64, 10, 'Set Record-R', 'SetRecordReliablePdu', 'Dis6SetRecordReliableSemanticPdu', 'Dis6SetRecordReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfRecordSets', 'recordSets'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 65, 10, 'Record Query-R', 'RecordQueryReliablePdu', 'Dis6RecordQueryReliableSemanticPdu', 'Dis6RecordQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 66, 1, 'Collision-Elastic', 'CollisionElasticPdu', 'Dis6CollisionElasticSemanticPdu', 'Dis6CollisionElasticPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'location', 'collisionResultXX', 'collisionResultXY', 'collisionResultXZ', 'collisionResultYY', 'collisionResultYZ', 'collisionResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution'), 'semantic_decoded', True),
    SemanticPduDescriptor(6, 67, 1, 'Entity State Update', 'EntityStateUpdatePdu', 'Dis6EntityStateUpdateSemanticPdu', 'Dis6EntityStateUpdatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'padding1', 'numberOfArticulationParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'articulationParameters'), 'semantic_prefix', True),
    SemanticPduDescriptor(7, 0, 0, 'Other', 'OtherPdu', 'Dis7OtherSemanticPdu', 'Dis7OtherPdu', 'Protocol Family 0', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 1, 1, 'Entity State', 'EntityStatePdu', 'Dis7EntityStateSemanticPdu', 'Dis7EntityStatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'forceId', 'numberOfVariableParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'variableParameters'), 'semantic_prefix', True),
    SemanticPduDescriptor(7, 2, 2, 'Fire', 'FirePdu', 'Dis7FireSemanticPdu', 'Dis7FirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionExpendibleID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'descriptor', 'velocity', 'range'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 3, 2, 'Detonation', 'DetonationPdu', 'Dis7DetonationSemanticPdu', 'Dis7DetonationPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'explodingEntityID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'descriptor', 'locationOfEntityCoordinates', 'detonationResult', 'numberOfVariableParameters', 'pad', 'variableParameters'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 4, 1, 'Collision', 'CollisionPdu', 'Dis7CollisionSemanticPdu', 'Dis7CollisionPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 5, 3, 'Service Request', 'ServiceRequestPdu', 'Dis7ServiceRequestSemanticPdu', 'Dis7ServiceRequestPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 6, 3, 'Resupply Offer', 'ResupplyOfferPdu', 'Dis7ResupplyOfferSemanticPdu', 'Dis7ResupplyOfferPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 7, 3, 'Resupply Received', 'ResupplyReceivedPdu', 'Dis7ResupplyReceivedSemanticPdu', 'Dis7ResupplyReceivedPdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 8, 3, 'Resupply Cancel', 'ResupplyCancelPdu', 'Dis7ResupplyCancelSemanticPdu', 'Dis7ResupplyCancelPdu', 'Logistics', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 9, 3, 'Repair Complete', 'RepairCompletePdu', 'Dis7RepairCompleteSemanticPdu', 'Dis7RepairCompletePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding4'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 10, 3, 'Repair Response', 'RepairResponsePdu', 'Dis7RepairResponseSemanticPdu', 'Dis7RepairResponsePdu', 'Logistics', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2'), 'semantic_observation', False),
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
    SemanticPduDescriptor(7, 23, 6, 'Electromagnetic Emission', 'ElectronicEmissionsPdu', 'Dis7ElectronicEmissionsSemanticPdu', 'Dis7ElectronicEmissionsPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systemDataLength', 'numberOfBeams', 'emitterSystem', 'location', 'systems'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 24, 6, 'Designator', 'DesignatorPdu', 'Dis7DesignatorSemanticPdu', 'Dis7DesignatorPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 25, 4, 'Transmitter', 'TransmitterPdu', 'Dis7TransmitterSemanticPdu', 'Dis7TransmitterPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'radioReferenceID', 'radioNumber', 'radioEntityType', 'transmitState', 'inputSource', 'variableTransmitterParameterCount', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 26, 4, 'Signal', 'SignalPdu', 'Dis7SignalSemanticPdu', 'Dis7SignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 27, 4, 'Receiver', 'ReceiverPdu', 'Dis7ReceiverSemanticPdu', 'Dis7ReceiverPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 28, 6, 'IFF', 'IffPdu', 'Dis7IffSemanticPdu', 'Dis7IffPdu', 'Distributed Emission Regeneration', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 29, 6, 'Underwater Acoustic', 'UaPdu', 'Dis7UaSemanticPdu', 'Dis7UaPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 30, 6, 'Supplemental Emission / Entity State', 'SEESPdu', 'Dis7SEESSemanticPdu', 'Dis7SEESPdu', 'Distributed Emission Regeneration', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 31, 4, 'Intercom Signal', 'IntercomSignalPdu', 'Dis7IntercomSignalSemanticPdu', 'Dis7IntercomSignalPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 32, 4, 'Intercom Control', 'IntercomControlPdu', 'Dis7IntercomControlSemanticPdu', 'Dis7IntercomControlPdu', 'Radio Communications', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 33, 7, 'Aggregate State', 'AggregateStatePdu', 'Dis7AggregateStateSemanticPdu', 'Dis7AggregateStatePdu', 'Entity Management', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 34, 7, 'IsGroupOf', 'IsGroupOfPdu', 'Dis7IsGroupOfSemanticPdu', 'Dis7IsGroupOfPdu', 'Entity Management', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 35, 7, 'Transfer Ownership', 'TransferOwnershipPdu', 'Dis7TransferOwnershipSemanticPdu', 'Dis7TransferOwnershipPdu', 'Entity Management', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 36, 7, 'IsPartOf', 'IsPartOfPdu', 'Dis7IsPartOfSemanticPdu', 'Dis7IsPartOfPdu', 'Entity Management', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 37, 8, 'Minefield State', 'MinefieldStatePdu', 'Dis7MinefieldStateSemanticPdu', 'Dis7MinefieldStatePdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 38, 8, 'Minefield Query', 'MinefieldQueryPdu', 'Dis7MinefieldQuerySemanticPdu', 'Dis7MinefieldQueryPdu', 'Minefield', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 39, 8, 'Minefield Data', 'MinefieldDataPdu', 'Dis7MinefieldDataSemanticPdu', 'Dis7MinefieldDataPdu', 'Minefield', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 40, 8, 'Minefield Response NACK', 'MinefieldResponseNackPdu', 'Dis7MinefieldResponseNackSemanticPdu', 'Dis7MinefieldResponseNackPdu', 'Minefield', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 41, 9, 'Environmental Process', 'EnvironmentalProcessPdu', 'Dis7EnvironmentalProcessSemanticPdu', 'Dis7EnvironmentalProcessPdu', 'Synthetic Environment', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 42, 9, 'Gridded Data', 'GriddedDataPdu', 'Dis7GriddedDataSemanticPdu', 'Dis7GriddedDataPdu', 'Synthetic Environment', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 43, 9, 'Point Object State', 'PointObjectStatePdu', 'Dis7PointObjectStateSemanticPdu', 'Dis7PointObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 44, 9, 'Linear Object State', 'LinearObjectStatePdu', 'Dis7LinearObjectStateSemanticPdu', 'Dis7LinearObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 45, 9, 'Areal Object State', 'ArealObjectStatePdu', 'Dis7ArealObjectStateSemanticPdu', 'Dis7ArealObjectStatePdu', 'Synthetic Environment', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'specificObjectAppearance', 'generalObjectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation'), 'semantic_observation', False),
    SemanticPduDescriptor(7, 46, 11, 'TSPI', 'TSPIPdu', 'Dis7TSPISemanticPdu', 'Dis7TSPIPdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 47, 11, 'Appearance', 'AppearancePdu', 'Dis7AppearanceSemanticPdu', 'Dis7AppearancePdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 48, 11, 'Articulated Parts', 'ArticulatedPartsPdu', 'Dis7ArticulatedPartsSemanticPdu', 'Dis7ArticulatedPartsPdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 49, 11, 'LE Fire', 'LEFirePdu', 'Dis7LEFireSemanticPdu', 'Dis7LEFirePdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 50, 11, 'LE Detonation', 'LEDetonationPdu', 'Dis7LEDetonationSemanticPdu', 'Dis7LEDetonationPdu', 'Live Entity', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
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
    SemanticPduDescriptor(7, 63, 10, 'Record-R', 'RecordReliablePdu', 'Dis7RecordReliableSemanticPdu', 'Dis7RecordReliablePdu', 'Simulation Management with Reliability', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 64, 10, 'Set Record-R', 'SetRecordReliablePdu', 'Dis7SetRecordReliableSemanticPdu', 'Dis7SetRecordReliablePdu', 'Simulation Management with Reliability', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 65, 10, 'Record Query-R', 'RecordQueryReliablePdu', 'Dis7RecordQueryReliableSemanticPdu', 'Dis7RecordQueryReliablePdu', 'Simulation Management with Reliability', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 66, 1, 'Collision-Elastic', 'CollisionElasticPdu', 'Dis7CollisionElasticSemanticPdu', 'Dis7CollisionElasticPdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'locationOfImpact', 'collisionIntermediateResultXX', 'collisionIntermediateResultXY', 'collisionIntermediateResultXZ', 'collisionIntermediateResultYY', 'collisionIntermediateResultYZ', 'collisionIntermediateResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 67, 1, 'Entity State Update', 'EntityStateUpdatePdu', 'Dis7EntityStateUpdateSemanticPdu', 'Dis7EntityStateUpdatePdu', 'Entity Information', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'padding1', 'numberOfVariableParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'variableParameters'), 'semantic_prefix', True),
    SemanticPduDescriptor(7, 68, 2, 'Directed Energy Fire', 'DirectedEnergyFirePdu', 'Dis7DirectedEnergyFireSemanticPdu', 'Dis7DirectedEnergyFirePdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionType', 'shotStartTime', 'commulativeShotTime', 'ApertureEmitterLocation', 'apertureDiameter', 'wavelength', 'peakIrradiance', 'pulseRepetitionFrequency', 'pulseWidth', 'flags', 'pulseShape', 'padding1', 'padding2', 'padding3', 'numberOfDERecords', 'dERecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 69, 2, 'Entity Damage Status', 'EntityDamageStatusPdu', 'Dis7EntityDamageStatusSemanticPdu', 'Dis7EntityDamageStatusPdu', 'Warfare', 'PRESENT', 'CATALOGED', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'damagedEntityID', 'padding1', 'padding2', 'numberOfDamageDescription', 'damageDescriptionRecords'), 'semantic_decoded', True),
    SemanticPduDescriptor(7, 70, 13, 'Information Operations Action', 'InformationOperationsActionPdu', 'Dis7InformationOperationsActionSemanticPdu', 'Dis7InformationOperationsActionPdu', 'Information Operations', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 71, 13, 'Information Operations Report', 'InformationOperationsReportPdu', 'Dis7InformationOperationsReportSemanticPdu', 'Dis7InformationOperationsReportPdu', 'Information Operations', 'SCHEMA_GAP', 'ENUM_ONLY', (), 'semantic_observation', False),
    SemanticPduDescriptor(7, 72, 1, 'Attribute', 'AttributePdu', 'Dis7AttributeSemanticPdu', 'Dis7AttributePdu', 'Entity Information', 'PRESENT_BUT_MISSING_PDU_TYPE_INITIAL_VALUE', 'ENUM_ONLY', (), 'semantic_observation', False),
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


def _vec3f(body: bytes, offset: int) -> tuple[dict[str, float], int]:
    x, y, z = struct.unpack_from('>fff', body, offset)
    return ({'x': float(x), 'y': float(y), 'z': float(z)}, offset + 12)


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
    (6, 24): _decode_designator,
    (6, 25): _decode_transmitter_dis6,
    (6, 26): _decode_signal_dis6,
    (6, 27): _decode_receiver_dis6,
    (6, 2): _decode_fire,
    (6, 3): _decode_detonation,
    (6, 4): _decode_collision,
    (6, 31): _decode_intercom_signal_dis6,
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
    (6, 64): _decode_set_record_reliable,
    (6, 65): _decode_record_query_reliable,
    (6, 66): _decode_collision_elastic,
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
    (7, 24): _decode_designator,
    (7, 25): _decode_transmitter_dis7,
    (7, 26): _decode_signal_dis7,
    (7, 27): _decode_receiver_dis7,
    (7, 2): _decode_fire,
    (7, 3): _decode_detonation,
    (7, 4): _decode_collision,
    (7, 31): _decode_intercom_signal_dis7,
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
    (7, 65): _decode_record_query_reliable,
    (7, 66): _decode_collision_elastic,
    (7, 68): _decode_directed_energy_fire,
    (7, 69): _decode_entity_damage_status,
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
