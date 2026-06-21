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
    public struct FastDisEntityId
    {
        public ushort Site;
        public ushort Application;
        public ushort Entity;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct FastDisEntityTransform
    {
        public FastDisEntityId EntityId;
        public byte ForceId;
        public double X;
        public double Y;
        public double Z;
        public float Psi;
        public float Theta;
        public float Phi;
        public uint Timestamp;
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
