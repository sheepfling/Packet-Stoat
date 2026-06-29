using UnityEngine;

namespace FastDIS.Unity
{
    public static class FastDisTransformMapper
    {
        public static Vector3 EnuToUnity(Vector3 enuMeters, FastDisUnityFrameProfile profile = FastDisUnityFrameProfile.StandaloneEastUpNorth)
        {
            switch (profile)
            {
                case FastDisUnityFrameProfile.CesiumForUnity:
                case FastDisUnityFrameProfile.StandaloneEastUpNorth:
                default:
                    return new Vector3(enuMeters.x, enuMeters.z, enuMeters.y);
            }
        }

        public static Vector3 UnityToEnu(Vector3 unityMeters, FastDisUnityFrameProfile profile = FastDisUnityFrameProfile.StandaloneEastUpNorth)
        {
            switch (profile)
            {
                case FastDisUnityFrameProfile.CesiumForUnity:
                case FastDisUnityFrameProfile.StandaloneEastUpNorth:
                default:
                    return new Vector3(unityMeters.x, unityMeters.z, unityMeters.y);
            }
        }

        public static Quaternion BodyBasisToUnityRotation(
            Vector3 forwardEnu,
            Vector3 upEnu,
            FastDisUnityFrameProfile profile = FastDisUnityFrameProfile.StandaloneEastUpNorth)
        {
            Vector3 forward = EnuToUnity(forwardEnu, profile).normalized;
            Vector3 up = EnuToUnity(upEnu, profile).normalized;
            return Quaternion.LookRotation(forward, up);
        }
    }
}
