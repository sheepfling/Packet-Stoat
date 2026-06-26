using System;
using System.Runtime.InteropServices;

namespace FastDIS.Native
{
    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisScanConfig
    {
        public uint AcceptedProtocolMask;
        public uint AcceptedPduTypeMaskLow;
        public uint AcceptedPduTypeMaskHigh;
        public uint Flags;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisHeader
    {
        public byte Version;
        public byte ExerciseId;
        public byte PduType;
        public byte ProtocolFamily;
        public uint Timestamp;
        public ushort Length;
        public short Status;
        public ushort Padding;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisEntityId
    {
        public ushort Site;
        public ushort Application;
        public ushort Entity;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisClockTime
    {
        public uint Hour;
        public uint TimePastHour;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisSimulationAddress
    {
        public ushort Site;
        public ushort Application;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisEventId
    {
        public ushort Site;
        public ushort Application;
        public ushort EventNumber;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisBurstDescriptor
    {
        public FastDisEntityType MunitionType;
        public ushort Warhead;
        public ushort Fuse;
        public ushort Quantity;
        public ushort Rate;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisEntityTransform
    {
        public FastDisEntityId EntityId;
        public byte ForceId;
        public byte ExerciseId;
        public byte Version;
        public byte Reserved0;
        public uint Timestamp;
        public uint Appearance;
        public FastDisWorldCoordinates Location;
        public FastDisEulerAngles Orientation;
        public FastDisVec3F LinearVelocity;
        public ulong FieldsPresent;
        public byte DeadReckoningAlgorithm;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 15)]
        public byte[] DeadReckoningParameters;
        public FastDisVec3F DeadReckoningLinearAcceleration;
        public FastDisVec3F DeadReckoningAngularVelocity;

        public bool HasField(ulong fieldMask)
        {
            return (FieldsPresent & fieldMask) != 0UL;
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisSimulationManagementRequest
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisStartResume
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public FastDisClockTime RealWorldTime;
        public FastDisClockTime SimulationTime;
        public uint RequestId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisStopFreeze
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public FastDisClockTime RealWorldTime;
        public byte Reason;
        public byte FrozenBehavior;
        public ushort Padding1;
        public uint RequestId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisAcknowledge
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public ushort AcknowledgeFlag;
        public ushort ResponseFlag;
        public uint RequestId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisSimulationManagementReliableRequest
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint RequestId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisStartResumeReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public FastDisClockTime RealWorldTime;
        public FastDisClockTime SimulationTime;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint RequestId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisStopFreezeReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public FastDisClockTime RealWorldTime;
        public byte Reason;
        public byte FrozenBehavior;
        public byte RequiredReliablityService;
        public byte Pad1;
        public uint RequestId;
    }

    public struct FastDisActionRequest
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public uint ActionId;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisActionResponse
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public uint RequestStatus;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisDataQuery
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public FastDisClockTime TimeInterval;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisSetData
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public uint Padding1;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisEventReport
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint EventType;
        public uint Padding1;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisComment
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisActionRequestReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint RequestId;
        public uint ActionId;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisActionResponseReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public uint ResponseStatus;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisDataQueryReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint RequestId;
        public FastDisClockTime TimeInterval;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisSetDataReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint RequestId;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisDataReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisEventReportReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint EventType;
        public uint Pad1;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisCommentReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint NumberOfFixedDatumRecords;
        public uint NumberOfVariableDatumRecords;
        public byte[] DatumRecordBytes;
    }

    public struct FastDisRecordReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public byte RequiredReliabilityService;
        public byte Pad1;
        public ushort EventType;
        public uint RecordSetCount;
        public byte[] RecordSetBytes;
    }

    public struct FastDisSetRecordReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public uint RecordSetCount;
        public byte[] RecordSetBytes;
    }

    public struct FastDisRecordQueryReliable
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public byte RequiredReliabilityService;
        public ushort Pad1;
        public byte Pad2;
        public ushort EventType;
        public uint Time;
        public uint RecordIdCount;
        public byte[] RecordIdBytes;
    }

    public struct FastDisDesignator
    {
        public FastDisHeader Header;
        public FastDisEntityId DesignatingEntityId;
        public ushort CodeName;
        public FastDisEntityId DesignatedEntityId;
        public ushort DesignatorCode;
        public float DesignatorPower;
        public float DesignatorWavelength;
        public FastDisVec3F DesignatorSpotWrtDesignated;
        public FastDisWorldCoordinates DesignatorSpotLocation;
        public byte DeadReckoningAlgorithm;
        public ushort Padding1;
        public byte Padding2;
        public FastDisVec3F EntityLinearAcceleration;
    }

    public struct FastDisRadioEntityType
    {
        public byte EntityKind;
        public byte Domain;
        public ushort Country;
        public byte Category;
        public byte NomenclatureVersion;
        public ushort Nomenclature;
    }

    public struct FastDisModulationType
    {
        public ushort SpreadSpectrum;
        public ushort Major;
        public ushort Detail;
        public ushort System;
    }

    public struct FastDisSystemId
    {
        public ushort SystemType;
        public ushort SystemName;
        public byte SystemMode;
        public byte ChangeOptions;
    }

    public struct FastDisIffFundamentalData
    {
        public byte SystemStatus;
        public byte AlternateParameter4;
        public byte InformationLayers;
        public byte Modifier;
        public ushort Parameter1;
        public ushort Parameter2;
        public ushort Parameter3;
        public ushort Parameter4;
        public ushort Parameter5;
        public ushort Parameter6;
    }

    public struct FastDisTransmitter
    {
        public FastDisHeader Header;
        public FastDisEntityId EntityId;
        public ushort RadioId;
        public FastDisRadioEntityType RadioEntityType;
        public FastDisEntityType EntityType;
        public byte TransmitState;
        public byte InputSource;
        public ushort VariableTransmitterParameterCount;
        public FastDisWorldCoordinates AntennaLocation;
        public FastDisVec3F RelativeAntennaLocation;
        public ushort AntennaPatternType;
        public ushort AntennaPatternCount;
        public uint Frequency;
        public float TransmitFrequencyBandwidth;
        public float Power;
        public FastDisModulationType ModulationType;
        public ushort CryptoSystem;
        public ushort CryptoKeyId;
        public byte ModulationParameterCount;
        public ushort Padding2;
        public byte Padding3;
        public byte[] ModulationParameterBytes;
        public byte[] AntennaPatternBytes;
    }

    public struct FastDisSignal
    {
        public FastDisHeader Header;
        public FastDisEntityId EntityId;
        public ushort RadioId;
        public ushort EncodingScheme;
        public ushort TdlType;
        public uint SampleRate;
        public ushort DataLength;
        public ushort Samples;
        public byte[] DataBytes;
    }

    public struct FastDisReceiver
    {
        public FastDisHeader Header;
        public FastDisEntityId EntityId;
        public ushort RadioId;
        public ushort ReceiverState;
        public ushort Padding1;
        public float ReceivedPower;
        public FastDisEntityId TransmitterEntityId;
        public ushort TransmitterRadioId;
    }

    public struct FastDisElectronicEmissions
    {
        public FastDisHeader Header;
        public FastDisEntityId EmittingEntityId;
        public FastDisEventId EventId;
        public byte StateUpdateIndicator;
        public byte NumberOfSystems;
        public ushort Padding1;
        public byte[] SystemRecordBytes;
    }

    public struct FastDisOtherPdu
    {
        public FastDisHeader Header;
        public byte[] OpaquePayloadBytes;
    }

    public struct FastDisAggregateState
    {
        public FastDisHeader Header;
        public FastDisEntityId AggregateId;
        public byte ForceId;
        public byte AggregateStateValue;
        public FastDisEntityType AggregateType;
        public uint Formation;
        public byte AggregateMarkingCharacterSet;
        public byte[] AggregateMarkingBytes;
        public FastDisVec3F Dimensions;
        public FastDisEulerAngles Orientation;
        public FastDisWorldCoordinates CenterOfMass;
        public FastDisVec3F Velocity;
        public ushort NumberOfDisAggregates;
        public ushort NumberOfDisEntities;
        public ushort NumberOfSilentAggregateTypes;
        public ushort NumberOfSilentEntityTypes;
        public byte[] AggregateRecordBytes;
    }

    public struct FastDisIsGroupOf
    {
        public FastDisHeader Header;
        public FastDisEntityId GroupEntityId;
        public byte GroupedEntityCategory;
        public byte NumberOfGroupedEntities;
        public uint Pad2;
        public double Latitude;
        public double Longitude;
        public byte[] GroupedEntityDescriptionBytes;
    }

    public struct FastDisTransferControlRequest
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public byte RequiredReliabilityService;
        public byte TransferType;
        public FastDisEntityId TransferEntityId;
        public byte NumberOfRecordSets;
        public byte[] RecordSetBytes;
    }

    public struct FastDisTransferOwnership
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public uint RequestId;
        public byte RequiredReliabilityService;
        public byte TransferType;
        public FastDisEntityId TransferEntityId;
        public byte NumberOfRecordSets;
        public byte[] RecordSetBytes;
    }

    public struct FastDisIsPartOf
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public FastDisEntityId ReceivingEntityId;
        public ushort RelationshipNature;
        public ushort RelationshipPosition;
        public FastDisVec3F PartLocation;
        public ushort StationName;
        public ushort StationNumber;
        public FastDisEntityType PartEntityType;
    }

    public struct FastDisMinefieldState
    {
        public FastDisHeader Header;
        public FastDisEntityId MinefieldId;
        public ushort MinefieldSequence;
        public byte ForceId;
        public byte NumberOfPerimeterPoints;
        public FastDisEntityType MinefieldType;
        public ushort NumberOfMineTypes;
        public FastDisWorldCoordinates MinefieldLocation;
        public FastDisEulerAngles MinefieldOrientation;
        public ushort Appearance;
        public ushort ProtocolMode;
        public byte[] PerimeterPointBytes;
        public byte[] MineTypeBytes;
    }

    public struct FastDisMinefieldQuery
    {
        public FastDisHeader Header;
        public FastDisEntityId MinefieldId;
        public FastDisEntityId RequestingEntityId;
        public byte RequestId;
        public byte NumberOfPerimeterPoints;
        public byte Pad2;
        public byte NumberOfSensorTypes;
        public uint DataFilter;
        public FastDisEntityType RequestedMineType;
        public byte[] RequestedPerimeterPointBytes;
        public byte[] SensorTypeBytes;
    }

    public struct FastDisMinefieldData
    {
        public FastDisHeader Header;
        public FastDisEntityId MinefieldId;
        public FastDisEntityId RequestingEntityId;
        public ushort MinefieldSequenceNumber;
        public byte RequestId;
        public byte PduSequenceNumber;
        public byte NumberOfPdus;
        public byte NumberOfMinesInThisPdu;
        public byte NumberOfSensorTypes;
        public byte Pad2;
        public uint DataFilter;
        public FastDisEntityType MineType;
        public byte Pad3;
        public byte[] SensorTypeBytes;
        public byte[] MineLocationBytes;
    }

    public struct FastDisMinefieldResponseNack
    {
        public FastDisHeader Header;
        public FastDisEntityId MinefieldId;
        public FastDisEntityId RequestingEntityId;
        public byte RequestId;
        public byte NumberOfMissingPdus;
        public byte[] MissingPduSequenceNumberBytes;
    }

    public struct FastDisEnvironmentObjectType
    {
        public byte Domain;
        public byte Kind;
        public ushort Country;
        public byte Category;
        public byte Subcategory;
    }

    public struct FastDisLiveEntityId
    {
        public byte Site;
        public byte Application;
        public ushort Entity;
    }

    public struct FastDisLiveEventId
    {
        public byte Site;
        public byte Application;
        public ushort EventNumber;
    }

    public struct FastDisEnvironmentalProcess
    {
        public FastDisHeader Header;
        public FastDisEntityId EnvironmentalProcessId;
        public FastDisEntityType EnvironmentType;
        public byte ModelType;
        public byte EnvironmentStatus;
        public byte NumberOfEnvironmentRecords;
        public ushort SequenceNumber;
        public byte[] EnvironmentRecordBytes;
    }

    public struct FastDisGriddedData
    {
        public FastDisHeader Header;
        public FastDisEntityId EnvironmentalSimulationApplicationId;
        public ushort FieldNumber;
        public ushort PduNumber;
        public ushort PduTotal;
        public ushort CoordinateSystem;
        public byte NumberOfGridAxes;
        public byte ConstantGrid;
        public FastDisEntityType EnvironmentType;
        public FastDisEulerAngles Orientation;
        public ulong SampleTime;
        public uint TotalValues;
        public byte VectorDimension;
        public ushort Padding1;
        public byte Padding2;
        public byte[] GridDataBytes;
    }

    public struct FastDisPointObjectState
    {
        public FastDisHeader Header;
        public FastDisEntityId ObjectId;
        public FastDisEntityId ReferencedObjectId;
        public ushort UpdateNumber;
        public byte ForceId;
        public byte Modifications;
        public FastDisEnvironmentObjectType ObjectType;
        public FastDisWorldCoordinates ObjectLocation;
        public FastDisEulerAngles ObjectOrientation;
        public double ObjectAppearance;
        public FastDisSimulationAddress RequesterId;
        public FastDisSimulationAddress ReceivingId;
        public uint Pad2;
    }

    public struct FastDisLinearObjectState
    {
        public FastDisHeader Header;
        public FastDisEntityId ObjectId;
        public FastDisEntityId ReferencedObjectId;
        public ushort UpdateNumber;
        public byte ForceId;
        public byte NumberOfSegments;
        public FastDisSimulationAddress RequesterId;
        public FastDisSimulationAddress ReceivingId;
        public FastDisEnvironmentObjectType ObjectType;
        public byte[] LinearSegmentParameterBytes;
    }

    public struct FastDisArealObjectState
    {
        public FastDisHeader Header;
        public FastDisEntityId ObjectId;
        public FastDisEntityId ReferencedObjectId;
        public ushort UpdateNumber;
        public byte ForceId;
        public byte Modifications;
        public FastDisEntityType ObjectType;
        public byte[] ObjectAppearanceBytes;
        public ushort NumberOfPoints;
        public FastDisSimulationAddress RequesterId;
        public FastDisSimulationAddress ReceivingId;
        public byte[] ObjectLocationBytes;
    }

    public struct FastDisTspi
    {
        public FastDisHeader Header;
        public FastDisLiveEntityId LiveEntityId;
        public byte TspiFlag;
        public byte[] EntityLocationBytes;
        public byte[] EntityLinearVelocityBytes;
        public byte[] EntityOrientationBytes;
        public byte[] PositionErrorBytes;
        public byte[] OrientationErrorBytes;
        public byte[] DeadReckoningParameterBytes;
        public ushort MeasuredSpeed;
        public byte SystemSpecificDataLength;
        public byte[] SystemSpecificDataBytes;
    }

    public struct FastDisLiveEntityAppearance
    {
        public FastDisHeader Header;
        public FastDisLiveEntityId LiveEntityId;
        public ushort AppearanceFlags;
        public byte ForceId;
        public byte Padding1;
        public FastDisEntityType EntityType;
        public FastDisEntityType AlternateEntityType;
        public byte[] EntityMarking;
        public uint Capabilities;
        public byte[] AppearanceFieldBytes;
    }

    public struct FastDisArticulatedParts
    {
        public FastDisHeader Header;
        public FastDisLiveEntityId LiveEntityId;
        public byte NumberOfParameterRecords;
        public byte[] PaddingBytes;
        public byte[] VariableParameterBytes;
    }

    public struct FastDisLeFire
    {
        public FastDisHeader Header;
        public FastDisLiveEntityId FiringLiveEntityId;
        public byte Flags;
        public byte Padding1;
        public FastDisLiveEntityId TargetLiveEntityId;
        public FastDisLiveEntityId MunitionLiveEntityId;
        public FastDisLiveEventId EventId;
        public byte[] LocationBytes;
        public FastDisBurstDescriptor MunitionDescriptor;
        public byte[] VelocityBytes;
        public ushort Range;
    }

    public struct FastDisLeDetonation
    {
        public FastDisHeader Header;
        public FastDisLiveEntityId FiringLiveEntityId;
        public byte DetonationFlag1;
        public byte DetonationFlag2;
        public FastDisLiveEntityId TargetLiveEntityId;
        public FastDisLiveEntityId MunitionLiveEntityId;
        public FastDisLiveEventId EventId;
        public byte[] WorldLocationBytes;
        public byte[] VelocityBytes;
        public byte[] MunitionOrientationBytes;
        public FastDisBurstDescriptor MunitionDescriptor;
        public byte[] EntityLocationBytes;
        public byte DetonationResult;
        public byte Padding1;
    }

    public struct FastDisIffAtcNavAidsLayer1
    {
        public FastDisHeader Header;
        public FastDisEntityId EmittingEntityId;
        public FastDisEventId EventId;
        public FastDisVec3F Location;
        public FastDisSystemId SystemId;
        public ushort Padding2;
        public FastDisIffFundamentalData FundamentalParameters;
    }

    public struct FastDisIff
    {
        public FastDisHeader Header;
        public FastDisEntityId EmittingEntityId;
        public FastDisEventId EventId;
        public FastDisVec3F Location;
        public FastDisSystemId SystemId;
        public ushort Padding2;
        public FastDisIffFundamentalData FundamentalParameters;
    }

    public struct FastDisUa
    {
        public FastDisHeader Header;
        public FastDisEntityId EmittingEntityId;
        public FastDisEventId EventId;
        public sbyte StateChangeIndicator;
        public byte Padding1;
        public ushort PassiveParameterIndex;
        public byte PropulsionPlantConfiguration;
        public byte NumberOfShafts;
        public byte NumberOfApas;
        public byte NumberOfUaEmitterSystems;
        public byte[] UaRecordBytes;
    }

    public struct FastDisSees
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingEntityId;
        public ushort InfraredSignatureRepresentationIndex;
        public ushort AcousticSignatureRepresentationIndex;
        public ushort RadarCrossSectionSignatureRepresentationIndex;
        public ushort NumberOfPropulsionSystems;
        public ushort NumberOfVectoringNozzleSystems;
        public byte[] SupplementalEmissionRecordBytes;
    }

    public struct FastDisIntercomSignal
    {
        public FastDisHeader Header;
        public FastDisEntityId EntityId;
        public ushort CommunicationsDeviceId;
        public ushort EncodingScheme;
        public ushort TdlType;
        public uint SampleRate;
        public ushort DataLength;
        public ushort Samples;
        public byte[] DataBytes;
    }

    public struct FastDisIntercomControl
    {
        public FastDisHeader Header;
        public byte ControlType;
        public byte CommunicationsChannelType;
        public FastDisEntityId SourceEntityId;
        public byte SourceCommunicationsDeviceId;
        public byte SourceLineId;
        public byte TransmitPriority;
        public byte TransmitLineState;
        public byte Command;
        public FastDisEntityId MasterEntityId;
        public ushort MasterCommunicationsDeviceId;
        public uint IntercomParametersLength;
        public byte[] IntercomParametersBytes;
    }

    public struct FastDisAttribute
    {
        public FastDisHeader Header;
        public FastDisSimulationAddress OriginatingSimulationAddress;
        public int Padding1;
        public short Padding2;
        public byte AttributeRecordPduType;
        public byte AttributeRecordProtocolVersion;
        public uint MasterAttributeRecordType;
        public byte ActionCode;
        public sbyte Padding3;
        public ushort NumberAttributeRecordSet;
        public byte[] AttributeRecordSetBytes;
    }

    public struct FastDisDirectedEnergyFire
    {
        public FastDisHeader Header;
        public FastDisEntityId FiringEntityId;
        public FastDisEntityId TargetEntityId;
        public FastDisEntityType MunitionType;
        public FastDisClockTime ShotStartTime;
        public float CommulativeShotTime;
        public FastDisVec3F ApertureEmitterLocation;
        public float ApertureDiameter;
        public float Wavelength;
        public float PeakIrradiance;
        public float PulseRepetitionFrequency;
        public int PulseWidth;
        public int Flags;
        public sbyte PulseShape;
        public byte Padding1;
        public uint Padding2;
        public ushort Padding3;
        public ushort NumberOfDeRecords;
        public byte[] DeRecordBytes;
    }

    public struct FastDisEntityDamageStatus
    {
        public FastDisHeader Header;
        public FastDisEntityId FiringEntityId;
        public FastDisEntityId TargetEntityId;
        public FastDisEntityId DamagedEntityId;
        public ushort Padding1;
        public ushort Padding2;
        public ushort NumberOfDamageDescription;
        public byte[] DamageDescriptionRecordBytes;
    }

    public struct FastDisInformationOperationsAction
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingSimId;
        public FastDisEntityId ReceivingSimId;
        public uint RequestId;
        public ushort IoWarfareType;
        public ushort IoSimulationSource;
        public ushort IoActionType;
        public ushort IoActionPhase;
        public uint Padding1;
        public FastDisEntityId IoAttackerId;
        public FastDisEntityId IoPrimaryTargetId;
        public ushort Padding2;
        public ushort NumberOfIoRecords;
        public byte[] IoRecordBytes;
    }

    public struct FastDisInformationOperationsReport
    {
        public FastDisHeader Header;
        public FastDisEntityId OriginatingSimId;
        public ushort IoSimSource;
        public byte IoReportType;
        public byte Padding1;
        public FastDisEntityId IoAttackerId;
        public FastDisEntityId IoPrimaryTargetId;
        public ushort Padding2;
        public ushort Padding3;
        public ushort NumberOfIoRecords;
        public byte[] IoRecordBytes;
    }

    public struct FastDisServiceRequest
    {
        public FastDisHeader Header;
        public FastDisEntityId RequestingEntityId;
        public FastDisEntityId ServicingEntityId;
        public byte ServiceTypeRequested;
        public byte NumberOfSupplyTypes;
        public short ServiceRequestPadding;
        public byte[] SupplyBytes;
    }

    public struct FastDisResupplyOffer
    {
        public FastDisHeader Header;
        public FastDisEntityId ReceivingEntityId;
        public FastDisEntityId SupplyingEntityId;
        public byte NumberOfSupplyTypes;
        public byte[] PaddingBytes;
        public byte[] SupplyBytes;
    }

    public struct FastDisResupplyReceived
    {
        public FastDisHeader Header;
        public FastDisEntityId ReceivingEntityId;
        public FastDisEntityId SupplyingEntityId;
        public byte NumberOfSupplyTypes;
        public ushort Padding1;
        public byte Padding2;
        public byte[] SupplyBytes;
    }

    public struct FastDisResupplyCancel
    {
        public FastDisHeader Header;
        public FastDisEntityId ReceivingEntityId;
        public FastDisEntityId SupplyingEntityId;
    }

    public struct FastDisRepairComplete
    {
        public FastDisHeader Header;
        public FastDisEntityId ReceivingEntityId;
        public FastDisEntityId RepairingEntityId;
        public ushort Repair;
        public short Padding2;
    }

    public struct FastDisRepairResponse
    {
        public FastDisHeader Header;
        public FastDisEntityId ReceivingEntityId;
        public FastDisEntityId RepairingEntityId;
        public byte RepairResult;
        public ushort Padding1;
        public byte Padding2;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisFire
    {
        public FastDisHeader Header;
        public FastDisEntityId FiringEntityId;
        public FastDisEntityId TargetEntityId;
        public FastDisEntityId MunitionEntityId;
        public FastDisEventId EventId;
        public uint FireMissionIndex;
        public FastDisWorldCoordinates WorldLocation;
        public FastDisBurstDescriptor MunitionDescriptor;
        public FastDisVec3F Velocity;
        public float RangeToTarget;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisDetonation
    {
        public FastDisHeader Header;
        public FastDisEntityId FiringEntityId;
        public FastDisEntityId TargetEntityId;
        public FastDisEntityId ExplodingEntityId;
        public FastDisEventId EventId;
        public FastDisVec3F Velocity;
        public FastDisWorldCoordinates WorldLocation;
        public FastDisBurstDescriptor MunitionDescriptor;
        public FastDisVec3F LocationInEntityCoordinates;
        public byte DetonationResult;
        public byte VariableParameterCount;
        public ushort Padding1;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisCollision
    {
        public FastDisHeader Header;
        public FastDisEntityId IssuingEntityId;
        public FastDisEntityId CollidingEntityId;
        public FastDisEventId EventId;
        public byte CollisionType;
        public byte Padding1;
        public FastDisVec3F Velocity;
        public float Mass;
        public FastDisVec3F Location;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisCollisionElastic
    {
        public FastDisHeader Header;
        public FastDisEntityId IssuingEntityId;
        public FastDisEntityId CollidingEntityId;
        public FastDisEventId EventId;
        public ushort Padding1;
        public FastDisVec3F ContactVelocity;
        public float Mass;
        public FastDisVec3F Location;
        public float CollisionResultXx;
        public float CollisionResultXy;
        public float CollisionResultXz;
        public float CollisionResultYy;
        public float CollisionResultYz;
        public float CollisionResultZz;
        public FastDisVec3F UnitSurfaceNormal;
        public float CoefficientOfRestitution;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisVec3F
    {
        public float X;
        public float Y;
        public float Z;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisEntityType
    {
        public byte EntityKind;
        public byte Domain;
        public ushort Country;
        public byte Category;
        public byte Subcategory;
        public byte Specific;
        public byte Extra;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisWorldCoordinates
    {
        public double X;
        public double Y;
        public double Z;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisEulerAngles
    {
        public float Psi;
        public float Theta;
        public float Phi;
    }

    public readonly struct FastDisPacketView
    {
        public FastDisPacketView(byte[] bytes)
        {
            Bytes = bytes ?? Array.Empty<byte>();
        }

        public byte[] Bytes { get; }
        public int Length => Bytes.Length;
    }
}
