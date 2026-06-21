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
            public GameObject Prefab;
        }

        [SerializeField]
        private Entry[] entries = Array.Empty<Entry>();

        public Entry[] Entries => entries;
    }
}
