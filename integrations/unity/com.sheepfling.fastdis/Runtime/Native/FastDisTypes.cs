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
    public struct FastDisVec3F
    {
        public float X;
        public float Y;
        public float Z;
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
