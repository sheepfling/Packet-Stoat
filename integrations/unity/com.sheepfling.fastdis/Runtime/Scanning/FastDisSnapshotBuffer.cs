using System.Collections.Generic;
using FastDIS.Native;

namespace FastDIS.Scanning
{
    public sealed class FastDisSnapshotBuffer
    {
        private readonly List<FastDisEntityTransform> changed = new List<FastDisEntityTransform>();

        public IReadOnlyList<FastDisEntityTransform> Changed => changed;

        public void Publish(FastDisEntityTransform transform)
        {
            changed.Add(transform);
        }

        public void Clear()
        {
            changed.Clear();
        }
    }
}
