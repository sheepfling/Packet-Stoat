using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisEntityBehaviour : MonoBehaviour
    {
        [SerializeField]
        private FastDisEntityId entityId;

        public FastDisEntityId EntityId => entityId;

        public void ApplyLocalEnuPose(Vector3 positionEnuMeters, Vector3 forwardEnu, Vector3 upEnu)
        {
            transform.localPosition = FastDisFrameTransform.EnuToUnity(positionEnuMeters);
            transform.localRotation = FastDisFrameTransform.BodyBasisToUnityRotation(forwardEnu, upEnu);
        }
    }
}
