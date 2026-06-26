using System.Collections.Generic;
using FastDIS.Native;

namespace FastDIS.Scanning
{
    public sealed class FastDisEntityTable
    {
        private readonly Dictionary<FastDisEntityId, FastDisEntityTransform> latest = new Dictionary<FastDisEntityId, FastDisEntityTransform>();

        public int Count => latest.Count;
        public IEnumerable<KeyValuePair<FastDisEntityId, FastDisEntityTransform>> Entries => latest;

        public bool Upsert(FastDisEntityTransform transform)
        {
            if (latest.TryGetValue(transform.EntityId, out FastDisEntityTransform existing) && Equivalent(existing, transform))
            {
                return false;
            }
            latest[transform.EntityId] = transform;
            return true;
        }

        public bool TryGet(FastDisEntityId entityId, out FastDisEntityTransform transform)
        {
            return latest.TryGetValue(entityId, out transform);
        }

        public bool Remove(FastDisEntityId entityId)
        {
            return latest.Remove(entityId);
        }

        public void Clear()
        {
            latest.Clear();
        }

        private static bool Equivalent(FastDisEntityTransform left, FastDisEntityTransform right)
        {
            return left.EntityId.Site == right.EntityId.Site
                && left.EntityId.Application == right.EntityId.Application
                && left.EntityId.Entity == right.EntityId.Entity
                && left.Timestamp == right.Timestamp
                && left.Appearance == right.Appearance
                && left.FieldsPresent == right.FieldsPresent
                && left.ForceId == right.ForceId
                && left.ExerciseId == right.ExerciseId
                && left.Version == right.Version
                && left.Location.X == right.Location.X
                && left.Location.Y == right.Location.Y
                && left.Location.Z == right.Location.Z
                && left.Orientation.Psi == right.Orientation.Psi
                && left.Orientation.Theta == right.Orientation.Theta
                && left.Orientation.Phi == right.Orientation.Phi
                && left.LinearVelocity.X == right.LinearVelocity.X
                && left.LinearVelocity.Y == right.LinearVelocity.Y
                && left.LinearVelocity.Z == right.LinearVelocity.Z;
        }
    }
}
