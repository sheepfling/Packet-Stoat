using UnityEngine;

namespace FastDIS.Unity
{
    public static class FastDisFrameTransform
    {
        public static Vector3 EnuToUnity(Vector3 enuMeters)
        {
            return new Vector3(enuMeters.x, enuMeters.z, enuMeters.y);
        }

        public static Quaternion BodyBasisToUnityRotation(Vector3 forwardEnu, Vector3 upEnu)
        {
            Vector3 forward = EnuToUnity(forwardEnu).normalized;
            Vector3 up = EnuToUnity(upEnu).normalized;
            return Quaternion.LookRotation(forward, up);
        }
    }
}
