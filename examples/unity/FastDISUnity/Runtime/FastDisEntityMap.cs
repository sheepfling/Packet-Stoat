using System;
using UnityEngine;

namespace FastDIS.Unity
{
    [CreateAssetMenu(menuName = "FastDIS/Entity Map")]
    public sealed class FastDisEntityMap : ScriptableObject
    {
        [SerializeField]
        private Entry[] entries = Array.Empty<Entry>();

        public GameObject FindPrefab(FastDisEntityId entityId)
        {
            foreach (Entry entry in entries)
            {
                if (entry.entityId.site == entityId.site
                    && entry.entityId.application == entityId.application
                    && entry.entityId.entity == entityId.entity)
                {
                    return entry.prefab;
                }
            }

            return null;
        }

        [Serializable]
        private struct Entry
        {
            public FastDisEntityId entityId;
            public GameObject prefab;
        }
    }
}
