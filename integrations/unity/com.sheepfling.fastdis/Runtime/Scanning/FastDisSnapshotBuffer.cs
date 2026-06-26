using System.Collections.Generic;
using FastDIS.Native;

namespace FastDIS.Scanning
{
    public sealed class FastDisSnapshotBuffer
    {
        private readonly List<FastDisEntityTransform> changed = new List<FastDisEntityTransform>();

        public IReadOnlyList<FastDisEntityTransform> Changed => changed;
        public ulong Revision { get; private set; }

        public void Publish(FastDisEntityTransform transform)
        {
            changed.Add(transform);
            Revision++;
        }

        public int ConsumeInto(ICollection<FastDisEntityTransform> destination)
        {
            int count = changed.Count;
            for (int i = 0; i < changed.Count; i++)
            {
                destination.Add(changed[i]);
            }
            changed.Clear();
            return count;
        }

        public void Clear()
        {
            changed.Clear();
        }
    }
}
