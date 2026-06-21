using FastDIS.Native;
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
        private FastDisUnityFrameProfile frameProfile = FastDisUnityFrameProfile.StandaloneEastUpNorth;

        [SerializeField]
        private FastDisEntityMapping entityMapping;

        public bool NativeLibraryAvailable => FastDisNative.TryGetAbiVersion(out _);
        public double OriginLatitudeDeg => originLatitudeDeg;
        public double OriginLongitudeDeg => originLongitudeDeg;
        public double OriginHeightMeters => originHeightMeters;
        public FastDisUnityFrameProfile FrameProfile => frameProfile;
        public FastDisEntityMapping EntityMapping => entityMapping;
    }
}
