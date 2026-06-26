using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Threading;
using FastDIS.Native;
using FastDIS.Scanning;
using FastDIS.Unity;
using NUnit.Framework;
using UnityEngine;

namespace FastDIS.Tests
{
    public sealed class FastDisNetworkLoopbackTests
    {
        [Test]
        public void WorldProcessesEntityStateAndAutoSpawnsActor()
        {
            GameObject root = new GameObject("FastDIS World Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                byte[] packet = CreateEntityStatePdu(7, 2, 10.0, 20.0, 30.0);

                Assert.That(world.ProcessPacket(packet), Is.True);
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));
                Assert.That(world.BoundActorCount, Is.EqualTo(1));
                Assert.That(world.PacketsProcessed, Is.EqualTo(1));
                Assert.That(world.LastPdu, Does.Contain("PDU1"));

                FastDIS.Unity.FastDisEntityId entityId = new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 };
                Assert.That(world.TryGetEntityTransform(entityId, out FastDisEntityTransform transform), Is.True);
                Assert.That(transform.Location.X, Is.EqualTo(10.0).Within(0.0001));
                Assert.That(world.TryGetBoundActor(entityId, out Transform actor), Is.True);
                Assert.That(actor.localPosition.x, Is.EqualTo(10.0f).Within(0.0001f));
                Assert.That(actor.localPosition.y, Is.EqualTo(30.0f).Within(0.0001f));
                Assert.That(actor.localPosition.z, Is.EqualTo(20.0f).Within(0.0001f));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void ReplayPlayerParsesLengthPrefixedReplayAndFeedsWorld()
        {
            GameObject root = new GameObject("FastDIS Replay Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisReplayPlayer replay = root.AddComponent<FastDisReplayPlayer>();

                byte[] first = CreateEntityStatePdu(7, 2, 1.0, 2.0, 3.0);
                byte[] second = CreateEntityStateUpdatePdu(7, 4.0, 5.0, 6.0);
                byte[] replayBytes = BuildReplay(first, second);

                replay.LoadReplay(replayBytes);
                replay.Play();
                Assert.That(replay.PacketCount, Is.EqualTo(2));
                Assert.That(replay.Step(), Is.GreaterThanOrEqualTo(1));
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void ReplayPlayerParsesHeaderedReplayAndFeedsWorld()
        {
            GameObject root = new GameObject("FastDIS Headered Replay Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisReplayPlayer replay = root.AddComponent<FastDisReplayPlayer>();

                byte[] first = CreateEntityStatePdu(7, 2, 1.0, 2.0, 3.0);
                byte[] second = CreateEntityStateUpdatePdu(7, 4.0, 5.0, 6.0);
                byte[] replayBytes = BuildHeaderedReplay(first, second);

                replay.LoadReplay(replayBytes);
                replay.Play();
                Assert.That(replay.PacketCount, Is.EqualTo(2));
                Assert.That(replay.Step(), Is.GreaterThanOrEqualTo(1));
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void ReceiverSocketLoopbackFeedsWorld()
        {
            GameObject root = new GameObject("FastDIS Receiver Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver receiver = root.AddComponent<FastDisNetworkReceiver>();

                ushort port = ReserveLoopbackPort();
                receiver.ConfigureEndpoint("127.0.0.1", port);
                receiver.StartReceiver();
                byte[] packet = CreateEntityStatePdu(6, 1, 7.0, 8.0, 9.0);
                using (UdpClient sender = new UdpClient())
                {
                    sender.Send(packet, packet.Length, new IPEndPoint(IPAddress.Loopback, port));
                }
                bool received = false;
                for (int attempt = 0; attempt < 20; attempt++)
                {
                    if (receiver.PumpAvailable() > 0)
                    {
                        received = true;
                        break;
                    }
                    Thread.Sleep(10);
                }

                Assert.That(received, Is.True);
                Assert.That(receiver.PacketsReceived, Is.EqualTo(1));
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void ReceiverMulticastLoopbackFeedsWorld()
        {
            GameObject root = new GameObject("FastDIS Multicast Receiver Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver receiver = root.AddComponent<FastDisNetworkReceiver>();

                ushort port = ReserveLoopbackPort();
                receiver.ConfigureMulticast("239.255.42.99", port, "127.0.0.1", true);
                receiver.StartReceiver();
                byte[] packet = CreateEntityStatePdu(6, 1, 17.0, 18.0, 19.0);
                using (UdpClient sender = new UdpClient(AddressFamily.InterNetwork))
                {
                    sender.MulticastLoopback = true;
                    sender.Client.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.MulticastInterface, IPAddress.Loopback.GetAddressBytes());
                    sender.Send(packet, packet.Length, new IPEndPoint(IPAddress.Parse("239.255.42.99"), port));
                }
                bool received = false;
                for (int attempt = 0; attempt < 20; attempt++)
                {
                    if (receiver.PumpAvailable() > 0)
                    {
                        received = true;
                        break;
                    }
                    Thread.Sleep(10);
                }

                Assert.That(received, Is.True);
                Assert.That(receiver.MulticastEnabled, Is.True);
                Assert.That(receiver.PacketsReceived, Is.EqualTo(1));
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void SenderRawUnicastFeedsReceiverWorld()
        {
            GameObject root = new GameObject("FastDIS Sender Raw Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver receiver = root.AddComponent<FastDisNetworkReceiver>();
                FastDisNetworkSender sender = root.AddComponent<FastDisNetworkSender>();

                ushort port = ReserveLoopbackPort();
                receiver.ConfigureEndpoint("127.0.0.1", port);
                receiver.StartReceiver();
                sender.ConfigureUnicast("127.0.0.1", port);

                Assert.That(sender.SendRaw(CreateEntityStatePdu(7, 2, 70.0, 80.0, 90.0)), Is.True);
                bool received = false;
                for (int attempt = 0; attempt < 20; attempt++)
                {
                    if (receiver.PumpAvailable() > 0)
                    {
                        received = true;
                        break;
                    }
                    Thread.Sleep(10);
                }

                Assert.That(received, Is.True);
                Assert.That(sender.PacketsSent, Is.EqualTo(1));
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void SenderTypedEntityStateFeedsReceiverWorld()
        {
            GameObject root = new GameObject("FastDIS Sender Typed Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver receiver = root.AddComponent<FastDisNetworkReceiver>();
                FastDisNetworkSender sender = root.AddComponent<FastDisNetworkSender>();

                ushort port = ReserveLoopbackPort();
                receiver.ConfigureEndpoint("127.0.0.1", port);
                receiver.StartReceiver();
                sender.ConfigureUnicast("127.0.0.1", port);

                FastDisNetworkSender.EntityStateSpec spec = new FastDisNetworkSender.EntityStateSpec
                {
                    Version = 7,
                    Site = 0x1111,
                    Application = 0x2222,
                    Entity = 0x4444,
                    ForceId = 2,
                    X = 12.0,
                    Y = 34.0,
                    Z = 56.0,
                    Psi = 0.1f,
                    Theta = 0.2f,
                    Phi = 0.3f,
                    VelocityX = 1.0f,
                    VelocityY = 2.0f,
                    VelocityZ = 3.0f,
                };
                Assert.That(sender.SendEntityState(spec), Is.True);
                bool received = false;
                for (int attempt = 0; attempt < 20; attempt++)
                {
                    if (receiver.PumpAvailable() > 0)
                    {
                        received = true;
                        break;
                    }
                    Thread.Sleep(10);
                }

                Assert.That(received, Is.True);
                Assert.That(sender.PacketsSent, Is.EqualTo(1));
                Assert.That(world.TryGetEntityTransform(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x4444 }, out FastDisEntityTransform transform), Is.True);
                Assert.That(transform.Location.X, Is.EqualTo(12.0).Within(0.0001));
                Assert.That(transform.Location.Y, Is.EqualTo(34.0).Within(0.0001));
                Assert.That(transform.Location.Z, Is.EqualTo(56.0).Within(0.0001));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void RemoveEntityRequestClearsKnownEntity()
        {
            GameObject root = new GameObject("FastDIS Remove Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, 30.0)), Is.True);
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));

                Assert.That(world.ProcessPacket(CreateRemoveEntityPdu(6, 0x1111, 0x2222, 0x3333)), Is.True);
                Assert.That(world.KnownEntityCount, Is.EqualTo(0));
                Assert.That(world.RemoveRequests, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldUsesExactWildcardPriorityAndFallbackPrefabMappings()
        {
            GameObject root = new GameObject("FastDIS Mapping Test");
            GameObject exactPrefab = new GameObject("ExactPrefab");
            GameObject wildcardPrefab = new GameObject("WildcardPrefab");
            GameObject priorityWildcardPrefab = new GameObject("PriorityWildcardPrefab");
            GameObject fallbackPrefab = new GameObject("FallbackPrefab");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisEntityMapping mapping = ScriptableObject.CreateInstance<FastDisEntityMapping>();
                SetPrivateField(
                    mapping,
                    "entries",
                    new[]
                    {
                        new FastDisEntityMapping.Entry
                        {
                            EntityType = "4369:8738:13107",
                            Priority = 0,
                            Prefab = exactPrefab,
                        },
                        new FastDisEntityMapping.Entry
                        {
                            EntityType = "30583:*:*",
                            Priority = 0,
                            Prefab = wildcardPrefab,
                        },
                        new FastDisEntityMapping.Entry
                        {
                            EntityType = "30583:34952:*",
                            Priority = 10,
                            Prefab = priorityWildcardPrefab,
                        },
                    }
                );
                SetPrivateField(mapping, "defaultPrefab", fallbackPrefab);
                SetPrivateField(world, "entityMapping", mapping);

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, 30.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 }, out Transform exactActor), Is.True);
                Assert.That(exactActor.name, Does.StartWith("ExactPrefab"));

                Assert.That(world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0x7777, 0x1234, 0x0001, 40.0, 50.0, 60.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x7777, Application = 0x1234, Entity = 0x0001 }, out Transform wildcardActor), Is.True);
                Assert.That(wildcardActor.name, Does.StartWith("WildcardPrefab"));

                Assert.That(world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0x7777, 0x8888, 0x9999, 41.0, 51.0, 61.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x7777, Application = 0x8888, Entity = 0x9999 }, out Transform priorityWildcardActor), Is.True);
                Assert.That(priorityWildcardActor.name, Does.StartWith("PriorityWildcardPrefab"));

                Assert.That(world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0xAAAA, 0xBBBB, 0xCCCC, 70.0, 80.0, 90.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0xAAAA, Application = 0xBBBB, Entity = 0xCCCC }, out Transform fallbackActor), Is.True);
                Assert.That(fallbackActor.name, Does.StartWith("FallbackPrefab"));
            }
            finally
            {
                Object.DestroyImmediate(exactPrefab);
                Object.DestroyImmediate(wildcardPrefab);
                Object.DestroyImmediate(priorityWildcardPrefab);
                Object.DestroyImmediate(fallbackPrefab);
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldPrunesStaleEntitiesWhenTimeoutExpires()
        {
            GameObject root = new GameObject("FastDIS Stale Timeout Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                world.StaleTimeoutSeconds = 1.0f;

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, 30.0), 1.0f), Is.True);
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));

                Assert.That(world.RemoveExpiredEntities(1.5f), Is.EqualTo(0));
                Assert.That(world.KnownEntityCount, Is.EqualTo(1));

                Assert.That(world.RemoveExpiredEntities(2.5f), Is.EqualTo(1));
                Assert.That(world.KnownEntityCount, Is.EqualTo(0));
                Assert.That(world.BoundActorCount, Is.EqualTo(0));
                Assert.That(world.StaleRemovals, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldAppliesDeadReckoningFromNativeTransform()
        {
            GameObject root = new GameObject("FastDIS Dead Reckoning Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                world.DeadReckoningEnabled = true;
                world.SmoothingDurationSeconds = 0.0f;

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, 30.0), 1.0f), Is.True);
                Assert.That(world.AdvanceSimulation(3.0f), Is.GreaterThanOrEqualTo(1));

                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 }, out Transform actor), Is.True);
                Assert.That(actor.localPosition.x, Is.EqualTo(13.5f).Within(0.01f));
                Assert.That(actor.localPosition.y, Is.EqualTo(38.9f).Within(0.01f));
                Assert.That(actor.localPosition.z, Is.EqualTo(16.2f).Within(0.01f));
                Assert.That(world.DeadReckoningUpdates, Is.GreaterThanOrEqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldSmoothsAuthoritativeCorrectionWhenEnabled()
        {
            GameObject root = new GameObject("FastDIS Smoothing Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                world.DeadReckoningEnabled = false;
                world.SmoothingDurationSeconds = 1.0f;
                world.TeleportDistanceMeters = 1000.0f;

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, 30.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 }, out Transform actor), Is.True);
                actor.localPosition = Vector3.zero;

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 20.0, 40.0, 60.0), 2.0f), Is.True);
                Assert.That(actor.localPosition, Is.EqualTo(Vector3.zero));

                world.AdvanceSimulation(2.5f);
                Assert.That(actor.localPosition.x, Is.GreaterThan(0.0f));
                Assert.That(actor.localPosition.x, Is.LessThan(20.0f));

                world.AdvanceSimulation(3.5f);
                Assert.That(actor.localPosition.x, Is.EqualTo(20.0f).Within(0.01f));
                Assert.That(actor.localPosition.y, Is.EqualTo(60.0f).Within(0.01f));
                Assert.That(actor.localPosition.z, Is.EqualTo(40.0f).Within(0.01f));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldSurfacesFireAndDetonationEvents()
        {
            GameObject root = new GameObject("FastDIS Event Surface Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisFire fire = default;
                FastDisDetonation detonation = default;
                int fireCalls = 0;
                int detonationCalls = 0;
                world.FireReceived += value =>
                {
                    fire = value;
                    fireCalls++;
                };
                world.DetonationReceived += value =>
                {
                    detonation = value;
                    detonationCalls++;
                };

                Assert.That(world.ProcessPacket(CreateFirePdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateDetonationPdu(7)), Is.True);

                Assert.That(fireCalls, Is.EqualTo(1));
                Assert.That(detonationCalls, Is.EqualTo(1));
                Assert.That(world.FireEventsReceived, Is.EqualTo(1));
                Assert.That(world.DetonationEventsReceived, Is.EqualTo(1));
                Assert.That(fire.EventId.EventNumber, Is.EqualTo(0x000C));
                Assert.That(fire.MunitionDescriptor.Rate, Is.EqualTo(600));
                Assert.That(detonation.DetonationResult, Is.EqualTo(17));
                Assert.That(detonation.ExplodingEntityId.Entity, Is.EqualTo(0x0009));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldSurfacesStartResumeAndStopFreezeEvents()
        {
            GameObject root = new GameObject("FastDIS Simulation Management Event Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisStartResume startResume = default;
                FastDisStopFreeze stopFreeze = default;
                int startCalls = 0;
                int stopCalls = 0;
                world.StartResumeReceived += value =>
                {
                    startResume = value;
                    startCalls++;
                };
                world.StopFreezeReceived += value =>
                {
                    stopFreeze = value;
                    stopCalls++;
                };

                Assert.That(world.ProcessPacket(CreateStartResumePdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateStopFreezePdu(7)), Is.True);

                Assert.That(startCalls, Is.EqualTo(1));
                Assert.That(stopCalls, Is.EqualTo(1));
                Assert.That(world.StartResumeEventsReceived, Is.EqualTo(1));
                Assert.That(world.StopFreezeEventsReceived, Is.EqualTo(1));
                Assert.That(startResume.RequestId, Is.EqualTo(0x01020304u));
                Assert.That(startResume.SimulationTime.TimePastHour, Is.EqualTo(654321u));
                Assert.That(stopFreeze.Reason, Is.EqualTo(3));
                Assert.That(stopFreeze.RequestId, Is.EqualTo(0x0F1E2D3Cu));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void EntityPublisherSendsInitialHeartbeatAndThresholdUpdates()
        {
            GameObject receiverRoot = new GameObject("FastDIS Publisher Receiver Test");
            GameObject senderRoot = new GameObject("FastDIS Publisher Sender Test");
            try
            {
                FastDisWorld world = receiverRoot.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver receiver = receiverRoot.AddComponent<FastDisNetworkReceiver>();
                FastDisNetworkSender sender = senderRoot.AddComponent<FastDisNetworkSender>();
                FastDisEntityPublisher publisher = senderRoot.AddComponent<FastDisEntityPublisher>();
                publisher.Sender = sender;
                publisher.EntityId = new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x5555 };
                publisher.HeartbeatSeconds = 1.0f;
                publisher.PositionThresholdMeters = 1.0f;
                publisher.OrientationThresholdDegrees = 5.0f;

                ushort port = ReserveLoopbackPort();
                receiver.ConfigureEndpoint("127.0.0.1", port);
                receiver.StartReceiver();
                sender.ConfigureUnicast("127.0.0.1", port);

                senderRoot.transform.localPosition = new Vector3(12.0f, 56.0f, 34.0f);
                senderRoot.transform.localRotation = Quaternion.identity;

                Assert.That(publisher.Tick(0.0f), Is.True);
                Assert.That(PumpReceiver(receiver), Is.True);
                Assert.That(publisher.TotalPublishes, Is.EqualTo(1));
                Assert.That(publisher.LastPublishReason, Is.EqualTo(FastDisEntityPublisher.PublishReason.Initial));

                Assert.That(publisher.Tick(0.5f), Is.False);

                Assert.That(publisher.Tick(1.1f), Is.True);
                Assert.That(PumpReceiver(receiver), Is.True);
                Assert.That(publisher.HeartbeatPublishes, Is.EqualTo(1));
                Assert.That(publisher.TotalPublishes, Is.EqualTo(2));
                Assert.That(publisher.LastPublishReason, Is.EqualTo(FastDisEntityPublisher.PublishReason.Heartbeat));

                senderRoot.transform.localPosition = new Vector3(15.5f, 56.0f, 34.0f);
                Assert.That(publisher.Tick(1.2f), Is.True);
                Assert.That(PumpReceiver(receiver), Is.True);
                Assert.That(publisher.ThresholdPublishes, Is.EqualTo(1));
                Assert.That(publisher.TotalPublishes, Is.EqualTo(3));
                Assert.That(publisher.LastPublishReason, Is.EqualTo(FastDisEntityPublisher.PublishReason.Threshold));

                Assert.That(receiver.PacketsReceived, Is.EqualTo(3));
                Assert.That(sender.PacketsSent, Is.EqualTo(3));
                Assert.That(world.TryGetEntityTransform(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x5555 }, out FastDisEntityTransform transform), Is.True);
                Assert.That(transform.Location.X, Is.EqualTo(15.5).Within(0.0001));
                Assert.That(transform.Location.Y, Is.EqualTo(34.0).Within(0.0001));
                Assert.That(transform.Location.Z, Is.EqualTo(56.0).Within(0.0001));
            }
            finally
            {
                Object.DestroyImmediate(senderRoot);
                Object.DestroyImmediate(receiverRoot);
            }
        }

        [Test]
        public void WorldAppliesGroundClampPolicy()
        {
            GameObject root = new GameObject("FastDIS Ground Clamp Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                world.GroundClampPolicy = FastDisWorld.GroundClampPolicyKind.ClampToZeroY;

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, -5.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 }, out Transform actor), Is.True);
                Assert.That(actor.localPosition.x, Is.EqualTo(10.0f).Within(0.0001f));
                Assert.That(actor.localPosition.y, Is.EqualTo(0.0f).Within(0.0001f));
                Assert.That(actor.localPosition.z, Is.EqualTo(20.0f).Within(0.0001f));
                Assert.That(world.GroundClampApplications, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldAppliesDistanceCullingPolicy()
        {
            GameObject root = new GameObject("FastDIS Distance Culling Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                world.CullingPolicy = FastDisWorld.CullingPolicyKind.Distance;
                world.CullingDistanceMeters = 25.0f;

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 100.0, 0.0, 0.0), 1.0f), Is.True);
                Assert.That(world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 }, out Transform actor), Is.True);
                Assert.That(actor.gameObject.activeSelf, Is.False);
                Assert.That(world.CullingSkips, Is.EqualTo(1));

                Assert.That(world.ProcessPacket(CreateEntityStatePdu(7, 2, 5.0, 0.0, 0.0), 2.0f), Is.True);
                Assert.That(actor.gameObject.activeSelf, Is.True);
                Assert.That(actor.localPosition.x, Is.EqualTo(5.0f).Within(0.0001f));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldSurfacesDesignatorSignalAndElectronicEmissionsEvents()
        {
            GameObject root = new GameObject("FastDIS Alpha8 Event Surface Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisDesignator designator = default;
                FastDisSignal signal = default;
                FastDisElectronicEmissions emissions = default;
                int designatorCalls = 0;
                int signalCalls = 0;
                int emissionsCalls = 0;
                world.DesignatorReceived += value =>
                {
                    designator = value;
                    designatorCalls++;
                };
                world.SignalReceived += value =>
                {
                    signal = value;
                    signalCalls++;
                };
                world.ElectronicEmissionsReceived += value =>
                {
                    emissions = value;
                    emissionsCalls++;
                };

                Assert.That(world.ProcessPacket(CreateDesignatorPdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateSignalPdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateElectronicEmissionsPdu(7)), Is.True);

                Assert.That(designatorCalls, Is.EqualTo(1));
                Assert.That(signalCalls, Is.EqualTo(1));
                Assert.That(emissionsCalls, Is.EqualTo(1));
                Assert.That(world.DesignatorEventsReceived, Is.EqualTo(1));
                Assert.That(world.SignalEventsReceived, Is.EqualTo(1));
                Assert.That(world.ElectronicEmissionsEventsReceived, Is.EqualTo(1));
                Assert.That(designator.DesignatedEntityId.Entity, Is.EqualTo(0x0006));
                Assert.That(designator.DesignatorPower, Is.EqualTo(12.5f).Within(0.0001f));
                Assert.That(signal.RadioId, Is.EqualTo(0x2222));
                Assert.That(signal.SampleRate, Is.EqualTo(48000u));
                Assert.That(emissions.EventId.EventNumber, Is.EqualTo(0x0006));
                Assert.That(emissions.NumberOfSystems, Is.EqualTo(0x02));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void SenderSupportsMulticastAndBroadcastDestinations()
        {
            GameObject multicastRoot = new GameObject("FastDIS Multicast Send Test");
            GameObject broadcastRoot = new GameObject("FastDIS Broadcast Send Test");
            try
            {
                FastDisWorld multicastWorld = multicastRoot.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver multicastReceiver = multicastRoot.AddComponent<FastDisNetworkReceiver>();
                FastDisNetworkSender multicastSender = multicastRoot.AddComponent<FastDisNetworkSender>();

                ushort multicastPort = ReserveLoopbackPort();
                multicastReceiver.ConfigureMulticast("239.255.42.99", multicastPort, "127.0.0.1", true);
                multicastReceiver.StartReceiver();
                multicastSender.ConfigureMulticast("239.255.42.99", multicastPort, true);

                Assert.That(multicastSender.MulticastEnabled, Is.True);
                Assert.That(multicastSender.BroadcastEnabled, Is.False);
                Assert.That(multicastSender.SendRaw(CreateEntityStatePdu(7, 2, 21.0, 22.0, 23.0)), Is.True);
                Assert.That(PumpReceiver(multicastReceiver), Is.True);
                Assert.That(multicastWorld.KnownEntityCount, Is.EqualTo(1));

                FastDisWorld broadcastWorld = broadcastRoot.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver broadcastReceiver = broadcastRoot.AddComponent<FastDisNetworkReceiver>();
                FastDisNetworkSender broadcastSender = broadcastRoot.AddComponent<FastDisNetworkSender>();

                ushort broadcastPort = ReserveLoopbackPort();
                broadcastReceiver.ConfigureEndpoint("0.0.0.0", broadcastPort);
                broadcastReceiver.StartReceiver();
                broadcastSender.ConfigureBroadcast(broadcastPort);

                Assert.That(broadcastSender.BroadcastEnabled, Is.True);
                Assert.That(broadcastSender.MulticastEnabled, Is.False);
                Assert.That(broadcastSender.SendRaw(CreateEntityStatePdu(7, 2, 31.0, 32.0, 33.0)), Is.True);
                Assert.That(PumpReceiver(broadcastReceiver), Is.True);
                Assert.That(broadcastWorld.KnownEntityCount, Is.EqualTo(1));
                Assert.That(multicastSender.PacketsSent, Is.EqualTo(1));
                Assert.That(broadcastSender.PacketsSent, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(multicastRoot);
                Object.DestroyImmediate(broadcastRoot);
            }
        }

        [Test]
        public void WorldSurfacesBeta1ParserBackedEvents()
        {
            GameObject root = new GameObject("FastDIS Beta1 Event Surface Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisTransmitter transmitter = default;
                FastDisReceiver receiver = default;
                FastDisIff iff = default;
                FastDisAttribute attribute = default;
                FastDisDirectedEnergyFire directedEnergyFire = default;
                FastDisEntityDamageStatus entityDamageStatus = default;
                int transmitterCalls = 0;
                int receiverCalls = 0;
                int iffCalls = 0;
                int attributeCalls = 0;
                int directedEnergyFireCalls = 0;
                int entityDamageStatusCalls = 0;
                world.TransmitterReceived += value => { transmitter = value; transmitterCalls++; };
                world.ReceiverReceived += value => { receiver = value; receiverCalls++; };
                world.IffReceived += value => { iff = value; iffCalls++; };
                world.AttributeReceived += value => { attribute = value; attributeCalls++; };
                world.DirectedEnergyFireReceived += value => { directedEnergyFire = value; directedEnergyFireCalls++; };
                world.EntityDamageStatusReceived += value => { entityDamageStatus = value; entityDamageStatusCalls++; };

                Assert.That(world.ProcessPacket(CreateTransmitterPdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateReceiverPdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateIffPdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateAttributePdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateDirectedEnergyFirePdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateEntityDamageStatusPdu(7)), Is.True);

                Assert.That(transmitterCalls, Is.EqualTo(1));
                Assert.That(receiverCalls, Is.EqualTo(1));
                Assert.That(iffCalls, Is.EqualTo(1));
                Assert.That(attributeCalls, Is.EqualTo(1));
                Assert.That(directedEnergyFireCalls, Is.EqualTo(1));
                Assert.That(entityDamageStatusCalls, Is.EqualTo(1));
                Assert.That(world.TransmitterEventsReceived, Is.EqualTo(1));
                Assert.That(world.ReceiverEventsReceived, Is.EqualTo(1));
                Assert.That(world.IffEventsReceived, Is.EqualTo(1));
                Assert.That(world.AttributeEventsReceived, Is.EqualTo(1));
                Assert.That(world.DirectedEnergyFireEventsReceived, Is.EqualTo(1));
                Assert.That(world.EntityDamageStatusEventsReceived, Is.EqualTo(1));
                Assert.That(transmitter.Frequency, Is.EqualTo(225000u));
                Assert.That(transmitter.VariableTransmitterParameterCount, Is.EqualTo(2));
                Assert.That(receiver.ReceivedPower, Is.EqualTo(12.5f).Within(0.0001f));
                Assert.That(receiver.TransmitterEntityId.Entity, Is.EqualTo(0x0006));
                Assert.That(iff.EventId.EventNumber, Is.EqualTo(0x0006));
                Assert.That(iff.FundamentalParameters.Parameter6, Is.EqualTo(10));
                Assert.That(attribute.MasterAttributeRecordType, Is.EqualTo(0x778899AAu));
                Assert.That(attribute.NumberAttributeRecordSet, Is.EqualTo(1));
                Assert.That(directedEnergyFire.PulseWidth, Is.EqualTo(9012));
                Assert.That(directedEnergyFire.NumberOfDeRecords, Is.EqualTo(1));
                Assert.That(entityDamageStatus.DamagedEntityId.Entity, Is.EqualTo(0x0009));
                Assert.That(entityDamageStatus.NumberOfDamageDescription, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void WorldSurfacesCollisionAndCollisionElasticEvents()
        {
            GameObject root = new GameObject("FastDIS Collision Event Surface Test");
            try
            {
                FastDisWorld world = root.AddComponent<FastDisWorld>();
                FastDisCollision collision = default;
                FastDisCollisionElastic collisionElastic = default;
                int collisionCalls = 0;
                int collisionElasticCalls = 0;
                world.CollisionReceived += value => { collision = value; collisionCalls++; };
                world.CollisionElasticReceived += value => { collisionElastic = value; collisionElasticCalls++; };

                Assert.That(world.ProcessPacket(CreateCollisionPdu(7)), Is.True);
                Assert.That(world.ProcessPacket(CreateCollisionElasticPdu(7)), Is.True);

                Assert.That(collisionCalls, Is.EqualTo(1));
                Assert.That(collisionElasticCalls, Is.EqualTo(1));
                Assert.That(world.CollisionEventsReceived, Is.EqualTo(1));
                Assert.That(world.CollisionElasticEventsReceived, Is.EqualTo(1));
                Assert.That(collision.CollidingEntityId.Entity, Is.EqualTo(0x0006));
                Assert.That(collision.CollisionType, Is.EqualTo(0x07));
                Assert.That(collision.Mass, Is.EqualTo(123.5f).Within(0.0001f));
                Assert.That(collisionElastic.ContactVelocity.Z, Is.EqualTo(6.5f).Within(0.0001f));
                Assert.That(collisionElastic.CollisionResultZz, Is.EqualTo(16.5f).Within(0.0001f));
                Assert.That(collisionElastic.CoefficientOfRestitution, Is.EqualTo(0.75f).Within(0.0001f));
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        private static byte[] BuildReplay(params byte[][] packets)
        {
            List<byte> bytes = new List<byte>();
            for (int i = 0; i < packets.Length; i++)
            {
                byte[] packet = packets[i];
                int length = packet.Length;
                bytes.Add((byte)((length >> 24) & 0xFF));
                bytes.Add((byte)((length >> 16) & 0xFF));
                bytes.Add((byte)((length >> 8) & 0xFF));
                bytes.Add((byte)(length & 0xFF));
                bytes.AddRange(packet);
            }
            return bytes.ToArray();
        }

        private static byte[] BuildHeaderedReplay(params byte[][] packets)
        {
            List<byte> bytes = new List<byte>();
            bytes.AddRange(Encoding.ASCII.GetBytes("FDPKT1"));
            bytes.Add((byte)((packets.Length >> 8) & 0xFF));
            bytes.Add((byte)(packets.Length & 0xFF));
            for (int i = 0; i < packets.Length; i++)
            {
                byte[] packet = packets[i];
                int length = packet.Length;
                bytes.Add((byte)((length >> 24) & 0xFF));
                bytes.Add((byte)((length >> 16) & 0xFF));
                bytes.Add((byte)((length >> 8) & 0xFF));
                bytes.Add((byte)(length & 0xFF));
                bytes.AddRange(packet);
            }
            return bytes.ToArray();
        }

        private static ushort ReserveLoopbackPort()
        {
            using (Socket socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
            {
                socket.Bind(new IPEndPoint(IPAddress.Loopback, 0));
                return (ushort)((IPEndPoint)socket.LocalEndPoint).Port;
            }
        }

        private static bool PumpReceiver(FastDisNetworkReceiver receiver)
        {
            for (int attempt = 0; attempt < 20; attempt++)
            {
                if (receiver.PumpAvailable() > 0)
                {
                    return true;
                }
                Thread.Sleep(10);
            }

            return false;
        }

        private static byte[] CreateEntityStatePdu(byte version, byte forceId, double x, double y, double z)
        {
            return CreateEntityStatePduForEntity(version, forceId, 0x1111, 0x2222, 0x3333, x, y, z);
        }

        private static byte[] CreateEntityStatePduForEntity(byte version, byte forceId, ushort site, ushort application, ushort entity, double x, double y, double z)
        {
            byte[] packet = CreatePdu(version, 1, 144);
            packet[3] = 1;
            int body = 12;
            WriteU16(packet, body + 0, site);
            WriteU16(packet, body + 2, application);
            WriteU16(packet, body + 4, entity);
            packet[body + 6] = forceId;
            packet[body + 8] = 3;
            WriteWorld(packet, body + 36, x, y, z);
            WriteVec3(packet, body + 60, 0.1f, 0.2f, 0.3f);
            WriteU32(packet, body + 72, 0xAABBCCDDu);
            packet[body + 76] = 4;
            for (int i = 0; i < 15; i++)
            {
                packet[body + 77 + i] = (byte)(i + 1);
            }
            WriteVec3(packet, body + 92, 0.5f, 0.6f, 0.7f);
            WriteVec3(packet, body + 104, 1.5f, 1.6f, 1.7f);
            WriteU32(packet, body + 128, 0x01020304u);
            return packet;
        }

        private static byte[] CreateEntityStateUpdatePdu(byte version, double x, double y, double z)
        {
            byte[] packet = CreatePdu(version, 67, 72);
            packet[3] = 1;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            packet[body + 8] = 3;
            WriteVec3(packet, body + 8, 4.0f, 5.0f, 6.0f);
            WriteWorld(packet, body + 20, x, y, z);
            WriteVec3(packet, body + 44, 0.4f, 0.5f, 0.6f);
            WriteU32(packet, body + 56, 0x11223344u);
            return packet;
        }

        private static byte[] CreateRemoveEntityPdu(byte version, ushort receivingSite, ushort receivingApplication, ushort receivingEntity)
        {
            byte[] packet = CreatePdu(version, 12, 28);
            packet[3] = 5;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, receivingSite);
            WriteU16(packet, body + 8, receivingApplication);
            WriteU16(packet, body + 10, receivingEntity);
            WriteU32(packet, body + 12, 0x0BADF00Du);
            return packet;
        }

        private static byte[] CreateFirePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 2, 96);
            packet[3] = 2;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            WriteU16(packet, body + 12, 0x0007);
            WriteU16(packet, body + 14, 0x0008);
            WriteU16(packet, body + 16, 0x0009);
            WriteU16(packet, body + 18, 0x000A);
            WriteU16(packet, body + 20, 0x000B);
            WriteU16(packet, body + 22, 0x000C);
            WriteU32(packet, body + 24, 99u);
            WriteWorld(packet, body + 28, 1000.5, 2000.25, 3000.75);
            packet[body + 52] = 2;
            packet[body + 53] = 1;
            WriteU16(packet, body + 54, 225);
            packet[body + 56] = 4;
            packet[body + 57] = 5;
            packet[body + 58] = 6;
            packet[body + 59] = 7;
            WriteU16(packet, body + 60, 101);
            WriteU16(packet, body + 62, 202);
            WriteU16(packet, body + 64, 3);
            WriteU16(packet, body + 66, 600);
            WriteVec3(packet, body + 68, 1.5f, 2.5f, 3.5f);
            WriteFloat(packet, body + 80, 4444.5f);
            return packet;
        }

        private static byte[] CreateDetonationPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 3, 108);
            packet[3] = 2;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            WriteU16(packet, body + 12, 0x0007);
            WriteU16(packet, body + 14, 0x0008);
            WriteU16(packet, body + 16, 0x0009);
            WriteU16(packet, body + 18, 0x000A);
            WriteU16(packet, body + 20, 0x000B);
            WriteU16(packet, body + 22, 0x000C);
            WriteVec3(packet, body + 24, 11.0f, 22.0f, 33.0f);
            WriteWorld(packet, body + 36, 111.5, 222.25, 333.75);
            packet[body + 60] = 2;
            packet[body + 61] = 1;
            WriteU16(packet, body + 62, 225);
            packet[body + 64] = 4;
            packet[body + 65] = 5;
            packet[body + 66] = 6;
            packet[body + 67] = 7;
            WriteU16(packet, body + 68, 101);
            WriteU16(packet, body + 70, 202);
            WriteU16(packet, body + 72, 3);
            WriteU16(packet, body + 74, 600);
            WriteVec3(packet, body + 76, -4.0f, -5.0f, -6.0f);
            packet[body + 88] = 17;
            packet[body + 89] = 1;
            WriteU16(packet, body + 90, 0);
            for (int i = 0; i < 16; i++)
            {
                packet[body + 92 + i] = (byte)(i + 1);
            }
            return packet;
        }

        private static byte[] CreateStartResumePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 13, 44);
            packet[3] = 5;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            WriteU32(packet, body + 12, 7u);
            WriteU32(packet, body + 16, 123456u);
            WriteU32(packet, body + 20, 9u);
            WriteU32(packet, body + 24, 654321u);
            WriteU32(packet, body + 28, 0x01020304u);
            return packet;
        }

        private static byte[] CreateStopFreezePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 14, 40);
            packet[3] = 5;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            WriteU32(packet, body + 12, 5u);
            WriteU32(packet, body + 16, 7654321u);
            packet[body + 20] = 3;
            packet[body + 21] = 4;
            WriteU16(packet, body + 22, 0xABCD);
            WriteU32(packet, body + 24, 0x0F1E2D3Cu);
            return packet;
        }

        private static byte[] CreateDesignatorPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 24, 88);
            packet[3] = 6;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x1234);
            WriteU16(packet, body + 8, 0x0004);
            WriteU16(packet, body + 10, 0x0005);
            WriteU16(packet, body + 12, 0x0006);
            WriteU16(packet, body + 14, 0x2345);
            WriteFloat(packet, body + 16, 12.5f);
            WriteFloat(packet, body + 20, 1.25f);
            WriteVec3(packet, body + 24, 2.5f, 3.5f, 4.5f);
            WriteWorld(packet, body + 36, 100.0, 200.0, 300.0);
            packet[body + 60] = 4;
            WriteU16(packet, body + 61, 0x3456);
            packet[body + 63] = 0x78;
            WriteVec3(packet, body + 64, 5.5f, 6.5f, 7.5f);
            return packet;
        }

        private static byte[] CreateSignalPdu(byte version)
        {
            ushort length = (ushort)(version >= 7 ? 28 : 36);
            byte[] packet = CreatePdu(version, 26, length);
            packet[3] = 4;
            int body = 12;
            int offset = 0;
            if (version < 7)
            {
                WriteU16(packet, body + 0, 0x0001);
                WriteU16(packet, body + 2, 0x0002);
                WriteU16(packet, body + 4, 0x0003);
                WriteU16(packet, body + 6, 0x1111);
                offset = 8;
            }
            WriteU16(packet, body + offset + 0, 0x2222);
            WriteU16(packet, body + offset + 2, 0x3333);
            WriteU32(packet, body + offset + 4, 48000u);
            WriteU16(packet, body + offset + 8, 4);
            WriteU16(packet, body + offset + 10, 2);
            packet[body + offset + 12] = 0x41;
            packet[body + offset + 13] = 0x42;
            packet[body + offset + 14] = 0x43;
            packet[body + offset + 15] = 0x44;
            return packet;
        }

        private static byte[] CreateElectronicEmissionsPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 23, 34);
            packet[3] = 6;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            packet[body + 12] = 0x07;
            packet[body + 13] = 0x02;
            WriteU16(packet, body + 14, 0x0809);
            packet[body + 16] = 0xE1;
            packet[body + 17] = 0xE2;
            packet[body + 18] = 0xE3;
            packet[body + 19] = 0xE4;
            packet[body + 20] = 0xE5;
            packet[body + 21] = 0xE6;
            return packet;
        }

        private static byte[] CreateTransmitterPdu(byte version)
        {
            ushort length = (ushort)(version >= 7 ? 124 : 103);
            byte[] packet = CreatePdu(version, 25, length);
            packet[3] = 4;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x1212);
            if (version >= 7)
            {
                packet[body + 8] = 1;
                packet[body + 9] = 2;
                WriteU16(packet, body + 10, 840);
                packet[body + 12] = 5;
                packet[body + 13] = 6;
                packet[body + 14] = 7;
                packet[body + 15] = 8;
                WriteU16(packet, body + 18, 2);
            }
            packet[body + 16] = 9;
            packet[body + 17] = 10;
            WriteWorld(packet, body + 20, 10.0, 20.0, 30.0);
            WriteVec3(packet, body + 44, 1.0f, 2.0f, 3.0f);
            WriteU16(packet, body + 56, 0x4444);
            WriteU16(packet, body + 58, 1);
            WriteU32(packet, body + 60, 225000u);
            WriteFloat(packet, body + 64, 50.5f);
            WriteFloat(packet, body + 68, 60.5f);
            WriteU16(packet, body + 72, 1);
            WriteU16(packet, body + 74, 2);
            WriteU16(packet, body + 76, 3);
            WriteU16(packet, body + 78, 4);
            WriteU16(packet, body + 80, 0x5555);
            WriteU16(packet, body + 82, 0x6666);
            packet[body + 84] = 1;
            WriteU16(packet, body + 85, 0x7777);
            packet[body + 87] = 0x88;
            WriteVec3(packet, 100, 9.0f, 10.0f, 11.0f);
            WriteVec3(packet, 112, 12.0f, 13.0f, 14.0f);
            return packet;
        }

        private static byte[] CreateReceiverPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 27, 28);
            packet[3] = 4;
            int body = 12;
            WriteU16(packet, body + 0, 0x0000);
            WriteU16(packet, body + 2, 0x0000);
            WriteU16(packet, body + 4, 0x0000);
            WriteU16(packet, body + 6, 0x1111);
            WriteU16(packet, body + 8, 0x2222);
            WriteU16(packet, body + 10, 0x3333);
            WriteFloat(packet, body + 12, 12.5f);
            WriteU16(packet, body + 16, 0x0004);
            WriteU16(packet, body + 18, 0x0005);
            WriteU16(packet, body + 20, 0x0006);
            WriteU16(packet, body + 22, 0x4444);
            return packet;
        }

        private static byte[] CreateIffPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 28, 56);
            packet[3] = 6;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            WriteVec3(packet, body + 12, 1.0f, 2.0f, 3.0f);
            WriteU16(packet, body + 24, 0x1111);
            WriteU16(packet, body + 26, 0x2222);
            packet[body + 28] = 0x33;
            packet[body + 29] = 0x44;
            WriteU16(packet, body + 30, 0x5555);
            packet[body + 32] = 1;
            packet[body + 33] = 2;
            packet[body + 34] = 3;
            packet[body + 35] = 4;
            WriteU16(packet, body + 36, 5);
            WriteU16(packet, body + 38, 6);
            WriteU16(packet, body + 40, 7);
            WriteU16(packet, body + 42, 8);
            WriteU16(packet, body + 44, 9);
            WriteU16(packet, body + 46, 10);
            return packet;
        }

        private static byte[] CreateAttributePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 72, 36);
            packet[3] = 1;
            int body = 12;
            WriteU16(packet, body + 0, 0x0101);
            WriteU16(packet, body + 2, 0x0202);
            WriteU32(packet, body + 4, 0x11223344u);
            WriteU16(packet, body + 8, 0x5566);
            packet[body + 10] = 67;
            packet[body + 11] = 7;
            WriteU32(packet, body + 12, 0x778899AAu);
            packet[body + 16] = 0x12;
            packet[body + 17] = 0x34;
            WriteU16(packet, body + 18, 1);
            packet[body + 20] = 0x61;
            packet[body + 21] = 0x62;
            packet[body + 22] = 0x63;
            packet[body + 23] = 0x64;
            return packet;
        }

        private static byte[] CreateDirectedEnergyFirePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 68, 94);
            packet[3] = 2;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            packet[body + 12] = 2;
            packet[body + 13] = 1;
            WriteU16(packet, body + 14, 225);
            packet[body + 16] = 4;
            packet[body + 17] = 5;
            packet[body + 18] = 6;
            packet[body + 19] = 7;
            WriteU32(packet, body + 20, 7u);
            WriteU32(packet, body + 24, 123456u);
            WriteFloat(packet, body + 28, 1.25f);
            WriteVec3(packet, body + 32, 2.5f, 3.5f, 4.5f);
            WriteFloat(packet, body + 44, 5.5f);
            WriteFloat(packet, body + 48, 6.5f);
            WriteFloat(packet, body + 52, 7.5f);
            WriteFloat(packet, body + 56, 8.5f);
            WriteU32(packet, body + 60, 9012u);
            WriteU32(packet, body + 64, 0x10203040u);
            packet[body + 68] = 0x11;
            packet[body + 69] = 0x22;
            WriteU32(packet, body + 70, 0x33445566u);
            WriteU16(packet, body + 74, 0x7788);
            WriteU16(packet, body + 76, 1);
            packet[body + 78] = 0x90;
            packet[body + 79] = 0x91;
            packet[body + 80] = 0x92;
            packet[body + 81] = 0x93;
            return packet;
        }

        private static byte[] CreateEntityDamageStatusPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 69, 40);
            packet[3] = 2;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            WriteU16(packet, body + 12, 0x0007);
            WriteU16(packet, body + 14, 0x0008);
            WriteU16(packet, body + 16, 0x0009);
            WriteU16(packet, body + 18, 0x1112);
            WriteU16(packet, body + 20, 0x1314);
            WriteU16(packet, body + 22, 1);
            packet[body + 24] = 0xA1;
            packet[body + 25] = 0xA2;
            packet[body + 26] = 0xA3;
            packet[body + 27] = 0xA4;
            return packet;
        }

        private static byte[] CreateCollisionPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 4, 60);
            packet[3] = 1;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            WriteU16(packet, body + 12, 0x0007);
            WriteU16(packet, body + 14, 0x0008);
            WriteU16(packet, body + 16, 0x0009);
            packet[body + 18] = 0x07;
            packet[body + 19] = 0x08;
            WriteVec3(packet, body + 20, 1.5f, 2.5f, 3.5f);
            WriteFloat(packet, body + 32, 123.5f);
            WriteVec3(packet, body + 36, 4.5f, 5.5f, 6.5f);
            return packet;
        }

        private static byte[] CreateCollisionElasticPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 66, 100);
            packet[3] = 1;
            int body = 12;
            WriteU16(packet, body + 0, 0x0001);
            WriteU16(packet, body + 2, 0x0002);
            WriteU16(packet, body + 4, 0x0003);
            WriteU16(packet, body + 6, 0x0004);
            WriteU16(packet, body + 8, 0x0005);
            WriteU16(packet, body + 10, 0x0006);
            WriteU16(packet, body + 12, 0x0007);
            WriteU16(packet, body + 14, 0x0008);
            WriteU16(packet, body + 16, 0x0009);
            WriteU16(packet, body + 18, 0x0102);
            WriteVec3(packet, body + 20, 4.5f, 5.5f, 6.5f);
            WriteFloat(packet, body + 32, 222.5f);
            WriteVec3(packet, body + 36, 7.5f, 8.5f, 9.5f);
            WriteFloat(packet, body + 48, 11.5f);
            WriteFloat(packet, body + 52, 12.5f);
            WriteFloat(packet, body + 56, 13.5f);
            WriteFloat(packet, body + 60, 14.5f);
            WriteFloat(packet, body + 64, 15.5f);
            WriteFloat(packet, body + 68, 16.5f);
            WriteVec3(packet, body + 72, 0.1f, 0.2f, 0.3f);
            WriteFloat(packet, body + 84, 0.75f);
            return packet;
        }

        private static byte[] CreatePdu(byte version, byte pduType, ushort length)
        {
            byte[] packet = new byte[length];
            packet[0] = version;
            packet[1] = 3;
            packet[2] = pduType;
            WriteU16(packet, 8, length);
            return packet;
        }

        private static void WriteU16(byte[] packet, int offset, int value)
        {
            packet[offset] = (byte)((value >> 8) & 0xFF);
            packet[offset + 1] = (byte)(value & 0xFF);
        }

        private static void WriteU32(byte[] packet, int offset, uint value)
        {
            packet[offset] = (byte)((value >> 24) & 0xFF);
            packet[offset + 1] = (byte)((value >> 16) & 0xFF);
            packet[offset + 2] = (byte)((value >> 8) & 0xFF);
            packet[offset + 3] = (byte)(value & 0xFF);
        }

        private static void WriteFloat(byte[] packet, int offset, float value)
        {
            byte[] bytes = System.BitConverter.GetBytes(value);
            if (System.BitConverter.IsLittleEndian)
            {
                System.Array.Reverse(bytes);
            }
            System.Array.Copy(bytes, 0, packet, offset, 4);
        }

        private static void WriteVec3(byte[] packet, int offset, float x, float y, float z)
        {
            WriteFloat(packet, offset, x);
            WriteFloat(packet, offset + 4, y);
            WriteFloat(packet, offset + 8, z);
        }

        private static void WriteWorld(byte[] packet, int offset, double x, double y, double z)
        {
            WriteDouble(packet, offset, x);
            WriteDouble(packet, offset + 8, y);
            WriteDouble(packet, offset + 16, z);
        }

        private static void WriteDouble(byte[] packet, int offset, double value)
        {
            byte[] bytes = System.BitConverter.GetBytes(value);
            if (System.BitConverter.IsLittleEndian)
            {
                System.Array.Reverse(bytes);
            }
            System.Array.Copy(bytes, 0, packet, offset, 8);
        }

        private static void SetPrivateField(object target, string name, object value)
        {
            FieldInfo field = target.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic);
            Assert.That(field, Is.Not.Null, $"missing field {name}");
            field.SetValue(target, value);
        }
    }
}
