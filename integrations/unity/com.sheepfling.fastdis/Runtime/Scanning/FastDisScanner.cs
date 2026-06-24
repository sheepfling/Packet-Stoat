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
