using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisWorld : MonoBehaviour
    {
        [SerializeField]
        private double originLatitudeDeg;

        [SerializeField]
        private double originLongitudeDeg;

        [SerializeField]
        private double originHeightMeters;

        [SerializeField]
        private FastDisEntityMap entityMap;

        public bool NativeLibraryAvailable
        {
            get
            {
                return FastDisNative.TryGetAbiVersion(out _);
            }
        }

        public FastDisEntityMap EntityMap => entityMap;
        public double OriginLatitudeDeg => originLatitudeDeg;
        public double OriginLongitudeDeg => originLongitudeDeg;
        public double OriginHeightMeters => originHeightMeters;
    }
}
