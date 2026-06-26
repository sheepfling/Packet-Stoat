using System;
using UnityEngine;

namespace FastDIS.Unity
{
    [CreateAssetMenu(menuName = "FastDIS/Entity Mapping", fileName = "FastDisEntityMapping")]
    public sealed class FastDisEntityMapping : ScriptableObject
    {
        [Serializable]
        public struct Entry
        {
            public string EntityType;
            public int Priority;
            public GameObject Prefab;
        }

        [SerializeField]
        private Entry[] entries = Array.Empty<Entry>();

        [SerializeField]
        private GameObject defaultPrefab;

        public Entry[] Entries => entries;
        public GameObject DefaultPrefab => defaultPrefab;

        public GameObject ResolvePrefab(FastDisEntityId entityId)
        {
            string exact = $"{entityId.Site}:{entityId.Application}:{entityId.Entity}";
            GameObject bestPrefab = null;
            int bestSpecificity = -1;
            int bestPriority = int.MinValue;
            for (int i = 0; i < entries.Length; i++)
            {
                Entry entry = entries[i];
                if (entry.Prefab == null)
                {
                    continue;
                }

                if (!TryMatch(entry.EntityType, entityId, out int specificity))
                {
                    continue;
                }

                if (specificity > bestSpecificity
                    || (specificity == bestSpecificity && entry.Priority > bestPriority))
                {
                    bestPrefab = entry.Prefab;
                    bestSpecificity = specificity;
                    bestPriority = entry.Priority;
                }
            }

            return bestPrefab != null ? bestPrefab : defaultPrefab;
        }

        private static bool TryMatch(string pattern, FastDisEntityId entityId, out int specificity)
        {
            specificity = -1;
            if (string.IsNullOrWhiteSpace(pattern))
            {
                return false;
            }

            if (string.Equals(pattern, "*", StringComparison.Ordinal))
            {
                specificity = 0;
                return true;
            }

            string[] parts = pattern.Split(':');
            if (parts.Length != 3)
            {
                return false;
            }

            ushort[] values = { entityId.Site, entityId.Application, entityId.Entity };
            int matchedSegments = 0;
            for (int i = 0; i < 3; i++)
            {
                string part = parts[i].Trim();
                if (part == "*")
                {
                    continue;
                }

                if (!ushort.TryParse(part, out ushort parsed) || parsed != values[i])
                {
                    specificity = -1;
                    return false;
                }

                matchedSegments++;
            }

            specificity = matchedSegments;
            return true;
        }
    }
}
