"""Generated generic DIS PDU parser, visitor, and serializer views.

These views cover every cataloged DIS 6/7 PDU at the packet boundary:
header validation, byte-preserving parse, generic field visitation, and
round-trip serialization. They are intentionally distinct from typed
semantic body decoders such as the Entity State fast path.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import NamedTuple

from . import _fallback


class MessageDescriptor(NamedTuple):
    protocol_version: int
    pdu_type: int
    protocol_family: int
    class_name: str
    name: str
    family_name: str
    declared_fields: tuple[str, ...]


class GenericPduView(NamedTuple):
    descriptor: MessageDescriptor
    header: tuple[int, int, int, int, int, int, int, int]
    packet: bytes

    @property
    def body(self) -> bytes:
        return self.packet[12:self.header[5]]


class FieldVisit(NamedTuple):
    name: str
    path: str
    kind: str
    offset: int
    length: int
    value: object


MESSAGE_DESCRIPTORS: tuple[MessageDescriptor, ...] = (
    MessageDescriptor(6, 1, 1, 'EntityStatePdu', 'EntityState', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'forceId', 'numberOfArticulationParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'articulationParameters')),
    MessageDescriptor(6, 2, 2, 'FirePdu', 'Fire', 'Warfare', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'burstDescriptor', 'velocity', 'rangeToTarget')),
    MessageDescriptor(6, 3, 2, 'DetonationPdu', 'Detonation', 'Warfare', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'firingEntityID', 'targetEntityID', 'munitionID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'burstDescriptor', 'locationInEntityCoordinates', 'detonationResult', 'numberOfArticulationParameters', 'pad', 'articulationParameters')),
    MessageDescriptor(6, 4, 1, 'CollisionPdu', 'Collision', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location')),
    MessageDescriptor(6, 5, 3, 'ServiceRequestPdu', 'ServiceRequest', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies')),
    MessageDescriptor(6, 6, 3, 'ResupplyOfferPdu', 'ResupplyOffer', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies')),
    MessageDescriptor(6, 7, 3, 'ResupplyReceivedPdu', 'ResupplyReceived', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies')),
    MessageDescriptor(6, 8, 3, 'ResupplyCancelPdu', 'ResupplyCancel', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'supplyingEntityID')),
    MessageDescriptor(6, 9, 3, 'RepairCompletePdu', 'RepairComplete', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding2')),
    MessageDescriptor(6, 10, 3, 'RepairResponsePdu', 'RepairResponse', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2')),
    MessageDescriptor(6, 11, 5, 'CreateEntityPdu', 'CreateEntity', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID')),
    MessageDescriptor(6, 12, 5, 'RemoveEntityPdu', 'RemoveEntity', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID')),
    MessageDescriptor(6, 13, 5, 'StartResumePdu', 'StartResume', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requestID')),
    MessageDescriptor(6, 14, 5, 'StopFreezePdu', 'StopFreeze', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'padding1', 'requestID')),
    MessageDescriptor(6, 15, 5, 'AcknowledgePdu', 'Acknowledge', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID')),
    MessageDescriptor(6, 16, 5, 'ActionRequestPdu', 'ActionRequest', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 17, 5, 'ActionResponsePdu', 'ActionResponse', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requestStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 18, 5, 'DataQueryPdu', 'DataQuery', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 19, 5, 'SetDataPdu', 'SetData', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 20, 5, 'DataPdu', 'Data', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 21, 5, 'EventReportPdu', 'EventReport', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 22, 5, 'CommentPdu', 'Comment', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(6, 23, 6, 'ElectronicEmissionsPdu', 'ElectronicEmissions', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systems')),
    MessageDescriptor(6, 24, 6, 'DesignatorPdu', 'Designator', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration')),
    MessageDescriptor(6, 25, 4, 'TransmitterPdu', 'Transmitter', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'radioEntityType', 'transmitState', 'inputSource', 'padding1', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList')),
    MessageDescriptor(6, 26, 4, 'SignalPdu', 'Signal', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data')),
    MessageDescriptor(6, 27, 4, 'ReceiverPdu', 'Receiver', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'radioId', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId')),
    MessageDescriptor(6, 28, 6, 'IffAtcNavAidsLayer1Pdu', 'IffAtcNavAidsLayer1', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters')),
    MessageDescriptor(6, 29, 6, 'UaPdu', 'Ua', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems')),
    MessageDescriptor(6, 30, 6, 'SeesPdu', 'Sees', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData')),
    MessageDescriptor(6, 31, 4, 'IntercomSignalPdu', 'IntercomSignal', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityId', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data')),
    MessageDescriptor(6, 32, 4, 'IntercomControlPdu', 'IntercomControl', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters')),
    MessageDescriptor(6, 33, 7, 'AggregateStatePdu', 'AggregateState', 'Entity Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'aggregateID', 'forceID', 'aggregateState', 'aggregateType', 'formation', 'aggregateMarking', 'dimensions', 'orientation', 'centerOfMass', 'velocity', 'numberOfDisAggregates', 'numberOfDisEntities', 'numberOfSilentAggregateTypes', 'numberOfSilentEntityTypes', 'aggregateIDList', 'entityIDList', 'pad2', 'silentAggregateSystemList', 'silentEntitySystemList', 'numberOfVariableDatumRecords', 'variableDatumList')),
    MessageDescriptor(6, 34, 7, 'IsGroupOfPdu', 'IsGroupOf', 'Entity Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'groupEntityID', 'groupedEntityCategory', 'numberOfGroupedEntities', 'pad2', 'latitude', 'longitude', 'groupedEntityDescriptions')),
    MessageDescriptor(6, 35, 7, 'TransferControlRequestPdu', 'TransferControlRequest', 'Entity Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'recevingEntityID', 'requestID', 'requiredReliabilityService', 'tranferType', 'transferEntityID', 'numberOfRecordSets', 'recordSets')),
    MessageDescriptor(6, 36, 7, 'IsPartOfPdu', 'IsPartOf', 'Entity Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType')),
    MessageDescriptor(6, 37, 8, 'MinefieldStatePdu', 'MinefieldState', 'Minefield', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType')),
    MessageDescriptor(6, 38, 8, 'MinefieldQueryPdu', 'MinefieldQuery', 'Minefield', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfPerimeterPoints', 'pad2', 'numberOfSensorTypes', 'dataFilter', 'requestedMineType', 'requestedPerimeterPoints', 'sensorTypes')),
    MessageDescriptor(6, 39, 8, 'MinefieldDataPdu', 'MinefieldData', 'Minefield', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'minefieldSequenceNumbeer', 'requestID', 'pduSequenceNumber', 'numberOfPdus', 'numberOfMinesInThisPdu', 'numberOfSensorTypes', 'pad2', 'dataFilter', 'mineType', 'sensorTypes', 'pad3', 'mineLocation')),
    MessageDescriptor(6, 40, 8, 'MinefieldResponseNackPdu', 'MinefieldResponseNack', 'Minefield', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers')),
    MessageDescriptor(6, 41, 9, 'EnvironmentalProcessPdu', 'EnvironmentalProcess', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environementalProcessID', 'environmentType', 'modelType', 'environmentStatus', 'numberOfEnvironmentRecords', 'sequenceNumber', 'environmentRecords')),
    MessageDescriptor(6, 42, 9, 'GriddedDataPdu', 'GriddedData', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'environmentalSimulationApplicationID', 'fieldNumber', 'pduNumber', 'pduTotal', 'coordinateSystem', 'numberOfGridAxes', 'constantGrid', 'environmentType', 'orientation', 'sampleTime', 'totalValues', 'vectorDimension', 'padding1', 'padding2', 'gridDataList')),
    MessageDescriptor(6, 43, 9, 'PointObjectStatePdu', 'PointObjectState', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2')),
    MessageDescriptor(6, 44, 9, 'LinearObjectStatePdu', 'LinearObjectState', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters')),
    MessageDescriptor(6, 45, 9, 'ArealObjectStatePdu', 'ArealObjectState', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation')),
    MessageDescriptor(6, 51, 10, 'CreateEntityReliablePdu', 'CreateEntityReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID')),
    MessageDescriptor(6, 52, 10, 'RemoveEntityReliablePdu', 'RemoveEntityReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID')),
    MessageDescriptor(6, 53, 10, 'StartResumeReliablePdu', 'StartResumeReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID')),
    MessageDescriptor(6, 54, 10, 'StopFreezeReliablePdu', 'StopFreezeReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'requiredReliablityService', 'pad1', 'requestID')),
    MessageDescriptor(6, 55, 10, 'AcknowledgeReliablePdu', 'AcknowledgeReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID')),
    MessageDescriptor(6, 56, 10, 'ActionRequestReliablePdu', 'ActionRequestReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 57, 10, 'ActionResponseReliablePdu', 'ActionResponseReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'responseStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 58, 10, 'DataQueryReliablePdu', 'DataQueryReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 59, 10, 'SetDataReliablePdu', 'SetDataReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 60, 10, 'DataReliablePdu', 'DataReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 61, 10, 'EventReportReliablePdu', 'EventReportReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'pad1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 62, 10, 'CommentReliablePdu', 'CommentReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(6, 64, 10, 'SetRecordReliablePdu', 'SetRecordReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfRecordSets', 'recordSets')),
    MessageDescriptor(6, 65, 10, 'RecordQueryReliablePdu', 'RecordQueryReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs')),
    MessageDescriptor(6, 66, 1, 'CollisionElasticPdu', 'CollisionElastic', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'location', 'collisionResultXX', 'collisionResultXY', 'collisionResultXZ', 'collisionResultYY', 'collisionResultYZ', 'collisionResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution')),
    MessageDescriptor(6, 67, 1, 'EntityStateUpdatePdu', 'EntityStateUpdate', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'pduLength', 'padding', 'entityID', 'padding1', 'numberOfArticulationParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'articulationParameters')),
    MessageDescriptor(7, 1, 1, 'EntityStatePdu', 'EntityState', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'forceId', 'numberOfVariableParameters', 'entityType', 'alternativeEntityType', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'deadReckoningParameters', 'marking', 'capabilities', 'variableParameters')),
    MessageDescriptor(7, 2, 2, 'FirePdu', 'Fire', 'Warfare', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionExpendibleID', 'eventID', 'fireMissionIndex', 'locationInWorldCoordinates', 'descriptor', 'velocity', 'range')),
    MessageDescriptor(7, 3, 2, 'DetonationPdu', 'Detonation', 'Warfare', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'explodingEntityID', 'eventID', 'velocity', 'locationInWorldCoordinates', 'descriptor', 'locationOfEntityCoordinates', 'detonationResult', 'numberOfVariableParameters', 'pad', 'variableParameters')),
    MessageDescriptor(7, 4, 1, 'CollisionPdu', 'Collision', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'eventID', 'collisionType', 'pad', 'velocity', 'mass', 'location')),
    MessageDescriptor(7, 5, 3, 'ServiceRequestPdu', 'ServiceRequest', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'requestingEntityID', 'servicingEntityID', 'serviceTypeRequested', 'numberOfSupplyTypes', 'serviceRequestPadding', 'supplies')),
    MessageDescriptor(7, 6, 3, 'ResupplyOfferPdu', 'ResupplyOffer', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies')),
    MessageDescriptor(7, 7, 3, 'ResupplyReceivedPdu', 'ResupplyReceived', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'supplyingEntityID', 'numberOfSupplyTypes', 'padding1', 'padding2', 'supplies')),
    MessageDescriptor(7, 9, 3, 'RepairCompletePdu', 'RepairComplete', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repair', 'padding4')),
    MessageDescriptor(7, 10, 3, 'RepairResponsePdu', 'RepairResponse', 'Logistics', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receivingEntityID', 'repairingEntityID', 'repairResult', 'padding1', 'padding2')),
    MessageDescriptor(7, 11, 5, 'CreateEntityPdu', 'CreateEntity', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID')),
    MessageDescriptor(7, 12, 5, 'RemoveEntityPdu', 'RemoveEntity', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID')),
    MessageDescriptor(7, 13, 5, 'StartResumePdu', 'StartResume', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requestID')),
    MessageDescriptor(7, 14, 5, 'StopFreezePdu', 'StopFreeze', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'padding1', 'requestID')),
    MessageDescriptor(7, 15, 5, 'AcknowledgePdu', 'Acknowledge', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID')),
    MessageDescriptor(7, 16, 5, 'ActionRequestPdu', 'ActionRequest', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 17, 5, 'ActionResponsePdu', 'ActionResponse', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requestStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 18, 5, 'DataQueryPdu', 'DataQuery', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 19, 5, 'SetDataPdu', 'SetData', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 20, 5, 'DataPdu', 'Data', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 21, 5, 'EventReportPdu', 'EventReport', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'padding1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 22, 5, 'CommentPdu', 'Comment', 'Simulation Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatums', 'variableDatums')),
    MessageDescriptor(7, 23, 6, 'ElectronicEmissionsPdu', 'ElectronicEmissions', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateUpdateIndicator', 'numberOfSystems', 'paddingForEmissionsPdu', 'systemDataLength', 'numberOfBeams', 'emitterSystem', 'location', 'systems')),
    MessageDescriptor(7, 24, 6, 'DesignatorPdu', 'Designator', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'designatingEntityID', 'codeName', 'designatedEntityID', 'designatorCode', 'designatorPower', 'designatorWavelength', 'designatorSpotWrtDesignated', 'designatorSpotLocation', 'deadReckoningAlgorithm', 'padding1', 'padding2', 'entityLinearAcceleration')),
    MessageDescriptor(7, 25, 4, 'TransmitterPdu', 'Transmitter', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'radioReferenceID', 'radioNumber', 'radioEntityType', 'transmitState', 'inputSource', 'variableTransmitterParameterCount', 'antennaLocation', 'relativeAntennaLocation', 'antennaPatternType', 'antennaPatternCount', 'frequency', 'transmitFrequencyBandwidth', 'power', 'modulationType', 'cryptoSystem', 'cryptoKeyId', 'modulationParameterCount', 'padding2', 'padding3', 'modulationParametersList', 'antennaPatternList')),
    MessageDescriptor(7, 26, 4, 'SignalPdu', 'Signal', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data')),
    MessageDescriptor(7, 27, 4, 'ReceiverPdu', 'Receiver', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'receiverState', 'padding1', 'receivedPower', 'transmitterEntityId', 'transmitterRadioId')),
    MessageDescriptor(7, 28, 6, 'IffPdu', 'Iff', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityId', 'eventID', 'location', 'systemID', 'pad2', 'fundamentalParameters')),
    MessageDescriptor(7, 29, 6, 'UaPdu', 'Ua', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'emittingEntityID', 'eventID', 'stateChangeIndicator', 'pad', 'passiveParameterIndex', 'propulsionPlantConfiguration', 'numberOfShafts', 'numberOfAPAs', 'numberOfUAEmitterSystems', 'shaftRPMs', 'apaData', 'emitterSystems')),
    MessageDescriptor(7, 30, 6, 'SeesPdu', 'Sees', 'Distributed Emission Regeneration', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'infraredSignatureRepresentationIndex', 'acousticSignatureRepresentationIndex', 'radarCrossSectionSignatureRepresentationIndex', 'numberOfPropulsionSystems', 'numberOfVectoringNozzleSystems', 'propulsionSystemData', 'vectoringSystemData')),
    MessageDescriptor(7, 31, 4, 'IntercomSignalPdu', 'IntercomSignal', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'communicationsDeviceID', 'encodingScheme', 'tdlType', 'sampleRate', 'dataLength', 'samples', 'data')),
    MessageDescriptor(7, 32, 4, 'IntercomControlPdu', 'IntercomControl', 'Radio Communications', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'controlType', 'communicationsChannelType', 'sourceEntityID', 'sourceCommunicationsDeviceID', 'sourceLineID', 'transmitPriority', 'transmitLineState', 'command', 'masterEntityID', 'masterCommunicationsDeviceID', 'intercomParametersLength', 'intercomParameters')),
    MessageDescriptor(7, 36, 7, 'IsPartOfPdu', 'IsPartOf', 'Entity Management', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'orginatingEntityID', 'receivingEntityID', 'relationship', 'partLocation', 'namedLocationID', 'partEntityType')),
    MessageDescriptor(7, 37, 8, 'MinefieldStatePdu', 'MinefieldState', 'Minefield', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'minefieldSequence', 'forceID', 'numberOfPerimeterPoints', 'minefieldType', 'numberOfMineTypes', 'minefieldLocation', 'minefieldOrientation', 'appearance', 'protocolMode', 'perimeterPoints', 'mineType')),
    MessageDescriptor(7, 40, 8, 'MinefieldResponseNackPdu', 'MinefieldResponseNack', 'Minefield', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'minefieldID', 'requestingEntityID', 'requestID', 'numberOfMissingPdus', 'missingPduSequenceNumbers')),
    MessageDescriptor(7, 43, 9, 'PointObjectStatePdu', 'PointObjectState', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'objectLocation', 'objectOrientation', 'objectAppearance', 'requesterID', 'receivingID', 'pad2')),
    MessageDescriptor(7, 44, 9, 'LinearObjectStatePdu', 'LinearObjectState', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'numberOfSegments', 'requesterID', 'receivingID', 'objectType', 'linearSegmentParameters')),
    MessageDescriptor(7, 45, 9, 'ArealObjectStatePdu', 'ArealObjectState', 'Synthetic Environment', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'objectID', 'referencedObjectID', 'updateNumber', 'forceID', 'modifications', 'objectType', 'specificObjectAppearance', 'generalObjectAppearance', 'numberOfPoints', 'requesterID', 'receivingID', 'objectLocation')),
    MessageDescriptor(7, 51, 10, 'CreateEntityReliablePdu', 'CreateEntityReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID')),
    MessageDescriptor(7, 52, 10, 'RemoveEntityReliablePdu', 'RemoveEntityReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID')),
    MessageDescriptor(7, 53, 10, 'StartResumeReliablePdu', 'StartResumeReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'simulationTime', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID')),
    MessageDescriptor(7, 54, 10, 'StopFreezeReliablePdu', 'StopFreezeReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'realWorldTime', 'reason', 'frozenBehavior', 'requiredReliablityService', 'pad1', 'requestID')),
    MessageDescriptor(7, 55, 10, 'AcknowledgeReliablePdu', 'AcknowledgeReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'acknowledgeFlag', 'responseFlag', 'requestID')),
    MessageDescriptor(7, 56, 10, 'ActionRequestReliablePdu', 'ActionRequestReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'actionID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 57, 10, 'ActionResponseReliablePdu', 'ActionResponseReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'responseStatus', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 58, 10, 'DataQueryReliablePdu', 'DataQueryReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'timeInterval', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 59, 10, 'SetDataReliablePdu', 'SetDataReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requiredReliabilityService', 'pad1', 'pad2', 'requestID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 60, 10, 'DataReliablePdu', 'DataReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 61, 10, 'EventReportReliablePdu', 'EventReportReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'eventType', 'pad1', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 62, 10, 'CommentReliablePdu', 'CommentReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'numberOfFixedDatumRecords', 'numberOfVariableDatumRecords', 'fixedDatumRecords', 'variableDatumRecords')),
    MessageDescriptor(7, 65, 10, 'RecordQueryReliablePdu', 'RecordQueryReliable', 'Simulation Management with Reliability', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'originatingEntityID', 'receivingEntityID', 'requestID', 'requiredReliabilityService', 'pad1', 'pad2', 'eventType', 'time', 'numberOfRecords', 'recordIDs')),
    MessageDescriptor(7, 66, 1, 'CollisionElasticPdu', 'CollisionElastic', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'issuingEntityID', 'collidingEntityID', 'collisionEventID', 'pad', 'contactVelocity', 'mass', 'locationOfImpact', 'collisionIntermediateResultXX', 'collisionIntermediateResultXY', 'collisionIntermediateResultXZ', 'collisionIntermediateResultYY', 'collisionIntermediateResultYZ', 'collisionIntermediateResultZZ', 'unitSurfaceNormal', 'coefficientOfRestitution')),
    MessageDescriptor(7, 67, 1, 'EntityStateUpdatePdu', 'EntityStateUpdate', 'Entity Information', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'entityID', 'padding1', 'numberOfVariableParameters', 'entityLinearVelocity', 'entityLocation', 'entityOrientation', 'entityAppearance', 'variableParameters')),
    MessageDescriptor(7, 68, 2, 'DirectedEnergyFirePdu', 'DirectedEnergyFire', 'Warfare', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'munitionType', 'shotStartTime', 'commulativeShotTime', 'ApertureEmitterLocation', 'apertureDiameter', 'wavelength', 'peakIrradiance', 'pulseRepetitionFrequency', 'pulseWidth', 'flags', 'pulseShape', 'padding1', 'padding2', 'padding3', 'numberOfDERecords', 'dERecords')),
    MessageDescriptor(7, 69, 2, 'EntityDamageStatusPdu', 'EntityDamageStatus', 'Warfare', ('protocolVersion', 'exerciseID', 'pduType', 'protocolFamily', 'timestamp', 'length', 'pduStatus', 'padding', 'firingEntityID', 'targetEntityID', 'damagedEntityID', 'padding1', 'padding2', 'numberOfDamageDescription', 'damageDescriptionRecords')),
)

_DESCRIPTORS_BY_KEY = {(item.protocol_version, item.pdu_type): item for item in MESSAGE_DESCRIPTORS}


def find_message_descriptor(protocol_version: int, pdu_type: int) -> MessageDescriptor | None:
    return _DESCRIPTORS_BY_KEY.get((protocol_version, pdu_type))


def parse_pdu(data: bytes | bytearray | memoryview, *, strict: bool = True) -> GenericPduView | None:
    header = _fallback.parse_header(data, strict=strict)
    if header is None:
        return None
    descriptor = find_message_descriptor(header[0], header[2])
    if descriptor is None:
        if strict:
            raise ValueError(f'unknown DIS PDU type {header[2]} for protocol version {header[0]}')
        return None
    packet = bytes(memoryview(data).cast('B')[:header[5]])
    return GenericPduView(descriptor, header, packet)


def serialize_pdu(view: GenericPduView) -> bytes:
    if not isinstance(view, GenericPduView):
        raise TypeError('serialize_pdu expects a GenericPduView')
    return bytes(view.packet)


def visit_pdu_fields(data_or_view: bytes | bytearray | memoryview | GenericPduView) -> tuple[FieldVisit, ...]:
    view = data_or_view if isinstance(data_or_view, GenericPduView) else parse_pdu(data_or_view)
    if view is None:
        return ()
    header_names = ('version', 'exercise_id', 'pdu_type', 'protocol_family', 'timestamp', 'length', 'status', 'padding')
    header_offsets = (0, 1, 2, 3, 4, 8, 10, 11)
    header_lengths = (1, 1, 1, 1, 4, 2, 1 if view.header[0] >= 7 else 0, 1 if view.header[0] >= 7 else 2)
    visits = [
        FieldVisit(name, f'header.{name}', 'header', offset, length, value)
        for name, offset, length, value in zip(header_names, header_offsets, header_lengths, view.header, strict=True)
    ]
    visits.append(FieldVisit('body', 'body', 'raw_body', 12, max(0, view.header[5] - 12), view.body))
    visits.extend(
        FieldVisit(name, f'schema.{name}', 'declared_schema_field', -1, -1, None)
        for name in view.descriptor.declared_fields
    )
    return tuple(visits)


def walk_pdu_fields(
    data_or_view: bytes | bytearray | memoryview | GenericPduView,
    visitor: Callable[[FieldVisit], object],
) -> int:
    count = 0
    for field in visit_pdu_fields(data_or_view):
        visitor(field)
        count += 1
    return count


def roundtrip_packet(data: bytes | bytearray | memoryview) -> bytes:
    view = parse_pdu(data)
    if view is None:
        raise ValueError('packet could not be parsed')
    return serialize_pdu(view)


def parse_many(packets: Iterable[bytes | bytearray | memoryview], *, strict: bool = False) -> list[GenericPduView]:
    views: list[GenericPduView] = []
    for packet in packets:
        view = parse_pdu(packet, strict=strict)
        if view is not None:
            views.append(view)
    return views


PDU_PARSERS = {(item.protocol_version, item.pdu_type): parse_pdu for item in MESSAGE_DESCRIPTORS}
PDU_SERIALIZERS = {(item.protocol_version, item.pdu_type): serialize_pdu for item in MESSAGE_DESCRIPTORS}
