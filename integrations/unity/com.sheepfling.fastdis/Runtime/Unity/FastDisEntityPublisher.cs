using System;
using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisEntityPublisher : MonoBehaviour
    {
        public enum PublishReason
        {
            None = 0,
            Initial = 1,
            Heartbeat = 2,
            Threshold = 3,
        }

        [SerializeField]
        private FastDisNetworkSender sender;

        [SerializeField]
        private FastDisEntityId entityId;

        [SerializeField]
        private byte version = 7;

        [SerializeField]
        private byte forceId = 1;

        [SerializeField]
        private FastDisUnityFrameProfile frameProfile = FastDisUnityFrameProfile.StandaloneEastUpNorth;

        [SerializeField]
        private float heartbeatSeconds = 5.0f;

        [SerializeField]
        private float positionThresholdMeters = 1.0f;

        [SerializeField]
        private float orientationThresholdDegrees = 3.0f;

        [SerializeField]
        private bool publishInitialState = true;

        private bool hasPublished;
        private float lastPublishSeconds;
        private Vector3 lastPublishedPosition;
        private Quaternion lastPublishedRotation;
        private ulong heartbeatPublishes;
        private ulong thresholdPublishes;
        private ulong totalPublishes;
        private PublishReason lastPublishReason;

        public FastDisNetworkSender Sender
        {
            get => sender;
            set => sender = value;
        }

        public FastDisEntityId EntityId
        {
            get => entityId;
            set => entityId = value;
        }

        public byte Version
        {
            get => version;
            set => version = value == 0 ? (byte)7 : value;
        }

        public byte ForceId
        {
            get => forceId;
            set => forceId = value;
        }

        public FastDisUnityFrameProfile FrameProfile
        {
            get => frameProfile;
            set => frameProfile = value;
        }

        public float HeartbeatSeconds
        {
            get => heartbeatSeconds;
            set => heartbeatSeconds = Mathf.Max(0.0f, value);
        }

        public float PositionThresholdMeters
        {
            get => positionThresholdMeters;
            set => positionThresholdMeters = Mathf.Max(0.0f, value);
        }

        public float OrientationThresholdDegrees
        {
            get => orientationThresholdDegrees;
            set => orientationThresholdDegrees = Mathf.Max(0.0f, value);
        }

        public bool PublishInitialState
        {
            get => publishInitialState;
            set => publishInitialState = value;
        }

        public ulong HeartbeatPublishes => heartbeatPublishes;
        public ulong ThresholdPublishes => thresholdPublishes;
        public ulong TotalPublishes => totalPublishes;
        public PublishReason LastPublishReason => lastPublishReason;

        private void Update()
        {
            Tick(Time.realtimeSinceStartup);
        }

        public bool Tick(float nowSeconds)
        {
            FastDisNetworkSender resolvedSender = sender != null ? sender : GetComponent<FastDisNetworkSender>();
            if (resolvedSender == null)
            {
                return false;
            }

            Vector3 position = transform.localPosition;
            Quaternion rotation = transform.localRotation;
            PublishReason reason = ClassifyPublish(position, rotation, nowSeconds);
            if (reason == PublishReason.None)
            {
                return false;
            }

            if (!resolvedSender.SendEntityState(BuildSpec(position, rotation)))
            {
                return false;
            }

            sender = resolvedSender;
            hasPublished = true;
            lastPublishSeconds = nowSeconds;
            lastPublishedPosition = position;
            lastPublishedRotation = rotation;
            lastPublishReason = reason;
            totalPublishes++;
            if (reason == PublishReason.Heartbeat)
            {
                heartbeatPublishes++;
            }
            else if (reason == PublishReason.Threshold)
            {
                thresholdPublishes++;
            }

            return true;
        }

        private PublishReason ClassifyPublish(Vector3 position, Quaternion rotation, float nowSeconds)
        {
            if (!hasPublished)
            {
                return publishInitialState ? PublishReason.Initial : PublishReason.None;
            }

            if (positionThresholdMeters > 0.0f)
            {
                if (Vector3.Distance(lastPublishedPosition, position) >= positionThresholdMeters)
                {
                    return PublishReason.Threshold;
                }
            }

            if (orientationThresholdDegrees > 0.0f)
            {
                if (Quaternion.Angle(lastPublishedRotation, rotation) >= orientationThresholdDegrees)
                {
                    return PublishReason.Threshold;
                }
            }

            if (heartbeatSeconds <= 0.0f)
            {
                return PublishReason.Heartbeat;
            }

            return nowSeconds - lastPublishSeconds >= heartbeatSeconds
                ? PublishReason.Heartbeat
                : PublishReason.None;
        }

        private FastDisNetworkSender.EntityStateSpec BuildSpec(Vector3 unityPosition, Quaternion unityRotation)
        {
            Vector3 enuPosition = FastDisTransformMapper.UnityToEnu(unityPosition, frameProfile);
            Vector3 unityEuler = unityRotation.eulerAngles;
            return new FastDisNetworkSender.EntityStateSpec
            {
                Version = version,
                Site = entityId.Site,
                Application = entityId.Application,
                Entity = entityId.Entity,
                ForceId = forceId,
                X = enuPosition.x,
                Y = enuPosition.y,
                Z = enuPosition.z,
                Psi = unityEuler.y * Mathf.Deg2Rad,
                Theta = unityEuler.x * Mathf.Deg2Rad,
                Phi = unityEuler.z * Mathf.Deg2Rad,
                VelocityX = 0.0f,
                VelocityY = 0.0f,
                VelocityZ = 0.0f,
            };
        }
    }
}
