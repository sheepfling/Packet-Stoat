using System.Collections.Generic;
using FastDIS.Native;

namespace FastDIS.Scanning
{
    public sealed class FastDisScanner
    {
        public bool NativeAvailable => FastDisNative.TryGetAbiVersion(out _);

        public IReadOnlyList<FastDisPacketView> Scan(IEnumerable<byte[]> packets)
        {
            List<FastDisPacketView> views = new List<FastDisPacketView>();
            foreach (byte[] packet in packets)
            {
                if (packet != null && packet.Length >= 12)
                {
                    views.Add(new FastDisPacketView(packet));
                }
            }
            return views;
        }

        public bool TryParseEntityTransform(byte[] packet, out FastDisEntityTransform transform)
        {
            return FastDisNative.TryParseEntityTransform(packet, out transform);
        }

        public bool TryParseCreateEntity(byte[] packet, out FastDisSimulationManagementRequest request)
        {
            return FastDisNative.TryParseCreateEntity(packet, out request);
        }

        public bool TryParseFire(byte[] packet, out FastDisFire fire)
        {
            return FastDisNative.TryParseFire(packet, out fire);
        }

        public bool TryParseDetonation(byte[] packet, out FastDisDetonation detonation)
        {
            return FastDisNative.TryParseDetonation(packet, out detonation);
        }

        public bool TryParseRemoveEntity(byte[] packet, out FastDisSimulationManagementRequest request)
        {
            return FastDisNative.TryParseRemoveEntity(packet, out request);
        }

        public bool TryParseStartResume(byte[] packet, out FastDisStartResume request)
        {
            return FastDisNative.TryParseStartResume(packet, out request);
        }

        public bool TryParseStopFreeze(byte[] packet, out FastDisStopFreeze request)
        {
            return FastDisNative.TryParseStopFreeze(packet, out request);
        }

        public IReadOnlyList<FastDisEntityTransform> ScanEntityTransforms(IEnumerable<byte[]> packets)
        {
            List<FastDisEntityTransform> transforms = new List<FastDisEntityTransform>();
            foreach (byte[] packet in packets)
            {
                if (FastDisNative.TryParseEntityTransform(packet, out FastDisEntityTransform transform))
                {
                    transforms.Add(transform);
                }
            }
            return transforms;
        }
    }
}
