using FastDIS.Native;
using FastDIS.Scanning;
using System;
using System.Collections.Generic;
using UnityEngine;
using NativeEntityId = FastDIS.Native.FastDisEntityId;

namespace FastDIS.Unity
{
    public sealed class FastDisWorld : MonoBehaviour
    {
        public enum GroundClampPolicyKind
        {
            None = 0,
            ClampToZeroY = 1,
        }

        public enum CullingPolicyKind
        {
            None = 0,
            Distance = 1,
        }

        public event Action<FastDisFire> FireReceived;
        public event Action<FastDisDetonation> DetonationReceived;
        public event Action<FastDisStartResume> StartResumeReceived;
        public event Action<FastDisStopFreeze> StopFreezeReceived;
        public event Action<FastDisDesignator> DesignatorReceived;
        public event Action<FastDisSignal> SignalReceived;
        public event Action<FastDisElectronicEmissions> ElectronicEmissionsReceived;
        public event Action<FastDisTransmitter> TransmitterReceived;
        public event Action<FastDisReceiver> ReceiverReceived;
        public event Action<FastDisIff> IffReceived;
        public event Action<FastDisAttribute> AttributeReceived;
        public event Action<FastDisDirectedEnergyFire> DirectedEnergyFireReceived;
        public event Action<FastDisEntityDamageStatus> EntityDamageStatusReceived;
        public event Action<FastDisCollision> CollisionReceived;
        public event Action<FastDisCollisionElastic> CollisionElasticReceived;

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

        [SerializeField]
        private bool autoSpawnActors = true;

        [SerializeField]
        private bool destroyActorsOnRemove = true;

        [SerializeField]
        private bool applyOrientation;

        [SerializeField]
        private float staleTimeoutSeconds;

        [SerializeField]
        private bool deadReckoningEnabled = true;

        [SerializeField]
        private float smoothingDurationSeconds = 0.15f;

        [SerializeField]
        private float teleportDistanceMeters = 25.0f;

        [SerializeField]
        private GroundClampPolicyKind groundClampPolicy = GroundClampPolicyKind.None;

        [SerializeField]
        private CullingPolicyKind cullingPolicy = CullingPolicyKind.None;

        [SerializeField]
        private float cullingDistanceMeters = 1000.0f;

        private readonly FastDisScanner scanner = new FastDisScanner();
        private readonly FastDisEntityTable entityTable = new FastDisEntityTable();
        private readonly FastDisSnapshotBuffer snapshotBuffer = new FastDisSnapshotBuffer();
        private readonly Dictionary<FastDisEntityId, Transform> actors = new Dictionary<FastDisEntityId, Transform>();
        private readonly Dictionary<FastDisEntityId, float> lastSeenSeconds = new Dictionary<FastDisEntityId, float>();
        private readonly Dictionary<FastDisEntityId, ActorSmoothingState> smoothingStates = new Dictionary<FastDisEntityId, ActorSmoothingState>();
        private readonly List<FastDisEntityTransform> publishScratch = new List<FastDisEntityTransform>();
        private ulong packetsProcessed;
        private ulong entitiesSpawned;
        private ulong removeRequests;
        private ulong staleRemovals;
        private ulong deadReckoningUpdates;
        private ulong fireEventsReceived;
        private ulong detonationEventsReceived;
        private ulong startResumeEventsReceived;
        private ulong stopFreezeEventsReceived;
        private ulong designatorEventsReceived;
        private ulong signalEventsReceived;
        private ulong electronicEmissionsEventsReceived;
        private ulong transmitterEventsReceived;
        private ulong receiverEventsReceived;
        private ulong iffEventsReceived;
        private ulong attributeEventsReceived;
        private ulong directedEnergyFireEventsReceived;
        private ulong entityDamageStatusEventsReceived;
        private ulong collisionEventsReceived;
        private ulong collisionElasticEventsReceived;
        private ulong groundClampApplications;
        private ulong cullingSkips;
        private ulong malformedPackets;
        private string lastPdu = "none";

        private struct ActorSmoothingState
        {
            public Vector3 TargetPosition;
            public float StartSeconds;
            public float EndSeconds;
        }

        public bool NativeLibraryAvailable => FastDisNative.TryGetAbiVersion(out _);
        public double OriginLatitudeDeg => originLatitudeDeg;
        public double OriginLongitudeDeg => originLongitudeDeg;
        public double OriginHeightMeters => originHeightMeters;
        public FastDisUnityFrameProfile FrameProfile => frameProfile;
        public FastDisEntityMapping EntityMapping => entityMapping;
        public bool AutoSpawnActors => autoSpawnActors;
        public bool DestroyActorsOnRemove => destroyActorsOnRemove;
        public bool ApplyOrientation => applyOrientation;
        public bool DeadReckoningEnabled
        {
            get => deadReckoningEnabled;
            set => deadReckoningEnabled = value;
        }
        public float SmoothingDurationSeconds
        {
            get => smoothingDurationSeconds;
            set => smoothingDurationSeconds = Mathf.Max(0.0f, value);
        }
        public float TeleportDistanceMeters
        {
            get => teleportDistanceMeters;
            set => teleportDistanceMeters = Mathf.Max(0.0f, value);
        }
        public GroundClampPolicyKind GroundClampPolicy
        {
            get => groundClampPolicy;
            set => groundClampPolicy = value;
        }
        public CullingPolicyKind CullingPolicy
        {
            get => cullingPolicy;
            set => cullingPolicy = value;
        }
        public float CullingDistanceMeters
        {
            get => cullingDistanceMeters;
            set => cullingDistanceMeters = Mathf.Max(0.0f, value);
        }
        public float StaleTimeoutSeconds
        {
            get => staleTimeoutSeconds;
            set => staleTimeoutSeconds = Mathf.Max(0.0f, value);
        }
        public int KnownEntityCount => entityTable.Count;
        public int BoundActorCount => actors.Count;
        public ulong PacketsProcessed => packetsProcessed;
        public ulong EntitiesSpawned => entitiesSpawned;
        public ulong RemoveRequests => removeRequests;
        public ulong StaleRemovals => staleRemovals;
        public ulong DeadReckoningUpdates => deadReckoningUpdates;
        public ulong FireEventsReceived => fireEventsReceived;
        public ulong DetonationEventsReceived => detonationEventsReceived;
        public ulong StartResumeEventsReceived => startResumeEventsReceived;
        public ulong StopFreezeEventsReceived => stopFreezeEventsReceived;
        public ulong DesignatorEventsReceived => designatorEventsReceived;
        public ulong SignalEventsReceived => signalEventsReceived;
        public ulong ElectronicEmissionsEventsReceived => electronicEmissionsEventsReceived;
        public ulong TransmitterEventsReceived => transmitterEventsReceived;
        public ulong ReceiverEventsReceived => receiverEventsReceived;
        public ulong IffEventsReceived => iffEventsReceived;
        public ulong AttributeEventsReceived => attributeEventsReceived;
        public ulong DirectedEnergyFireEventsReceived => directedEnergyFireEventsReceived;
        public ulong EntityDamageStatusEventsReceived => entityDamageStatusEventsReceived;
        public ulong CollisionEventsReceived => collisionEventsReceived;
        public ulong CollisionElasticEventsReceived => collisionElasticEventsReceived;
        public ulong GroundClampApplications => groundClampApplications;
        public ulong CullingSkips => cullingSkips;
        public ulong MalformedPackets => malformedPackets;
        public string LastPdu => lastPdu;

        private void Update()
        {
            AdvanceSimulation(Time.realtimeSinceStartup);
        }

        public bool ProcessPacket(byte[] packet)
        {
            return ProcessPacket(packet, Time.realtimeSinceStartup);
        }

        public bool ProcessPacket(byte[] packet, float nowSeconds)
        {
            if (packet == null || packet.Length < 12)
            {
                malformedPackets++;
                return false;
            }

            packetsProcessed++;
            if (FastDisHeaderView.TryParse(packet, out FastDisHeaderView header))
            {
                lastPdu = DescribeHeader(header);
            }

            if (scanner.TryParseEntityTransform(packet, out FastDisEntityTransform transform))
            {
                MarkEntitySeen(ToUnityEntityId(transform.EntityId), nowSeconds);
                bool changed = entityTable.Upsert(transform);
                if (changed)
                {
                    snapshotBuffer.Publish(transform);
                    ApplyPublishedChanges();
                }
                return true;
            }

            if (scanner.TryParseRemoveEntity(packet, out FastDisSimulationManagementRequest remove))
            {
                removeRequests++;
                HandleRemove(ToUnityEntityId(remove.ReceivingEntityId));
                return true;
            }

            if (scanner.TryParseRemoveEntityReliable(packet, out FastDisSimulationManagementReliableRequest removeReliable))
            {
                removeRequests++;
                HandleRemove(ToUnityEntityId(removeReliable.ReceivingEntityId));
                return true;
            }

            if (scanner.TryParseCreateEntity(packet, out FastDisSimulationManagementRequest create))
            {
                EnsureActor(ToUnityEntityId(create.ReceivingEntityId));
                return true;
            }

            if (scanner.TryParseCreateEntityReliable(packet, out FastDisSimulationManagementReliableRequest createReliable))
            {
                EnsureActor(ToUnityEntityId(createReliable.ReceivingEntityId));
                return true;
            }

            if (scanner.TryParseFire(packet, out FastDisFire fire))
            {
                fireEventsReceived++;
                FireReceived?.Invoke(fire);
                return true;
            }

            if (scanner.TryParseDetonation(packet, out FastDisDetonation detonation))
            {
                detonationEventsReceived++;
                DetonationReceived?.Invoke(detonation);
                return true;
            }

            if (scanner.TryParseStartResume(packet, out FastDisStartResume startResume))
            {
                startResumeEventsReceived++;
                StartResumeReceived?.Invoke(startResume);
                return true;
            }

            if (scanner.TryParseStopFreeze(packet, out FastDisStopFreeze stopFreeze))
            {
                stopFreezeEventsReceived++;
                StopFreezeReceived?.Invoke(stopFreeze);
                return true;
            }

            if (scanner.TryParseDesignator(packet, out FastDisDesignator designator))
            {
                designatorEventsReceived++;
                DesignatorReceived?.Invoke(designator);
                return true;
            }

            if (scanner.TryParseSignal(packet, out FastDisSignal signal))
            {
                signalEventsReceived++;
                SignalReceived?.Invoke(signal);
                return true;
            }

            if (scanner.TryParseElectronicEmissions(packet, out FastDisElectronicEmissions emissions))
            {
                electronicEmissionsEventsReceived++;
                ElectronicEmissionsReceived?.Invoke(emissions);
                return true;
            }

            if (scanner.TryParseTransmitter(packet, out FastDisTransmitter transmitter))
            {
                transmitterEventsReceived++;
                TransmitterReceived?.Invoke(transmitter);
                return true;
            }

            if (scanner.TryParseReceiver(packet, out FastDisReceiver receiver))
            {
                receiverEventsReceived++;
                ReceiverReceived?.Invoke(receiver);
                return true;
            }

            if (scanner.TryParseIff(packet, out FastDisIff iff))
            {
                iffEventsReceived++;
                IffReceived?.Invoke(iff);
                return true;
            }

            if (scanner.TryParseAttribute(packet, out FastDisAttribute attribute))
            {
                attributeEventsReceived++;
                AttributeReceived?.Invoke(attribute);
                return true;
            }

            if (scanner.TryParseDirectedEnergyFire(packet, out FastDisDirectedEnergyFire directedEnergyFire))
            {
                directedEnergyFireEventsReceived++;
                DirectedEnergyFireReceived?.Invoke(directedEnergyFire);
                return true;
            }

            if (scanner.TryParseEntityDamageStatus(packet, out FastDisEntityDamageStatus entityDamageStatus))
            {
                entityDamageStatusEventsReceived++;
                EntityDamageStatusReceived?.Invoke(entityDamageStatus);
                return true;
            }

            if (scanner.TryParseCollision(packet, out FastDisCollision collision))
            {
                collisionEventsReceived++;
                CollisionReceived?.Invoke(collision);
                return true;
            }

            if (scanner.TryParseCollisionElastic(packet, out FastDisCollisionElastic collisionElastic))
            {
                collisionElasticEventsReceived++;
                CollisionElasticReceived?.Invoke(collisionElastic);
                return true;
            }

            return false;
        }

        public int ProcessPackets(IEnumerable<byte[]> packets)
        {
            int processed = 0;
            foreach (byte[] packet in packets)
            {
                if (ProcessPacket(packet))
                {
                    processed++;
                }
            }
            return processed;
        }

        public int ProcessPackets(IEnumerable<byte[]> packets, float nowSeconds)
        {
            int processed = 0;
            foreach (byte[] packet in packets)
            {
                if (ProcessPacket(packet, nowSeconds))
                {
                    processed++;
                }
            }
            return processed;
        }

        public bool TryGetEntityTransform(FastDisEntityId entityId, out FastDisEntityTransform transform)
        {
            return entityTable.TryGet(ToNativeEntityId(entityId), out transform);
        }

        public bool TryGetBoundActor(FastDisEntityId entityId, out Transform actor)
        {
            return actors.TryGetValue(entityId, out actor);
        }

        public void RegisterActor(FastDisEntityId entityId, Transform actor)
        {
            if (actor != null)
            {
                actors[entityId] = actor;
                actor.name = DescribeEntity(entityId);
            }
        }

        public void ClearRuntimeState()
        {
            entityTable.Clear();
            snapshotBuffer.Clear();
            packetsProcessed = 0;
            entitiesSpawned = 0;
            removeRequests = 0;
            staleRemovals = 0;
            deadReckoningUpdates = 0;
            fireEventsReceived = 0;
            detonationEventsReceived = 0;
            startResumeEventsReceived = 0;
            stopFreezeEventsReceived = 0;
            designatorEventsReceived = 0;
            signalEventsReceived = 0;
            electronicEmissionsEventsReceived = 0;
            transmitterEventsReceived = 0;
            receiverEventsReceived = 0;
            iffEventsReceived = 0;
            attributeEventsReceived = 0;
            directedEnergyFireEventsReceived = 0;
            entityDamageStatusEventsReceived = 0;
            collisionEventsReceived = 0;
            collisionElasticEventsReceived = 0;
            groundClampApplications = 0;
            cullingSkips = 0;
            malformedPackets = 0;
            lastPdu = "none";
            publishScratch.Clear();
            lastSeenSeconds.Clear();
            smoothingStates.Clear();
            actors.Clear();
        }

        public int AdvanceSimulation(float nowSeconds)
        {
            int removed = RemoveExpiredEntities(nowSeconds);
            int predicted = ApplyDeadReckoning(nowSeconds);
            ApplySmoothing(nowSeconds);
            return removed + predicted;
        }

        public int RemoveExpiredEntities(float nowSeconds)
        {
            if (staleTimeoutSeconds <= 0.0f || lastSeenSeconds.Count == 0)
            {
                return 0;
            }

            List<FastDisEntityId> expired = null;
            foreach (KeyValuePair<FastDisEntityId, float> item in lastSeenSeconds)
            {
                if (nowSeconds - item.Value < staleTimeoutSeconds)
                {
                    continue;
                }

                if (expired == null)
                {
                    expired = new List<FastDisEntityId>();
                }
                expired.Add(item.Key);
            }

            if (expired == null)
            {
                return 0;
            }

            for (int i = 0; i < expired.Count; i++)
            {
                staleRemovals++;
                HandleRemove(expired[i]);
            }
            return expired.Count;
        }

        private void ApplyPublishedChanges()
        {
            publishScratch.Clear();
            snapshotBuffer.ConsumeInto(publishScratch);
            for (int i = 0; i < publishScratch.Count; i++)
            {
                FastDisEntityTransform transform = publishScratch[i];
                Transform actor = EnsureActor(ToUnityEntityId(transform.EntityId));
                if (actor != null)
                {
                    ApplyTransformToActor(ToUnityEntityId(transform.EntityId), actor, transform, lastSeenSeconds[ToUnityEntityId(transform.EntityId)], smooth: true);
                }
            }
            publishScratch.Clear();
        }

        private void HandleRemove(FastDisEntityId entityId)
        {
            entityTable.Remove(ToNativeEntityId(entityId));
            lastSeenSeconds.Remove(entityId);
            smoothingStates.Remove(entityId);
            if (!actors.TryGetValue(entityId, out Transform actor))
            {
                return;
            }

            actors.Remove(entityId);
            if (actor == null)
            {
                return;
            }

            if (destroyActorsOnRemove)
            {
                DestroyImmediate(actor.gameObject);
            }
            else
            {
                actor.gameObject.SetActive(false);
            }
        }

        private Transform EnsureActor(FastDisEntityId entityId)
        {
            if (actors.TryGetValue(entityId, out Transform actor) && actor != null)
            {
                return actor;
            }
            if (!autoSpawnActors)
            {
                return null;
            }

            GameObject instance = null;
            GameObject prefab = entityMapping != null ? entityMapping.ResolvePrefab(entityId) : null;
            if (prefab != null)
            {
                instance = Instantiate(prefab, transform);
            }
            else
            {
                instance = new GameObject(DescribeEntity(entityId));
                instance.transform.SetParent(transform, false);
            }

            actor = instance.transform;
            actors[entityId] = actor;
            entitiesSpawned++;
            return actor;
        }

        private void MarkEntitySeen(FastDisEntityId entityId, float nowSeconds)
        {
            lastSeenSeconds[entityId] = nowSeconds;
        }

        private int ApplyDeadReckoning(float nowSeconds)
        {
            if (!deadReckoningEnabled || lastSeenSeconds.Count == 0)
            {
                return 0;
            }

            int updated = 0;
            foreach (KeyValuePair<FastDisEntityId, float> item in lastSeenSeconds)
            {
                if (!actors.TryGetValue(item.Key, out Transform actor) || actor == null)
                {
                    continue;
                }
                if (!entityTable.TryGet(ToNativeEntityId(item.Key), out FastDisEntityTransform transform))
                {
                    continue;
                }

                float deltaSeconds = Mathf.Max(0.0f, nowSeconds - item.Value);
                if (deltaSeconds <= 0.0f)
                {
                    continue;
                }

                if (FastDisNative.DeadReckoningAlgorithmKnown(transform.DeadReckoningAlgorithm)
                    && FastDisNative.TryExtrapolateEntityTransformDeadReckoning(transform, deltaSeconds, out FastDisEntityTransform extrapolated))
                {
                    ApplyTransformToActor(item.Key, actor, extrapolated, nowSeconds, smooth: false);
                    deadReckoningUpdates++;
                    updated++;
                    continue;
                }

                if (transform.HasField(FastDisNative.FastDisEsFieldLinearVelocity))
                {
                    FastDisEntityTransform linear = transform;
                    linear.Location.X += linear.LinearVelocity.X * deltaSeconds;
                    linear.Location.Y += linear.LinearVelocity.Y * deltaSeconds;
                    linear.Location.Z += linear.LinearVelocity.Z * deltaSeconds;
                    ApplyTransformToActor(item.Key, actor, linear, nowSeconds, smooth: false);
                    deadReckoningUpdates++;
                    updated++;
                }
            }
            return updated;
        }

        private void ApplySmoothing(float nowSeconds)
        {
            if (smoothingStates.Count == 0)
            {
                return;
            }

            List<FastDisEntityId> completed = null;
            foreach (KeyValuePair<FastDisEntityId, ActorSmoothingState> item in smoothingStates)
            {
                if (!actors.TryGetValue(item.Key, out Transform actor) || actor == null)
                {
                    if (completed == null)
                    {
                        completed = new List<FastDisEntityId>();
                    }
                    completed.Add(item.Key);
                    continue;
                }

                ActorSmoothingState state = item.Value;
                if (nowSeconds >= state.EndSeconds || state.EndSeconds <= state.StartSeconds)
                {
                    actor.localPosition = state.TargetPosition;
                    if (completed == null)
                    {
                        completed = new List<FastDisEntityId>();
                    }
                    completed.Add(item.Key);
                    continue;
                }

                float alpha = Mathf.Clamp01((nowSeconds - state.StartSeconds) / (state.EndSeconds - state.StartSeconds));
                actor.localPosition = Vector3.Lerp(actor.localPosition, state.TargetPosition, alpha);
            }

            if (completed == null)
            {
                return;
            }

            for (int i = 0; i < completed.Count; i++)
            {
                smoothingStates.Remove(completed[i]);
            }
        }

        private void ApplyTransformToActor(FastDisEntityId entityId, Transform actor, FastDisEntityTransform transform, float nowSeconds, bool smooth)
        {
            Vector3 targetPosition = FastDisTransformMapper.EnuToUnity(ToUnityMeters(transform), frameProfile);
            targetPosition = ApplyGroundClamp(targetPosition);

            bool culled = ShouldCull(targetPosition);
            SetActorCulled(actor, culled);
            if (culled)
            {
                smoothingStates.Remove(entityId);
                cullingSkips++;
                return;
            }

            if (smooth && smoothingDurationSeconds > 0.0f && Vector3.Distance(actor.localPosition, targetPosition) <= teleportDistanceMeters)
            {
                smoothingStates[entityId] = new ActorSmoothingState
                {
                    TargetPosition = targetPosition,
                    StartSeconds = nowSeconds,
                    EndSeconds = nowSeconds + smoothingDurationSeconds,
                };
            }
            else
            {
                actor.localPosition = targetPosition;
                smoothingStates.Remove(entityId);
            }

            if (applyOrientation)
            {
                actor.localRotation = Quaternion.Euler(
                    Mathf.Rad2Deg * transform.Orientation.Theta,
                    Mathf.Rad2Deg * transform.Orientation.Psi,
                    Mathf.Rad2Deg * transform.Orientation.Phi);
            }
        }

        private Vector3 ApplyGroundClamp(Vector3 targetPosition)
        {
            switch (groundClampPolicy)
            {
                case GroundClampPolicyKind.ClampToZeroY:
                    if (targetPosition.y < 0.0f)
                    {
                        targetPosition.y = 0.0f;
                        groundClampApplications++;
                    }
                    return targetPosition;
                case GroundClampPolicyKind.None:
                default:
                    return targetPosition;
            }
        }

        private bool ShouldCull(Vector3 targetPosition)
        {
            switch (cullingPolicy)
            {
                case CullingPolicyKind.Distance:
                    return cullingDistanceMeters > 0.0f && targetPosition.magnitude > cullingDistanceMeters;
                case CullingPolicyKind.None:
                default:
                    return false;
            }
        }

        private static void SetActorCulled(Transform actor, bool culled)
        {
            if (actor == null)
            {
                return;
            }

            if (actor.gameObject.activeSelf == !culled)
            {
                return;
            }

            actor.gameObject.SetActive(!culled);
        }

        private static string DescribeHeader(FastDisHeaderView header)
        {
            return $"DIS{header.Version} PF{header.ProtocolFamily} PDU{header.PduType}";
        }

        private static string DescribeEntity(FastDisEntityId entityId)
        {
            return $"FastDIS {entityId.Site}:{entityId.Application}:{entityId.Entity}";
        }

        private static FastDisEntityId ToUnityEntityId(NativeEntityId entityId)
        {
            return new FastDisEntityId
            {
                Site = entityId.Site,
                Application = entityId.Application,
                Entity = entityId.Entity,
            };
        }

        private static NativeEntityId ToNativeEntityId(FastDisEntityId entityId)
        {
            return new NativeEntityId
            {
                Site = entityId.Site,
                Application = entityId.Application,
                Entity = entityId.Entity,
            };
        }

        private static Vector3 ToUnityMeters(FastDisEntityTransform transform)
        {
            return new Vector3((float)transform.Location.X, (float)transform.Location.Y, (float)transform.Location.Z);
        }
    }
}
