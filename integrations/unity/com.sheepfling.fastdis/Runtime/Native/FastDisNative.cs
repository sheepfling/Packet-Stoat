using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace FastDIS.Native
{
    public static class FastDisNative
    {
        private const string LibraryName = "fastdis";
        public const uint AbiVersion = 16;
        public const uint FastDisFlagAllowTruncated = 0x00000001u;
        public const ulong FastDisEsFieldForceId = 0x0000000000000004UL;
        public const ulong FastDisEsFieldLocation = 0x0000000000000080UL;
        public const ulong FastDisEsFieldLinearVelocity = 0x0000000000000040UL;
        public const int FastDisOk = 0;

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        internal static extern uint fastdis_abi_version();

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr fastdis_version_string();

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_dead_reckoning_algorithm_known(byte algorithm);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_extrapolate_entity_transform_dead_reckoning(
            ref FastDisEntityTransform transform,
            double deltaSeconds,
            out FastDisEntityTransform outTransform);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_entity_transform(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisEntityTransform outTransform);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_fire(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisFire outFire);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_detonation(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisDetonation outDetonation);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_collision(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisCollision outCollision);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_collision_elastic(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisCollisionElastic outCollisionElastic);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_designator(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisDesignator outDesignator);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_transmitter(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeTransmitter outTransmitter);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_other_pdu(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeOtherPdu outOther);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_aggregate_state(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeAggregateState outAggregate);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_is_group_of(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeIsGroupOf outGroup);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_transfer_control_request(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeTransferControlRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_transfer_ownership(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeTransferOwnership outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_is_part_of(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeIsPartOf outPart);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_minefield_state(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeMinefieldState outState);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_minefield_query(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeMinefieldQuery outQuery);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_minefield_data(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeMinefieldData outData);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_minefield_response_nack(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeMinefieldResponseNack outNack);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_environmental_process(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeEnvironmentalProcess outProcess);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_gridded_data(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeGriddedData outGrid);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_point_object_state(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativePointObjectState outPoint);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_linear_object_state(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeLinearObjectState outLinear);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_areal_object_state(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeArealObjectState outAreal);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_tspi(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeTspi outTspi);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_live_entity_appearance(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeLiveEntityAppearance outAppearance);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_articulated_parts(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeArticulatedParts outParts);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_le_fire(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeLeFire outFire);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_le_detonation(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeLeDetonation outDetonation);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_signal(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeSignal outSignal);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_receiver(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisReceiver outReceiver);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_electronic_emissions(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeElectronicEmissions outEmissions);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_iff_atc_navaids_layer1(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisIffAtcNavAidsLayer1 outIff);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_iff(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisIff outIff);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_ua(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeUa outUa);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_sees(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeSees outSees);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_intercom_signal(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeIntercomSignal outSignal);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_intercom_control(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeIntercomControl outControl);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_attribute(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeAttribute outAttribute);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_directed_energy_fire(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeDirectedEnergyFire outDirectedEnergyFire);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_entity_damage_status(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeEntityDamageStatus outEntityDamageStatus);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_information_operations_action(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeInformationOperationsAction outAction);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_information_operations_report(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeInformationOperationsReport outReport);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_service_request(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeServiceRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_resupply_offer(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeResupplyOffer outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_resupply_received(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeResupplyReceived outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_resupply_cancel(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeResupplyCancel outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_repair_complete(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeRepairComplete outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_repair_response(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeRepairResponse outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_create_entity(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisSimulationManagementRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_remove_entity(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisSimulationManagementRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_start_resume(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisStartResume outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_stop_freeze(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisStopFreeze outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_acknowledge(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisAcknowledge outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_action_request(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeActionRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_action_response(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeActionResponse outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_data_query(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeDataQuery outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_set_data(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeSetData outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_data(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeSetData outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_event_report(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeEventReport outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_comment(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeComment outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_create_entity_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisSimulationManagementReliableRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_remove_entity_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisSimulationManagementReliableRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_start_resume_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisStartResumeReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_stop_freeze_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisStopFreezeReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_acknowledge_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisAcknowledge outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_action_request_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeActionRequestReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_action_response_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeActionResponseReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_data_query_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeDataQueryReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_set_data_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeSetDataReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_data_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeDataReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_event_report_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeEventReportReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_comment_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeCommentReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_record_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeRecordReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_set_record_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeSetRecordReliable outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_record_query_reliable(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out NativeRecordQueryReliable outRequest);

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeDatumRecordSetView
        {
            public IntPtr DatumRecordBytes;
            public UIntPtr DatumRecordBytesSize;
            public IntPtr DatumRecordBytesUser;
            public uint NumberOfFixedDatumRecords;
            public uint NumberOfVariableDatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeCountedBytesView
        {
            public IntPtr Bytes;
            public UIntPtr BytesSize;
            public IntPtr BytesUser;
            public uint Count;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeServiceRequest
        {
            public FastDisHeader Header;
            public FastDisEntityId RequestingEntityId;
            public FastDisEntityId ServicingEntityId;
            public byte ServiceTypeRequested;
            public byte NumberOfSupplyTypes;
            public short ServiceRequestPadding;
            public NativeCountedBytesView Supplies;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeResupplyOffer
        {
            public FastDisHeader Header;
            public FastDisEntityId ReceivingEntityId;
            public FastDisEntityId SupplyingEntityId;
            public byte NumberOfSupplyTypes;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
            public byte[] PaddingBytes;
            public NativeCountedBytesView Supplies;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeResupplyReceived
        {
            public FastDisHeader Header;
            public FastDisEntityId ReceivingEntityId;
            public FastDisEntityId SupplyingEntityId;
            public byte NumberOfSupplyTypes;
            public ushort Padding1;
            public byte Padding2;
            public NativeCountedBytesView Supplies;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeResupplyCancel
        {
            public FastDisHeader Header;
            public FastDisEntityId ReceivingEntityId;
            public FastDisEntityId SupplyingEntityId;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeRepairComplete
        {
            public FastDisHeader Header;
            public FastDisEntityId ReceivingEntityId;
            public FastDisEntityId RepairingEntityId;
            public ushort Repair;
            public short Padding2;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeRepairResponse
        {
            public FastDisHeader Header;
            public FastDisEntityId ReceivingEntityId;
            public FastDisEntityId RepairingEntityId;
            public byte RepairResult;
            public ushort Padding1;
            public byte Padding2;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeSignal
        {
            public FastDisHeader Header;
            public FastDisEntityId EntityId;
            public ushort RadioId;
            public ushort EncodingScheme;
            public ushort TdlType;
            public uint SampleRate;
            public ushort DataLength;
            public ushort Samples;
            public NativeCountedBytesView Data;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeIntercomSignal
        {
            public FastDisHeader Header;
            public FastDisEntityId EntityId;
            public ushort CommunicationsDeviceId;
            public ushort EncodingScheme;
            public ushort TdlType;
            public uint SampleRate;
            public ushort DataLength;
            public ushort Samples;
            public NativeCountedBytesView Data;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeTransmitter
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
            public NativeCountedBytesView ModulationParameters;
            public NativeCountedBytesView AntennaPatterns;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeIntercomControl
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
            public NativeCountedBytesView IntercomParameters;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeSimulationAddress
        {
            public ushort Site;
            public ushort Application;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeAttribute
        {
            public FastDisHeader Header;
            public NativeSimulationAddress OriginatingSimulationAddress;
            public int Padding1;
            public short Padding2;
            public byte AttributeRecordPduType;
            public byte AttributeRecordProtocolVersion;
            public uint MasterAttributeRecordType;
            public byte ActionCode;
            public sbyte Padding3;
            public ushort NumberAttributeRecordSet;
            public NativeCountedBytesView AttributeRecordSets;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeDirectedEnergyFire
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
            public NativeCountedBytesView DeRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeEntityDamageStatus
        {
            public FastDisHeader Header;
            public FastDisEntityId FiringEntityId;
            public FastDisEntityId TargetEntityId;
            public FastDisEntityId DamagedEntityId;
            public ushort Padding1;
            public ushort Padding2;
            public ushort NumberOfDamageDescription;
            public NativeCountedBytesView DamageDescriptionRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeElectronicEmissions
        {
            public FastDisHeader Header;
            public FastDisEntityId EmittingEntityId;
            public FastDisEventId EventId;
            public byte StateUpdateIndicator;
            public byte NumberOfSystems;
            public ushort Padding1;
            public NativeCountedBytesView SystemRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeOtherPdu
        {
            public FastDisHeader Header;
            public NativeCountedBytesView OpaquePayload;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeAggregateState
        {
            public FastDisHeader Header;
            public FastDisEntityId AggregateId;
            public byte ForceId;
            public byte AggregateStateValue;
            public FastDisEntityType AggregateType;
            public uint Formation;
            public byte AggregateMarkingCharacterSet;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 32)]
            public byte[] AggregateMarking;
            public FastDisVec3F Dimensions;
            public FastDisEulerAngles Orientation;
            public FastDisWorldCoordinates CenterOfMass;
            public FastDisVec3F Velocity;
            public ushort NumberOfDisAggregates;
            public ushort NumberOfDisEntities;
            public ushort NumberOfSilentAggregateTypes;
            public ushort NumberOfSilentEntityTypes;
            public NativeCountedBytesView AggregateRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeIsGroupOf
        {
            public FastDisHeader Header;
            public FastDisEntityId GroupEntityId;
            public byte GroupedEntityCategory;
            public byte NumberOfGroupedEntities;
            public uint Pad2;
            public double Latitude;
            public double Longitude;
            public NativeCountedBytesView GroupedEntityDescriptions;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeTransferControlRequest
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public byte RequiredReliabilityService;
            public byte TransferType;
            public FastDisEntityId TransferEntityId;
            public byte NumberOfRecordSets;
            public NativeCountedBytesView RecordSets;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeTransferOwnership
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public byte RequiredReliabilityService;
            public byte TransferType;
            public FastDisEntityId TransferEntityId;
            public byte NumberOfRecordSets;
            public NativeCountedBytesView RecordSets;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeIsPartOf
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

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeMinefieldState
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
            public NativeCountedBytesView PerimeterPoints;
            public NativeCountedBytesView MineTypes;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeMinefieldQuery
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
            public NativeCountedBytesView RequestedPerimeterPoints;
            public NativeCountedBytesView SensorTypes;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeMinefieldData
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
            public NativeCountedBytesView SensorTypes;
            public NativeCountedBytesView MineLocations;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeMinefieldResponseNack
        {
            public FastDisHeader Header;
            public FastDisEntityId MinefieldId;
            public FastDisEntityId RequestingEntityId;
            public byte RequestId;
            public byte NumberOfMissingPdus;
            public NativeCountedBytesView MissingPduSequenceNumbers;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeEnvironmentObjectType
        {
            public byte Domain;
            public byte Kind;
            public ushort Country;
            public byte Category;
            public byte Subcategory;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeLiveEntityId
        {
            public byte Site;
            public byte Application;
            public ushort Entity;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeLiveEventId
        {
            public byte Site;
            public byte Application;
            public ushort EventNumber;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeEnvironmentalProcess
        {
            public FastDisHeader Header;
            public FastDisEntityId EnvironmentalProcessId;
            public FastDisEntityType EnvironmentType;
            public byte ModelType;
            public byte EnvironmentStatus;
            public byte NumberOfEnvironmentRecords;
            public ushort SequenceNumber;
            public NativeCountedBytesView EnvironmentRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeGriddedData
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
            public NativeCountedBytesView GridData;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativePointObjectState
        {
            public FastDisHeader Header;
            public FastDisEntityId ObjectId;
            public FastDisEntityId ReferencedObjectId;
            public ushort UpdateNumber;
            public byte ForceId;
            public byte Modifications;
            public NativeEnvironmentObjectType ObjectType;
            public FastDisWorldCoordinates ObjectLocation;
            public FastDisEulerAngles ObjectOrientation;
            public double ObjectAppearance;
            public FastDisSimulationAddress RequesterId;
            public FastDisSimulationAddress ReceivingId;
            public uint Pad2;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeLinearObjectState
        {
            public FastDisHeader Header;
            public FastDisEntityId ObjectId;
            public FastDisEntityId ReferencedObjectId;
            public ushort UpdateNumber;
            public byte ForceId;
            public byte NumberOfSegments;
            public FastDisSimulationAddress RequesterId;
            public FastDisSimulationAddress ReceivingId;
            public NativeEnvironmentObjectType ObjectType;
            public NativeCountedBytesView LinearSegmentParameters;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeArealObjectState
        {
            public FastDisHeader Header;
            public FastDisEntityId ObjectId;
            public FastDisEntityId ReferencedObjectId;
            public ushort UpdateNumber;
            public byte ForceId;
            public byte Modifications;
            public FastDisEntityType ObjectType;
            public NativeCountedBytesView ObjectAppearance;
            public ushort NumberOfPoints;
            public FastDisSimulationAddress RequesterId;
            public FastDisSimulationAddress ReceivingId;
            public NativeCountedBytesView ObjectLocations;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeTspi
        {
            public FastDisHeader Header;
            public NativeLiveEntityId LiveEntityId;
            public byte TspiFlag;
            public NativeCountedBytesView EntityLocation;
            public NativeCountedBytesView EntityLinearVelocity;
            public NativeCountedBytesView EntityOrientation;
            public NativeCountedBytesView PositionError;
            public NativeCountedBytesView OrientationError;
            public NativeCountedBytesView DeadReckoningParameters;
            public ushort MeasuredSpeed;
            public byte SystemSpecificDataLength;
            public NativeCountedBytesView SystemSpecificData;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeLiveEntityAppearance
        {
            public FastDisHeader Header;
            public NativeLiveEntityId LiveEntityId;
            public ushort AppearanceFlags;
            public byte ForceId;
            public byte Padding1;
            public FastDisEntityType EntityType;
            public FastDisEntityType AlternateEntityType;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 12)]
            public byte[] EntityMarking;
            public uint Capabilities;
            public NativeCountedBytesView AppearanceFields;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeArticulatedParts
        {
            public FastDisHeader Header;
            public NativeLiveEntityId LiveEntityId;
            public byte NumberOfParameterRecords;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
            public byte[] Padding;
            public NativeCountedBytesView VariableParameters;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeLeFire
        {
            public FastDisHeader Header;
            public NativeLiveEntityId FiringLiveEntityId;
            public byte Flags;
            public byte Padding1;
            public NativeLiveEntityId TargetLiveEntityId;
            public NativeLiveEntityId MunitionLiveEntityId;
            public NativeLiveEventId EventId;
            public NativeCountedBytesView Location;
            public FastDisBurstDescriptor MunitionDescriptor;
            public NativeCountedBytesView Velocity;
            public ushort Range;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeLeDetonation
        {
            public FastDisHeader Header;
            public NativeLiveEntityId FiringLiveEntityId;
            public byte DetonationFlag1;
            public byte DetonationFlag2;
            public NativeLiveEntityId TargetLiveEntityId;
            public NativeLiveEntityId MunitionLiveEntityId;
            public NativeLiveEventId EventId;
            public NativeCountedBytesView WorldLocation;
            public NativeCountedBytesView Velocity;
            public NativeCountedBytesView MunitionOrientation;
            public FastDisBurstDescriptor MunitionDescriptor;
            public NativeCountedBytesView EntityLocation;
            public byte DetonationResult;
            public byte Padding1;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeUa
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
            public NativeCountedBytesView UaRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeSees
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public ushort InfraredSignatureRepresentationIndex;
            public ushort AcousticSignatureRepresentationIndex;
            public ushort RadarCrossSectionSignatureRepresentationIndex;
            public ushort NumberOfPropulsionSystems;
            public ushort NumberOfVectoringNozzleSystems;
            public NativeCountedBytesView SupplementalEmissionRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeInformationOperationsAction
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
            public NativeCountedBytesView IoRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeInformationOperationsReport
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
            public NativeCountedBytesView IoRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeActionRequest
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public uint ActionId;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeActionResponse
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public uint RequestStatus;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeDataQuery
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public FastDisClockTime TimeInterval;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeSetData
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public uint Padding1;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeEventReport
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint EventType;
            public uint Padding1;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeComment
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeActionRequestReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public byte RequiredReliabilityService;
            public ushort Pad1;
            public byte Pad2;
            public uint RequestId;
            public uint ActionId;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeActionResponseReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public uint ResponseStatus;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeDataQueryReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public byte RequiredReliabilityService;
            public ushort Pad1;
            public byte Pad2;
            public uint RequestId;
            public FastDisClockTime TimeInterval;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeSetDataReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public byte RequiredReliabilityService;
            public ushort Pad1;
            public byte Pad2;
            public uint RequestId;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeDataReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public byte RequiredReliabilityService;
            public ushort Pad1;
            public byte Pad2;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeEventReportReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint EventType;
            public uint Pad1;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeCommentReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public NativeDatumRecordSetView DatumRecords;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeRecordReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public byte RequiredReliabilityService;
            public byte Pad1;
            public ushort EventType;
            public NativeCountedBytesView RecordSets;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeSetRecordReliable
        {
            public FastDisHeader Header;
            public FastDisEntityId OriginatingEntityId;
            public FastDisEntityId ReceivingEntityId;
            public uint RequestId;
            public byte RequiredReliabilityService;
            public ushort Pad1;
            public byte Pad2;
            public NativeCountedBytesView RecordSets;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeRecordQueryReliable
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
            public NativeCountedBytesView RecordIds;
        }

        private static byte[] CopyDatumBytes(NativeDatumRecordSetView view)
        {
            int size = checked((int)view.DatumRecordBytesSize);
            if (view.DatumRecordBytes == IntPtr.Zero || size <= 0)
            {
                return Array.Empty<byte>();
            }

            byte[] bytes = new byte[size];
            Marshal.Copy(view.DatumRecordBytes, bytes, 0, size);
            return bytes;
        }

        private static byte[] CopyBytes(NativeCountedBytesView view)
        {
            int size = checked((int)view.BytesSize);
            if (view.Bytes == IntPtr.Zero || size <= 0)
            {
                return Array.Empty<byte>();
            }

            byte[] bytes = new byte[size];
            Marshal.Copy(view.Bytes, bytes, 0, size);
            return bytes;
        }

        public static bool TryGetAbiVersion(out uint abiVersion)
        {
            try
            {
                abiVersion = fastdis_abi_version();
                return true;
            }
            catch (DllNotFoundException)
            {
                abiVersion = 0;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                abiVersion = 0;
                return false;
            }
        }

        public static bool TryParseEntityTransform(
            byte[] packet,
            out FastDisEntityTransform transform,
            uint flags = 0,
            bool allowTruncated = false)
        {
            transform = default;
            if (packet == null || packet.Length == 0)
            {
                return false;
            }

            GCHandle handle = default;
            try
            {
                handle = GCHandle.Alloc(packet, GCHandleType.Pinned);
                uint combinedFlags = flags | (allowTruncated ? FastDisFlagAllowTruncated : 0u);
                int rc = fastdis_parse_entity_transform(
                    handle.AddrOfPinnedObject(),
                    (UIntPtr)(uint)packet.Length,
                    combinedFlags,
                    out transform);
                return rc == FastDisOk;
            }
            catch (DllNotFoundException)
            {
                transform = default;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                transform = default;
                return false;
            }
            finally
            {
                if (handle.IsAllocated)
                {
                    handle.Free();
                }
            }
        }

        public static bool DeadReckoningAlgorithmKnown(byte algorithm)
        {
            try
            {
                return fastdis_dead_reckoning_algorithm_known(algorithm) != 0;
            }
            catch (DllNotFoundException)
            {
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                return false;
            }
        }

        public static bool TryExtrapolateEntityTransformDeadReckoning(
            FastDisEntityTransform transform,
            double deltaSeconds,
            out FastDisEntityTransform outTransform)
        {
            outTransform = transform;
            if (deltaSeconds < 0.0)
            {
                return false;
            }

            try
            {
                return fastdis_extrapolate_entity_transform_dead_reckoning(ref transform, deltaSeconds, out outTransform) == FastDisOk;
            }
            catch (DllNotFoundException)
            {
                outTransform = transform;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                outTransform = transform;
                return false;
            }
        }

        public static bool TryParseCreateEntity(
            byte[] packet,
            out FastDisSimulationManagementRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_create_entity, out request);
        }

        public static bool TryParseRemoveEntity(
            byte[] packet,
            out FastDisSimulationManagementRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_remove_entity, out request);
        }

        public static bool TryParseStartResume(
            byte[] packet,
            out FastDisStartResume request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_start_resume, out request);
        }

        public static bool TryParseStopFreeze(
            byte[] packet,
            out FastDisStopFreeze request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_stop_freeze, out request);
        }

        public static bool TryParseAcknowledge(
            byte[] packet,
            out FastDisAcknowledge request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_acknowledge, out request);
        }

        public static bool TryParseActionRequest(
            byte[] packet,
            out FastDisActionRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeActionRequest, FastDisActionRequest>(packet, flags, allowTruncated, fastdis_parse_action_request, out request,
                native => new FastDisActionRequest
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    ActionId = native.ActionId,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseActionResponse(
            byte[] packet,
            out FastDisActionResponse request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeActionResponse, FastDisActionResponse>(packet, flags, allowTruncated, fastdis_parse_action_response, out request,
                native => new FastDisActionResponse
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequestStatus = native.RequestStatus,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseDataQuery(
            byte[] packet,
            out FastDisDataQuery request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeDataQuery, FastDisDataQuery>(packet, flags, allowTruncated, fastdis_parse_data_query, out request,
                native => new FastDisDataQuery
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    TimeInterval = native.TimeInterval,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseSetData(
            byte[] packet,
            out FastDisSetData request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeSetData, FastDisSetData>(packet, flags, allowTruncated, fastdis_parse_set_data, out request,
                native => new FastDisSetData
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    Padding1 = native.Padding1,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseData(
            byte[] packet,
            out FastDisSetData request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeSetData, FastDisSetData>(packet, flags, allowTruncated, fastdis_parse_data, out request,
                native => new FastDisSetData
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    Padding1 = native.Padding1,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseEventReport(
            byte[] packet,
            out FastDisEventReport request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeEventReport, FastDisEventReport>(packet, flags, allowTruncated, fastdis_parse_event_report, out request,
                native => new FastDisEventReport
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    EventType = native.EventType,
                    Padding1 = native.Padding1,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseComment(
            byte[] packet,
            out FastDisComment request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeComment, FastDisComment>(packet, flags, allowTruncated, fastdis_parse_comment, out request,
                native => new FastDisComment
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseCreateEntityReliable(
            byte[] packet,
            out FastDisSimulationManagementReliableRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_create_entity_reliable, out request);
        }

        public static bool TryParseRemoveEntityReliable(
            byte[] packet,
            out FastDisSimulationManagementReliableRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_remove_entity_reliable, out request);
        }

        public static bool TryParseStartResumeReliable(
            byte[] packet,
            out FastDisStartResumeReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_start_resume_reliable, out request);
        }

        public static bool TryParseStopFreezeReliable(
            byte[] packet,
            out FastDisStopFreezeReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_stop_freeze_reliable, out request);
        }

        public static bool TryParseAcknowledgeReliable(
            byte[] packet,
            out FastDisAcknowledge request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_acknowledge_reliable, out request);
        }

        public static bool TryParseActionRequestReliable(
            byte[] packet,
            out FastDisActionRequestReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeActionRequestReliable, FastDisActionRequestReliable>(packet, flags, allowTruncated, fastdis_parse_action_request_reliable, out request,
                native => new FastDisActionRequestReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    Pad2 = native.Pad2,
                    RequestId = native.RequestId,
                    ActionId = native.ActionId,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseActionResponseReliable(
            byte[] packet,
            out FastDisActionResponseReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeActionResponseReliable, FastDisActionResponseReliable>(packet, flags, allowTruncated, fastdis_parse_action_response_reliable, out request,
                native => new FastDisActionResponseReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    ResponseStatus = native.ResponseStatus,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseDataQueryReliable(
            byte[] packet,
            out FastDisDataQueryReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeDataQueryReliable, FastDisDataQueryReliable>(packet, flags, allowTruncated, fastdis_parse_data_query_reliable, out request,
                native => new FastDisDataQueryReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    Pad2 = native.Pad2,
                    RequestId = native.RequestId,
                    TimeInterval = native.TimeInterval,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseSetDataReliable(
            byte[] packet,
            out FastDisSetDataReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeSetDataReliable, FastDisSetDataReliable>(packet, flags, allowTruncated, fastdis_parse_set_data_reliable, out request,
                native => new FastDisSetDataReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    Pad2 = native.Pad2,
                    RequestId = native.RequestId,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseDataReliable(
            byte[] packet,
            out FastDisDataReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeDataReliable, FastDisDataReliable>(packet, flags, allowTruncated, fastdis_parse_data_reliable, out request,
                native => new FastDisDataReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    Pad2 = native.Pad2,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseEventReportReliable(
            byte[] packet,
            out FastDisEventReportReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeEventReportReliable, FastDisEventReportReliable>(packet, flags, allowTruncated, fastdis_parse_event_report_reliable, out request,
                native => new FastDisEventReportReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    EventType = native.EventType,
                    Pad1 = native.Pad1,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseCommentReliable(
            byte[] packet,
            out FastDisCommentReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeCommentReliable, FastDisCommentReliable>(packet, flags, allowTruncated, fastdis_parse_comment_reliable, out request,
                native => new FastDisCommentReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    NumberOfFixedDatumRecords = native.DatumRecords.NumberOfFixedDatumRecords,
                    NumberOfVariableDatumRecords = native.DatumRecords.NumberOfVariableDatumRecords,
                    DatumRecordBytes = CopyDatumBytes(native.DatumRecords),
                });
        }

        public static bool TryParseRecordReliable(
            byte[] packet,
            out FastDisRecordReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeRecordReliable, FastDisRecordReliable>(packet, flags, allowTruncated, fastdis_parse_record_reliable, out request,
                native => new FastDisRecordReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    EventType = native.EventType,
                    RecordSetCount = native.RecordSets.Count,
                    RecordSetBytes = CopyBytes(native.RecordSets),
                });
        }

        public static bool TryParseSetRecordReliable(
            byte[] packet,
            out FastDisSetRecordReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeSetRecordReliable, FastDisSetRecordReliable>(packet, flags, allowTruncated, fastdis_parse_set_record_reliable, out request,
                native => new FastDisSetRecordReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    Pad2 = native.Pad2,
                    RecordSetCount = native.RecordSets.Count,
                    RecordSetBytes = CopyBytes(native.RecordSets),
                });
        }

        public static bool TryParseRecordQueryReliable(
            byte[] packet,
            out FastDisRecordQueryReliable request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeRecordQueryReliable, FastDisRecordQueryReliable>(packet, flags, allowTruncated, fastdis_parse_record_query_reliable, out request,
                native => new FastDisRecordQueryReliable
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    Pad1 = native.Pad1,
                    Pad2 = native.Pad2,
                    EventType = native.EventType,
                    Time = native.Time,
                    RecordIdCount = native.RecordIds.Count,
                    RecordIdBytes = CopyBytes(native.RecordIds),
                });
        }

        public static bool TryParseFire(
            byte[] packet,
            out FastDisFire fire,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_fire, out fire);
        }

        public static bool TryParseDetonation(
            byte[] packet,
            out FastDisDetonation detonation,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_detonation, out detonation);
        }

        public static bool TryParseDesignator(
            byte[] packet,
            out FastDisDesignator designator,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_designator, out designator);
        }

        public static bool TryParseTransmitter(
            byte[] packet,
            out FastDisTransmitter transmitter,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeTransmitter, FastDisTransmitter>(packet, flags, allowTruncated, fastdis_parse_transmitter, out transmitter,
                native => new FastDisTransmitter
                {
                    Header = native.Header,
                    EntityId = native.EntityId,
                    RadioId = native.RadioId,
                    RadioEntityType = native.RadioEntityType,
                    EntityType = native.EntityType,
                    TransmitState = native.TransmitState,
                    InputSource = native.InputSource,
                    VariableTransmitterParameterCount = native.VariableTransmitterParameterCount,
                    AntennaLocation = native.AntennaLocation,
                    RelativeAntennaLocation = native.RelativeAntennaLocation,
                    AntennaPatternType = native.AntennaPatternType,
                    AntennaPatternCount = native.AntennaPatternCount,
                    Frequency = native.Frequency,
                    TransmitFrequencyBandwidth = native.TransmitFrequencyBandwidth,
                    Power = native.Power,
                    ModulationType = native.ModulationType,
                    CryptoSystem = native.CryptoSystem,
                    CryptoKeyId = native.CryptoKeyId,
                    ModulationParameterCount = native.ModulationParameterCount,
                    Padding2 = native.Padding2,
                    Padding3 = native.Padding3,
                    ModulationParameterBytes = CopyBytes(native.ModulationParameters),
                    AntennaPatternBytes = CopyBytes(native.AntennaPatterns),
                });
        }

        public static bool TryParseCollision(
            byte[] packet,
            out FastDisCollision collision,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_collision, out collision);
        }

        public static bool TryParseCollisionElastic(
            byte[] packet,
            out FastDisCollisionElastic collisionElastic,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_collision_elastic, out collisionElastic);
        }

        public static bool TryParseOtherPdu(
            byte[] packet,
            out FastDisOtherPdu other,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeOtherPdu, FastDisOtherPdu>(packet, flags, allowTruncated, fastdis_parse_other_pdu, out other,
                native => new FastDisOtherPdu
                {
                    Header = native.Header,
                    OpaquePayloadBytes = CopyBytes(native.OpaquePayload),
                });
        }

        public static bool TryParseAggregateState(
            byte[] packet,
            out FastDisAggregateState aggregate,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeAggregateState, FastDisAggregateState>(packet, flags, allowTruncated, fastdis_parse_aggregate_state, out aggregate,
                native => new FastDisAggregateState
                {
                    Header = native.Header,
                    AggregateId = native.AggregateId,
                    ForceId = native.ForceId,
                    AggregateStateValue = native.AggregateStateValue,
                    AggregateType = native.AggregateType,
                    Formation = native.Formation,
                    AggregateMarkingCharacterSet = native.AggregateMarkingCharacterSet,
                    AggregateMarkingBytes = native.AggregateMarking ?? Array.Empty<byte>(),
                    Dimensions = native.Dimensions,
                    Orientation = native.Orientation,
                    CenterOfMass = native.CenterOfMass,
                    Velocity = native.Velocity,
                    NumberOfDisAggregates = native.NumberOfDisAggregates,
                    NumberOfDisEntities = native.NumberOfDisEntities,
                    NumberOfSilentAggregateTypes = native.NumberOfSilentAggregateTypes,
                    NumberOfSilentEntityTypes = native.NumberOfSilentEntityTypes,
                    AggregateRecordBytes = CopyBytes(native.AggregateRecords),
                });
        }

        public static bool TryParseIsGroupOf(
            byte[] packet,
            out FastDisIsGroupOf group,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeIsGroupOf, FastDisIsGroupOf>(packet, flags, allowTruncated, fastdis_parse_is_group_of, out group,
                native => new FastDisIsGroupOf
                {
                    Header = native.Header,
                    GroupEntityId = native.GroupEntityId,
                    GroupedEntityCategory = native.GroupedEntityCategory,
                    NumberOfGroupedEntities = native.NumberOfGroupedEntities,
                    Pad2 = native.Pad2,
                    Latitude = native.Latitude,
                    Longitude = native.Longitude,
                    GroupedEntityDescriptionBytes = CopyBytes(native.GroupedEntityDescriptions),
                });
        }

        public static bool TryParseTransferControlRequest(
            byte[] packet,
            out FastDisTransferControlRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeTransferControlRequest, FastDisTransferControlRequest>(packet, flags, allowTruncated, fastdis_parse_transfer_control_request, out request,
                native => new FastDisTransferControlRequest
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    TransferType = native.TransferType,
                    TransferEntityId = native.TransferEntityId,
                    NumberOfRecordSets = native.NumberOfRecordSets,
                    RecordSetBytes = CopyBytes(native.RecordSets),
                });
        }

        public static bool TryParseTransferOwnership(
            byte[] packet,
            out FastDisTransferOwnership request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeTransferOwnership, FastDisTransferOwnership>(packet, flags, allowTruncated, fastdis_parse_transfer_ownership, out request,
                native => new FastDisTransferOwnership
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RequestId = native.RequestId,
                    RequiredReliabilityService = native.RequiredReliabilityService,
                    TransferType = native.TransferType,
                    TransferEntityId = native.TransferEntityId,
                    NumberOfRecordSets = native.NumberOfRecordSets,
                    RecordSetBytes = CopyBytes(native.RecordSets),
                });
        }

        public static bool TryParseIsPartOf(
            byte[] packet,
            out FastDisIsPartOf part,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeIsPartOf, FastDisIsPartOf>(packet, flags, allowTruncated, fastdis_parse_is_part_of, out part,
                native => new FastDisIsPartOf
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RelationshipNature = native.RelationshipNature,
                    RelationshipPosition = native.RelationshipPosition,
                    PartLocation = native.PartLocation,
                    StationName = native.StationName,
                    StationNumber = native.StationNumber,
                    PartEntityType = native.PartEntityType,
                });
        }

        public static bool TryParseMinefieldState(
            byte[] packet,
            out FastDisMinefieldState state,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeMinefieldState, FastDisMinefieldState>(packet, flags, allowTruncated, fastdis_parse_minefield_state, out state,
                native => new FastDisMinefieldState
                {
                    Header = native.Header,
                    MinefieldId = native.MinefieldId,
                    MinefieldSequence = native.MinefieldSequence,
                    ForceId = native.ForceId,
                    NumberOfPerimeterPoints = native.NumberOfPerimeterPoints,
                    MinefieldType = native.MinefieldType,
                    NumberOfMineTypes = native.NumberOfMineTypes,
                    MinefieldLocation = native.MinefieldLocation,
                    MinefieldOrientation = native.MinefieldOrientation,
                    Appearance = native.Appearance,
                    ProtocolMode = native.ProtocolMode,
                    PerimeterPointBytes = CopyBytes(native.PerimeterPoints),
                    MineTypeBytes = CopyBytes(native.MineTypes),
                });
        }

        public static bool TryParseMinefieldQuery(
            byte[] packet,
            out FastDisMinefieldQuery query,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeMinefieldQuery, FastDisMinefieldQuery>(packet, flags, allowTruncated, fastdis_parse_minefield_query, out query,
                native => new FastDisMinefieldQuery
                {
                    Header = native.Header,
                    MinefieldId = native.MinefieldId,
                    RequestingEntityId = native.RequestingEntityId,
                    RequestId = native.RequestId,
                    NumberOfPerimeterPoints = native.NumberOfPerimeterPoints,
                    Pad2 = native.Pad2,
                    NumberOfSensorTypes = native.NumberOfSensorTypes,
                    DataFilter = native.DataFilter,
                    RequestedMineType = native.RequestedMineType,
                    RequestedPerimeterPointBytes = CopyBytes(native.RequestedPerimeterPoints),
                    SensorTypeBytes = CopyBytes(native.SensorTypes),
                });
        }

        public static bool TryParseMinefieldData(
            byte[] packet,
            out FastDisMinefieldData data,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeMinefieldData, FastDisMinefieldData>(packet, flags, allowTruncated, fastdis_parse_minefield_data, out data,
                native => new FastDisMinefieldData
                {
                    Header = native.Header,
                    MinefieldId = native.MinefieldId,
                    RequestingEntityId = native.RequestingEntityId,
                    MinefieldSequenceNumber = native.MinefieldSequenceNumber,
                    RequestId = native.RequestId,
                    PduSequenceNumber = native.PduSequenceNumber,
                    NumberOfPdus = native.NumberOfPdus,
                    NumberOfMinesInThisPdu = native.NumberOfMinesInThisPdu,
                    NumberOfSensorTypes = native.NumberOfSensorTypes,
                    Pad2 = native.Pad2,
                    DataFilter = native.DataFilter,
                    MineType = native.MineType,
                    Pad3 = native.Pad3,
                    SensorTypeBytes = CopyBytes(native.SensorTypes),
                    MineLocationBytes = CopyBytes(native.MineLocations),
                });
        }

        public static bool TryParseMinefieldResponseNack(
            byte[] packet,
            out FastDisMinefieldResponseNack nack,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeMinefieldResponseNack, FastDisMinefieldResponseNack>(packet, flags, allowTruncated, fastdis_parse_minefield_response_nack, out nack,
                native => new FastDisMinefieldResponseNack
                {
                    Header = native.Header,
                    MinefieldId = native.MinefieldId,
                    RequestingEntityId = native.RequestingEntityId,
                    RequestId = native.RequestId,
                    NumberOfMissingPdus = native.NumberOfMissingPdus,
                    MissingPduSequenceNumberBytes = CopyBytes(native.MissingPduSequenceNumbers),
                });
        }

        public static bool TryParseEnvironmentalProcess(
            byte[] packet,
            out FastDisEnvironmentalProcess process,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeEnvironmentalProcess, FastDisEnvironmentalProcess>(packet, flags, allowTruncated, fastdis_parse_environmental_process, out process,
                native => new FastDisEnvironmentalProcess
                {
                    Header = native.Header,
                    EnvironmentalProcessId = native.EnvironmentalProcessId,
                    EnvironmentType = native.EnvironmentType,
                    ModelType = native.ModelType,
                    EnvironmentStatus = native.EnvironmentStatus,
                    NumberOfEnvironmentRecords = native.NumberOfEnvironmentRecords,
                    SequenceNumber = native.SequenceNumber,
                    EnvironmentRecordBytes = CopyBytes(native.EnvironmentRecords),
                });
        }

        public static bool TryParseGriddedData(
            byte[] packet,
            out FastDisGriddedData grid,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeGriddedData, FastDisGriddedData>(packet, flags, allowTruncated, fastdis_parse_gridded_data, out grid,
                native => new FastDisGriddedData
                {
                    Header = native.Header,
                    EnvironmentalSimulationApplicationId = native.EnvironmentalSimulationApplicationId,
                    FieldNumber = native.FieldNumber,
                    PduNumber = native.PduNumber,
                    PduTotal = native.PduTotal,
                    CoordinateSystem = native.CoordinateSystem,
                    NumberOfGridAxes = native.NumberOfGridAxes,
                    ConstantGrid = native.ConstantGrid,
                    EnvironmentType = native.EnvironmentType,
                    Orientation = native.Orientation,
                    SampleTime = native.SampleTime,
                    TotalValues = native.TotalValues,
                    VectorDimension = native.VectorDimension,
                    Padding1 = native.Padding1,
                    Padding2 = native.Padding2,
                    GridDataBytes = CopyBytes(native.GridData),
                });
        }

        public static bool TryParsePointObjectState(
            byte[] packet,
            out FastDisPointObjectState point,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativePointObjectState, FastDisPointObjectState>(packet, flags, allowTruncated, fastdis_parse_point_object_state, out point,
                native => new FastDisPointObjectState
                {
                    Header = native.Header,
                    ObjectId = native.ObjectId,
                    ReferencedObjectId = native.ReferencedObjectId,
                    UpdateNumber = native.UpdateNumber,
                    ForceId = native.ForceId,
                    Modifications = native.Modifications,
                    ObjectType = new FastDisEnvironmentObjectType
                    {
                        Domain = native.ObjectType.Domain,
                        Kind = native.ObjectType.Kind,
                        Country = native.ObjectType.Country,
                        Category = native.ObjectType.Category,
                        Subcategory = native.ObjectType.Subcategory,
                    },
                    ObjectLocation = native.ObjectLocation,
                    ObjectOrientation = native.ObjectOrientation,
                    ObjectAppearance = native.ObjectAppearance,
                    RequesterId = native.RequesterId,
                    ReceivingId = native.ReceivingId,
                    Pad2 = native.Pad2,
                });
        }

        public static bool TryParseLinearObjectState(
            byte[] packet,
            out FastDisLinearObjectState linear,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeLinearObjectState, FastDisLinearObjectState>(packet, flags, allowTruncated, fastdis_parse_linear_object_state, out linear,
                native => new FastDisLinearObjectState
                {
                    Header = native.Header,
                    ObjectId = native.ObjectId,
                    ReferencedObjectId = native.ReferencedObjectId,
                    UpdateNumber = native.UpdateNumber,
                    ForceId = native.ForceId,
                    NumberOfSegments = native.NumberOfSegments,
                    RequesterId = native.RequesterId,
                    ReceivingId = native.ReceivingId,
                    ObjectType = new FastDisEnvironmentObjectType
                    {
                        Domain = native.ObjectType.Domain,
                        Kind = native.ObjectType.Kind,
                        Country = native.ObjectType.Country,
                        Category = native.ObjectType.Category,
                        Subcategory = native.ObjectType.Subcategory,
                    },
                    LinearSegmentParameterBytes = CopyBytes(native.LinearSegmentParameters),
                });
        }

        public static bool TryParseArealObjectState(
            byte[] packet,
            out FastDisArealObjectState areal,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeArealObjectState, FastDisArealObjectState>(packet, flags, allowTruncated, fastdis_parse_areal_object_state, out areal,
                native => new FastDisArealObjectState
                {
                    Header = native.Header,
                    ObjectId = native.ObjectId,
                    ReferencedObjectId = native.ReferencedObjectId,
                    UpdateNumber = native.UpdateNumber,
                    ForceId = native.ForceId,
                    Modifications = native.Modifications,
                    ObjectType = native.ObjectType,
                    ObjectAppearanceBytes = CopyBytes(native.ObjectAppearance),
                    NumberOfPoints = native.NumberOfPoints,
                    RequesterId = native.RequesterId,
                    ReceivingId = native.ReceivingId,
                    ObjectLocationBytes = CopyBytes(native.ObjectLocations),
                });
        }

        public static bool TryParseTspi(
            byte[] packet,
            out FastDisTspi tspi,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeTspi, FastDisTspi>(packet, flags, allowTruncated, fastdis_parse_tspi, out tspi,
                native => new FastDisTspi
                {
                    Header = native.Header,
                    LiveEntityId = new FastDisLiveEntityId { Site = native.LiveEntityId.Site, Application = native.LiveEntityId.Application, Entity = native.LiveEntityId.Entity },
                    TspiFlag = native.TspiFlag,
                    EntityLocationBytes = CopyBytes(native.EntityLocation),
                    EntityLinearVelocityBytes = CopyBytes(native.EntityLinearVelocity),
                    EntityOrientationBytes = CopyBytes(native.EntityOrientation),
                    PositionErrorBytes = CopyBytes(native.PositionError),
                    OrientationErrorBytes = CopyBytes(native.OrientationError),
                    DeadReckoningParameterBytes = CopyBytes(native.DeadReckoningParameters),
                    MeasuredSpeed = native.MeasuredSpeed,
                    SystemSpecificDataLength = native.SystemSpecificDataLength,
                    SystemSpecificDataBytes = CopyBytes(native.SystemSpecificData),
                });
        }

        public static bool TryParseLiveEntityAppearance(
            byte[] packet,
            out FastDisLiveEntityAppearance appearance,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeLiveEntityAppearance, FastDisLiveEntityAppearance>(packet, flags, allowTruncated, fastdis_parse_live_entity_appearance, out appearance,
                native => new FastDisLiveEntityAppearance
                {
                    Header = native.Header,
                    LiveEntityId = new FastDisLiveEntityId { Site = native.LiveEntityId.Site, Application = native.LiveEntityId.Application, Entity = native.LiveEntityId.Entity },
                    AppearanceFlags = native.AppearanceFlags,
                    ForceId = native.ForceId,
                    Padding1 = native.Padding1,
                    EntityType = native.EntityType,
                    AlternateEntityType = native.AlternateEntityType,
                    EntityMarking = native.EntityMarking ?? Array.Empty<byte>(),
                    Capabilities = native.Capabilities,
                    AppearanceFieldBytes = CopyBytes(native.AppearanceFields),
                });
        }

        public static bool TryParseArticulatedParts(
            byte[] packet,
            out FastDisArticulatedParts parts,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeArticulatedParts, FastDisArticulatedParts>(packet, flags, allowTruncated, fastdis_parse_articulated_parts, out parts,
                native => new FastDisArticulatedParts
                {
                    Header = native.Header,
                    LiveEntityId = new FastDisLiveEntityId { Site = native.LiveEntityId.Site, Application = native.LiveEntityId.Application, Entity = native.LiveEntityId.Entity },
                    NumberOfParameterRecords = native.NumberOfParameterRecords,
                    PaddingBytes = native.Padding ?? Array.Empty<byte>(),
                    VariableParameterBytes = CopyBytes(native.VariableParameters),
                });
        }

        public static bool TryParseLeFire(
            byte[] packet,
            out FastDisLeFire fire,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeLeFire, FastDisLeFire>(packet, flags, allowTruncated, fastdis_parse_le_fire, out fire,
                native => new FastDisLeFire
                {
                    Header = native.Header,
                    FiringLiveEntityId = new FastDisLiveEntityId { Site = native.FiringLiveEntityId.Site, Application = native.FiringLiveEntityId.Application, Entity = native.FiringLiveEntityId.Entity },
                    Flags = native.Flags,
                    Padding1 = native.Padding1,
                    TargetLiveEntityId = new FastDisLiveEntityId { Site = native.TargetLiveEntityId.Site, Application = native.TargetLiveEntityId.Application, Entity = native.TargetLiveEntityId.Entity },
                    MunitionLiveEntityId = new FastDisLiveEntityId { Site = native.MunitionLiveEntityId.Site, Application = native.MunitionLiveEntityId.Application, Entity = native.MunitionLiveEntityId.Entity },
                    EventId = new FastDisLiveEventId { Site = native.EventId.Site, Application = native.EventId.Application, EventNumber = native.EventId.EventNumber },
                    LocationBytes = CopyBytes(native.Location),
                    MunitionDescriptor = native.MunitionDescriptor,
                    VelocityBytes = CopyBytes(native.Velocity),
                    Range = native.Range,
                });
        }

        public static bool TryParseLeDetonation(
            byte[] packet,
            out FastDisLeDetonation detonation,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeLeDetonation, FastDisLeDetonation>(packet, flags, allowTruncated, fastdis_parse_le_detonation, out detonation,
                native => new FastDisLeDetonation
                {
                    Header = native.Header,
                    FiringLiveEntityId = new FastDisLiveEntityId { Site = native.FiringLiveEntityId.Site, Application = native.FiringLiveEntityId.Application, Entity = native.FiringLiveEntityId.Entity },
                    DetonationFlag1 = native.DetonationFlag1,
                    DetonationFlag2 = native.DetonationFlag2,
                    TargetLiveEntityId = new FastDisLiveEntityId { Site = native.TargetLiveEntityId.Site, Application = native.TargetLiveEntityId.Application, Entity = native.TargetLiveEntityId.Entity },
                    MunitionLiveEntityId = new FastDisLiveEntityId { Site = native.MunitionLiveEntityId.Site, Application = native.MunitionLiveEntityId.Application, Entity = native.MunitionLiveEntityId.Entity },
                    EventId = new FastDisLiveEventId { Site = native.EventId.Site, Application = native.EventId.Application, EventNumber = native.EventId.EventNumber },
                    WorldLocationBytes = CopyBytes(native.WorldLocation),
                    VelocityBytes = CopyBytes(native.Velocity),
                    MunitionOrientationBytes = CopyBytes(native.MunitionOrientation),
                    MunitionDescriptor = native.MunitionDescriptor,
                    EntityLocationBytes = CopyBytes(native.EntityLocation),
                    DetonationResult = native.DetonationResult,
                    Padding1 = native.Padding1,
                });
        }

        public static bool TryParseSignal(
            byte[] packet,
            out FastDisSignal signal,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeSignal, FastDisSignal>(packet, flags, allowTruncated, fastdis_parse_signal, out signal,
                native => new FastDisSignal
                {
                    Header = native.Header,
                    EntityId = native.EntityId,
                    RadioId = native.RadioId,
                    EncodingScheme = native.EncodingScheme,
                    TdlType = native.TdlType,
                    SampleRate = native.SampleRate,
                    DataLength = native.DataLength,
                    Samples = native.Samples,
                    DataBytes = CopyBytes(native.Data),
                });
        }

        public static bool TryParseReceiver(
            byte[] packet,
            out FastDisReceiver receiver,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_receiver, out receiver);
        }

        public static bool TryParseElectronicEmissions(
            byte[] packet,
            out FastDisElectronicEmissions emissions,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeElectronicEmissions, FastDisElectronicEmissions>(packet, flags, allowTruncated, fastdis_parse_electronic_emissions, out emissions,
                native => new FastDisElectronicEmissions
                {
                    Header = native.Header,
                    EmittingEntityId = native.EmittingEntityId,
                    EventId = native.EventId,
                    StateUpdateIndicator = native.StateUpdateIndicator,
                    NumberOfSystems = native.NumberOfSystems,
                    Padding1 = native.Padding1,
                    SystemRecordBytes = CopyBytes(native.SystemRecords),
                });
        }

        public static bool TryParseIffAtcNavAidsLayer1(
            byte[] packet,
            out FastDisIffAtcNavAidsLayer1 iff,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_iff_atc_navaids_layer1, out iff);
        }

        public static bool TryParseIff(
            byte[] packet,
            out FastDisIff iff,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_iff, out iff);
        }

        public static bool TryParseUa(
            byte[] packet,
            out FastDisUa ua,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeUa, FastDisUa>(packet, flags, allowTruncated, fastdis_parse_ua, out ua,
                native => new FastDisUa
                {
                    Header = native.Header,
                    EmittingEntityId = native.EmittingEntityId,
                    EventId = native.EventId,
                    StateChangeIndicator = native.StateChangeIndicator,
                    Padding1 = native.Padding1,
                    PassiveParameterIndex = native.PassiveParameterIndex,
                    PropulsionPlantConfiguration = native.PropulsionPlantConfiguration,
                    NumberOfShafts = native.NumberOfShafts,
                    NumberOfApas = native.NumberOfApas,
                    NumberOfUaEmitterSystems = native.NumberOfUaEmitterSystems,
                    UaRecordBytes = CopyBytes(native.UaRecords),
                });
        }

        public static bool TryParseSees(
            byte[] packet,
            out FastDisSees sees,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeSees, FastDisSees>(packet, flags, allowTruncated, fastdis_parse_sees, out sees,
                native => new FastDisSees
                {
                    Header = native.Header,
                    OriginatingEntityId = native.OriginatingEntityId,
                    InfraredSignatureRepresentationIndex = native.InfraredSignatureRepresentationIndex,
                    AcousticSignatureRepresentationIndex = native.AcousticSignatureRepresentationIndex,
                    RadarCrossSectionSignatureRepresentationIndex = native.RadarCrossSectionSignatureRepresentationIndex,
                    NumberOfPropulsionSystems = native.NumberOfPropulsionSystems,
                    NumberOfVectoringNozzleSystems = native.NumberOfVectoringNozzleSystems,
                    SupplementalEmissionRecordBytes = CopyBytes(native.SupplementalEmissionRecords),
                });
        }

        public static bool TryParseIntercomSignal(
            byte[] packet,
            out FastDisIntercomSignal signal,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeIntercomSignal, FastDisIntercomSignal>(packet, flags, allowTruncated, fastdis_parse_intercom_signal, out signal,
                native => new FastDisIntercomSignal
                {
                    Header = native.Header,
                    EntityId = native.EntityId,
                    CommunicationsDeviceId = native.CommunicationsDeviceId,
                    EncodingScheme = native.EncodingScheme,
                    TdlType = native.TdlType,
                    SampleRate = native.SampleRate,
                    DataLength = native.DataLength,
                    Samples = native.Samples,
                    DataBytes = CopyBytes(native.Data),
                });
        }

        public static bool TryParseIntercomControl(
            byte[] packet,
            out FastDisIntercomControl control,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeIntercomControl, FastDisIntercomControl>(packet, flags, allowTruncated, fastdis_parse_intercom_control, out control,
                native => new FastDisIntercomControl
                {
                    Header = native.Header,
                    ControlType = native.ControlType,
                    CommunicationsChannelType = native.CommunicationsChannelType,
                    SourceEntityId = native.SourceEntityId,
                    SourceCommunicationsDeviceId = native.SourceCommunicationsDeviceId,
                    SourceLineId = native.SourceLineId,
                    TransmitPriority = native.TransmitPriority,
                    TransmitLineState = native.TransmitLineState,
                    Command = native.Command,
                    MasterEntityId = native.MasterEntityId,
                    MasterCommunicationsDeviceId = native.MasterCommunicationsDeviceId,
                    IntercomParametersLength = native.IntercomParametersLength,
                    IntercomParametersBytes = CopyBytes(native.IntercomParameters),
                });
        }

        public static bool TryParseAttribute(
            byte[] packet,
            out FastDisAttribute attribute,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeAttribute, FastDisAttribute>(packet, flags, allowTruncated, fastdis_parse_attribute, out attribute,
                native => new FastDisAttribute
                {
                    Header = native.Header,
                    OriginatingSimulationAddress = new FastDisSimulationAddress
                    {
                        Site = native.OriginatingSimulationAddress.Site,
                        Application = native.OriginatingSimulationAddress.Application,
                    },
                    Padding1 = native.Padding1,
                    Padding2 = native.Padding2,
                    AttributeRecordPduType = native.AttributeRecordPduType,
                    AttributeRecordProtocolVersion = native.AttributeRecordProtocolVersion,
                    MasterAttributeRecordType = native.MasterAttributeRecordType,
                    ActionCode = native.ActionCode,
                    Padding3 = native.Padding3,
                    NumberAttributeRecordSet = native.NumberAttributeRecordSet,
                    AttributeRecordSetBytes = CopyBytes(native.AttributeRecordSets),
                });
        }

        public static bool TryParseDirectedEnergyFire(
            byte[] packet,
            out FastDisDirectedEnergyFire directedEnergyFire,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeDirectedEnergyFire, FastDisDirectedEnergyFire>(packet, flags, allowTruncated, fastdis_parse_directed_energy_fire, out directedEnergyFire,
                native => new FastDisDirectedEnergyFire
                {
                    Header = native.Header,
                    FiringEntityId = native.FiringEntityId,
                    TargetEntityId = native.TargetEntityId,
                    MunitionType = native.MunitionType,
                    ShotStartTime = native.ShotStartTime,
                    CommulativeShotTime = native.CommulativeShotTime,
                    ApertureEmitterLocation = native.ApertureEmitterLocation,
                    ApertureDiameter = native.ApertureDiameter,
                    Wavelength = native.Wavelength,
                    PeakIrradiance = native.PeakIrradiance,
                    PulseRepetitionFrequency = native.PulseRepetitionFrequency,
                    PulseWidth = native.PulseWidth,
                    Flags = native.Flags,
                    PulseShape = native.PulseShape,
                    Padding1 = native.Padding1,
                    Padding2 = native.Padding2,
                    Padding3 = native.Padding3,
                    NumberOfDeRecords = native.NumberOfDeRecords,
                    DeRecordBytes = CopyBytes(native.DeRecords),
                });
        }

        public static bool TryParseEntityDamageStatus(
            byte[] packet,
            out FastDisEntityDamageStatus entityDamageStatus,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeEntityDamageStatus, FastDisEntityDamageStatus>(packet, flags, allowTruncated, fastdis_parse_entity_damage_status, out entityDamageStatus,
                native => new FastDisEntityDamageStatus
                {
                    Header = native.Header,
                    FiringEntityId = native.FiringEntityId,
                    TargetEntityId = native.TargetEntityId,
                    DamagedEntityId = native.DamagedEntityId,
                    Padding1 = native.Padding1,
                    Padding2 = native.Padding2,
                    NumberOfDamageDescription = native.NumberOfDamageDescription,
                    DamageDescriptionRecordBytes = CopyBytes(native.DamageDescriptionRecords),
                });
        }

        public static bool TryParseInformationOperationsAction(
            byte[] packet,
            out FastDisInformationOperationsAction action,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeInformationOperationsAction, FastDisInformationOperationsAction>(packet, flags, allowTruncated, fastdis_parse_information_operations_action, out action,
                native => new FastDisInformationOperationsAction
                {
                    Header = native.Header,
                    OriginatingSimId = native.OriginatingSimId,
                    ReceivingSimId = native.ReceivingSimId,
                    RequestId = native.RequestId,
                    IoWarfareType = native.IoWarfareType,
                    IoSimulationSource = native.IoSimulationSource,
                    IoActionType = native.IoActionType,
                    IoActionPhase = native.IoActionPhase,
                    Padding1 = native.Padding1,
                    IoAttackerId = native.IoAttackerId,
                    IoPrimaryTargetId = native.IoPrimaryTargetId,
                    Padding2 = native.Padding2,
                    NumberOfIoRecords = native.NumberOfIoRecords,
                    IoRecordBytes = CopyBytes(native.IoRecords),
                });
        }

        public static bool TryParseInformationOperationsReport(
            byte[] packet,
            out FastDisInformationOperationsReport report,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeInformationOperationsReport, FastDisInformationOperationsReport>(packet, flags, allowTruncated, fastdis_parse_information_operations_report, out report,
                native => new FastDisInformationOperationsReport
                {
                    Header = native.Header,
                    OriginatingSimId = native.OriginatingSimId,
                    IoSimSource = native.IoSimSource,
                    IoReportType = native.IoReportType,
                    Padding1 = native.Padding1,
                    IoAttackerId = native.IoAttackerId,
                    IoPrimaryTargetId = native.IoPrimaryTargetId,
                    Padding2 = native.Padding2,
                    Padding3 = native.Padding3,
                    NumberOfIoRecords = native.NumberOfIoRecords,
                    IoRecordBytes = CopyBytes(native.IoRecords),
                });
        }

        public static bool TryParseServiceRequest(
            byte[] packet,
            out FastDisServiceRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeServiceRequest, FastDisServiceRequest>(packet, flags, allowTruncated, fastdis_parse_service_request, out request,
                native => new FastDisServiceRequest
                {
                    Header = native.Header,
                    RequestingEntityId = native.RequestingEntityId,
                    ServicingEntityId = native.ServicingEntityId,
                    ServiceTypeRequested = native.ServiceTypeRequested,
                    NumberOfSupplyTypes = native.NumberOfSupplyTypes,
                    ServiceRequestPadding = native.ServiceRequestPadding,
                    SupplyBytes = CopyBytes(native.Supplies),
                });
        }

        public static bool TryParseResupplyOffer(
            byte[] packet,
            out FastDisResupplyOffer request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeResupplyOffer, FastDisResupplyOffer>(packet, flags, allowTruncated, fastdis_parse_resupply_offer, out request,
                native => new FastDisResupplyOffer
                {
                    Header = native.Header,
                    ReceivingEntityId = native.ReceivingEntityId,
                    SupplyingEntityId = native.SupplyingEntityId,
                    NumberOfSupplyTypes = native.NumberOfSupplyTypes,
                    PaddingBytes = native.PaddingBytes ?? Array.Empty<byte>(),
                    SupplyBytes = CopyBytes(native.Supplies),
                });
        }

        public static bool TryParseResupplyReceived(
            byte[] packet,
            out FastDisResupplyReceived request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeResupplyReceived, FastDisResupplyReceived>(packet, flags, allowTruncated, fastdis_parse_resupply_received, out request,
                native => new FastDisResupplyReceived
                {
                    Header = native.Header,
                    ReceivingEntityId = native.ReceivingEntityId,
                    SupplyingEntityId = native.SupplyingEntityId,
                    NumberOfSupplyTypes = native.NumberOfSupplyTypes,
                    Padding1 = native.Padding1,
                    Padding2 = native.Padding2,
                    SupplyBytes = CopyBytes(native.Supplies),
                });
        }

        public static bool TryParseResupplyCancel(
            byte[] packet,
            out FastDisResupplyCancel request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeResupplyCancel, FastDisResupplyCancel>(packet, flags, allowTruncated, fastdis_parse_resupply_cancel, out request,
                native => new FastDisResupplyCancel
                {
                    Header = native.Header,
                    ReceivingEntityId = native.ReceivingEntityId,
                    SupplyingEntityId = native.SupplyingEntityId,
                });
        }

        public static bool TryParseRepairComplete(
            byte[] packet,
            out FastDisRepairComplete request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeRepairComplete, FastDisRepairComplete>(packet, flags, allowTruncated, fastdis_parse_repair_complete, out request,
                native => new FastDisRepairComplete
                {
                    Header = native.Header,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RepairingEntityId = native.RepairingEntityId,
                    Repair = native.Repair,
                    Padding2 = native.Padding2,
                });
        }

        public static bool TryParseRepairResponse(
            byte[] packet,
            out FastDisRepairResponse request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParseDatum<NativeRepairResponse, FastDisRepairResponse>(packet, flags, allowTruncated, fastdis_parse_repair_response, out request,
                native => new FastDisRepairResponse
                {
                    Header = native.Header,
                    ReceivingEntityId = native.ReceivingEntityId,
                    RepairingEntityId = native.RepairingEntityId,
                    RepairResult = native.RepairResult,
                    Padding1 = native.Padding1,
                    Padding2 = native.Padding2,
                });
        }

        private delegate int ParseDelegate<T>(IntPtr data, UIntPtr size, uint flags, out T parsed);
        private delegate int ParseDatumDelegate<TNative>(IntPtr data, UIntPtr size, uint flags, out TNative parsed);

        private static bool TryParse<T>(
            byte[] packet,
            uint flags,
            bool allowTruncated,
            ParseDelegate<T> parser,
            out T parsed)
        {
            parsed = default;
            if (packet == null || packet.Length == 0)
            {
                return false;
            }

            GCHandle handle = default;
            try
            {
                handle = GCHandle.Alloc(packet, GCHandleType.Pinned);
                uint combinedFlags = flags | (allowTruncated ? FastDisFlagAllowTruncated : 0u);
                int rc = parser(
                    handle.AddrOfPinnedObject(),
                    (UIntPtr)(uint)packet.Length,
                    combinedFlags,
                    out parsed);
                return rc == FastDisOk;
            }
            catch (DllNotFoundException)
            {
                parsed = default;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                parsed = default;
                return false;
            }
            finally
            {
                if (handle.IsAllocated)
                {
                    handle.Free();
                }
            }
        }

        private static bool TryParseDatum<TNative, TValue>(
            byte[] packet,
            uint flags,
            bool allowTruncated,
            ParseDatumDelegate<TNative> parser,
            out TValue parsed,
            Func<TNative, TValue> convert)
        {
            parsed = default;
            if (packet == null || packet.Length == 0)
            {
                return false;
            }

            GCHandle handle = default;
            try
            {
                handle = GCHandle.Alloc(packet, GCHandleType.Pinned);
                uint combinedFlags = flags | (allowTruncated ? FastDisFlagAllowTruncated : 0u);
                int rc = parser(
                    handle.AddrOfPinnedObject(),
                    (UIntPtr)(uint)packet.Length,
                    combinedFlags,
                    out TNative nativeParsed);
                if (rc != FastDisOk)
                {
                    parsed = default;
                    return false;
                }

                parsed = convert(nativeParsed);
                return true;
            }
            catch (DllNotFoundException)
            {
                parsed = default;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                parsed = default;
                return false;
            }
            finally
            {
                if (handle.IsAllocated)
                {
                    handle.Free();
                }
            }
        }
    }
}
