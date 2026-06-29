using System;
using System.Net;
using System.Net.Sockets;
using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisNetworkSender : MonoBehaviour
    {
        [Serializable]
        public struct EntityStateSpec
        {
            public byte Version;
            public ushort Site;
            public ushort Application;
            public ushort Entity;
            public byte ForceId;
            public double X;
            public double Y;
            public double Z;
            public float Psi;
            public float Theta;
            public float Phi;
            public float VelocityX;
            public float VelocityY;
            public float VelocityZ;
        }

        [SerializeField]
        private string destinationAddress = "127.0.0.1";

        [SerializeField]
        private ushort port = 3001;

        [SerializeField]
        private bool broadcastEnabled;

        [SerializeField]
        private bool multicastEnabled;

        [SerializeField]
        private bool multicastLoopback = true;

        private UdpClient client;
        private ulong packetsSent;
        private ulong sendFailures;

        public string DestinationAddress => destinationAddress;
        public ushort Port => port;
        public bool BroadcastEnabled => broadcastEnabled;
        public bool MulticastEnabled => multicastEnabled;
        public bool IsRunning => client != null;
        public ulong PacketsSent => packetsSent;
        public ulong SendFailures => sendFailures;

        private void OnDisable()
        {
            StopSender();
        }

        public void ConfigureUnicast(string address, ushort targetPort)
        {
            EnsureStopped();
            destinationAddress = string.IsNullOrWhiteSpace(address) ? "127.0.0.1" : address;
            port = targetPort;
            broadcastEnabled = false;
            multicastEnabled = false;
        }

        public void ConfigureBroadcast(ushort targetPort)
        {
            EnsureStopped();
            destinationAddress = "255.255.255.255";
            port = targetPort;
            broadcastEnabled = true;
            multicastEnabled = false;
        }

        public void ConfigureMulticast(string address, ushort targetPort, bool loopback = true)
        {
            EnsureStopped();
            destinationAddress = string.IsNullOrWhiteSpace(address) ? "239.255.42.99" : address;
            port = targetPort;
            broadcastEnabled = false;
            multicastEnabled = true;
            multicastLoopback = loopback;
        }

        public void StartSender()
        {
            if (client != null)
            {
                return;
            }

            client = new UdpClient(AddressFamily.InterNetwork);
            if (broadcastEnabled)
            {
                client.EnableBroadcast = true;
            }
            if (multicastEnabled)
            {
                client.MulticastLoopback = multicastLoopback;
            }
        }

        public void StopSender()
        {
            if (client == null)
            {
                return;
            }

            try
            {
                client.Close();
            }
            finally
            {
                client = null;
            }
        }

        public bool SendRaw(byte[] packet)
        {
            if (packet == null || packet.Length == 0)
            {
                sendFailures++;
                return false;
            }

            EnsureStarted();
            try
            {
                client.Send(packet, packet.Length, destinationAddress, port);
                packetsSent++;
                return true;
            }
            catch (SocketException)
            {
                sendFailures++;
                return false;
            }
        }

        public bool SendEntityState(EntityStateSpec spec)
        {
            byte version = spec.Version == 0 ? (byte)7 : spec.Version;
            return SendRaw(CreateEntityStatePdu(version, spec));
        }

        private void EnsureStopped()
        {
            if (client != null)
            {
                throw new InvalidOperationException("Cannot reconfigure the sender while it is running.");
            }
        }

        private void EnsureStarted()
        {
            if (client == null)
            {
                StartSender();
            }
        }

        private static byte[] CreateEntityStatePdu(byte version, EntityStateSpec spec)
        {
            byte[] packet = new byte[144];
            packet[0] = version;
            packet[1] = 3;
            packet[2] = 1;
            packet[3] = 1;
            WriteU16(packet, 8, 144);

            int body = 12;
            WriteU16(packet, body + 0, spec.Site);
            WriteU16(packet, body + 2, spec.Application);
            WriteU16(packet, body + 4, spec.Entity);
            packet[body + 6] = spec.ForceId;
            packet[body + 8] = 3;
            WriteWorld(packet, body + 36, spec.X, spec.Y, spec.Z);
            WriteVec3(packet, body + 60, spec.Psi, spec.Theta, spec.Phi);
            WriteVec3(packet, body + 24, spec.VelocityX, spec.VelocityY, spec.VelocityZ);
            WriteU32(packet, body + 72, 0xAABBCCDDu);
            packet[body + 76] = 4;
            for (int i = 0; i < 15; i++)
            {
                packet[body + 77 + i] = (byte)(i + 1);
            }
            WriteVec3(packet, body + 92, 0.5f, 0.6f, 0.7f);
            WriteVec3(packet, body + 104, 1.5f, 1.6f, 1.7f);
            WriteU32(packet, body + 128, 0x01020304u);
            return packet;
        }

        private static void WriteU16(byte[] packet, int offset, int value)
        {
            packet[offset] = (byte)((value >> 8) & 0xFF);
            packet[offset + 1] = (byte)(value & 0xFF);
        }

        private static void WriteU32(byte[] packet, int offset, uint value)
        {
            packet[offset] = (byte)((value >> 24) & 0xFF);
            packet[offset + 1] = (byte)((value >> 16) & 0xFF);
            packet[offset + 2] = (byte)((value >> 8) & 0xFF);
            packet[offset + 3] = (byte)(value & 0xFF);
        }

        private static void WriteFloat(byte[] packet, int offset, float value)
        {
            byte[] bytes = BitConverter.GetBytes(value);
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(bytes);
            }
            Array.Copy(bytes, 0, packet, offset, 4);
        }

        private static void WriteDouble(byte[] packet, int offset, double value)
        {
            byte[] bytes = BitConverter.GetBytes(value);
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(bytes);
            }
            Array.Copy(bytes, 0, packet, offset, 8);
        }

        private static void WriteVec3(byte[] packet, int offset, float x, float y, float z)
        {
            WriteFloat(packet, offset, x);
            WriteFloat(packet, offset + 4, y);
            WriteFloat(packet, offset + 8, z);
        }

        private static void WriteWorld(byte[] packet, int offset, double x, double y, double z)
        {
            WriteDouble(packet, offset, x);
            WriteDouble(packet, offset + 8, y);
            WriteDouble(packet, offset + 16, z);
        }
    }
}
