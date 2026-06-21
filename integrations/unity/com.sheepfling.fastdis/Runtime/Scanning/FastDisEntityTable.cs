using System.Collections.Generic;
using FastDIS.Native;

namespace FastDIS.Scanning
{
    public sealed class FastDisEntityTable
    {
        private readonly Dictionary<FastDisEntityId, FastDisEntityTransform> latest = new Dictionary<FastDisEntityId, FastDisEntityTransform>();

        public int Count => latest.Count;

        public void Upsert(FastDisEntityTransform transform)
        {
            latest[transform.EntityId] = transform;
        }

        public bool TryGet(FastDisEntityId entityId, out FastDisEntityTransform transform)
        {
            return latest.TryGetValue(entityId, out transform);
        }
    }
}
