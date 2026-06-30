using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Threading;
using FastDIS.Native;
using FastDIS.Scanning;
using FastDIS.Unity;
using UnityEditor;
using UnityEngine;

namespace FastDIS.Editor
{
    public static class FastDisRuntimeVerification
    {
        private struct BenchmarkRow
        {
            public string Scenario;
            public int EntityCount;
            public int UpdateHz;
            public ulong PacketsReceived;
            public ulong PacketsParsed;
            public ulong PacketsAccepted;
            public ulong PacketsRejected;
            public ulong Malformed;
            public double MainThreadApplyMs;
            public double PacketsPerSec;
            public long SteadyStateGcBytes;
            public string Notes;
        }

        private struct BenchmarkScenarioSpec
        {
            public string Scenario;
            public int Iterations;
            public int EntityCount;
            public int UpdateHz;
            public string Notes;
        }

        public static void Run()
        {
            string reportPath = ReportPathFromArguments();
            if (string.IsNullOrEmpty(reportPath))
            {
                reportPath = Environment.GetEnvironmentVariable("FASTDIS_UNITY_RUNTIME_REPORT_JSON");
            }
            if (string.IsNullOrEmpty(reportPath))
            {
                reportPath = Path.Combine(Environment.CurrentDirectory, "fastdis_unity_runtime_verification.json");
            }

            int total = 0;
            int failed = 0;
            StringBuilder checks = new StringBuilder();

            Check("native_abi_loads", FastDisNative.TryGetAbiVersion(out uint abiVersion) && abiVersion > 0, ref total, ref failed, checks);

            byte[] packet = { 7, 1, 1, 1, 0, 0, 0, 1, 0, 12, 0, 0 };
            Check("header_view_parses_minimal_packet", FastDisHeaderView.TryParse(packet, out FastDisHeaderView header) && header.Version == 7 && header.Length == 12, ref total, ref failed, checks);

            FastDisScanner scanner = new FastDisScanner();
            Check("scanner_accepts_header_sized_packet", scanner.Scan(new[] { packet }).Count == 1, ref total, ref failed, checks);
            Check("scanner_parses_dis6_entity_state_transform", scanner.TryParseEntityTransform(CreateEntityStatePdu(6, 2), out FastDisEntityTransform dis6EntityState) && dis6EntityState.Version == 6 && dis6EntityState.ForceId == 2 && Math.Abs(dis6EntityState.Location.X - 10.0) < 0.0001, ref total, ref failed, checks);
            Check("scanner_parses_dis6_entity_state_update_transform", scanner.TryParseEntityTransform(CreateEntityStateUpdatePdu(6), out FastDisEntityTransform dis6EntityStateUpdate) && dis6EntityStateUpdate.Version == 6 && dis6EntityStateUpdate.ForceId == 0 && Math.Abs(dis6EntityStateUpdate.Location.X - 40.0) < 0.0001, ref total, ref failed, checks);
            Check("scanner_parses_dis7_entity_state_transform", scanner.TryParseEntityTransform(CreateEntityStatePdu(7, 2), out FastDisEntityTransform dis7EntityState) && dis7EntityState.Version == 7 && dis7EntityState.DeadReckoningAlgorithm == 4 && Math.Abs(dis7EntityState.Location.Y - 20.0) < 0.0001, ref total, ref failed, checks);
            Check("scanner_parses_dis7_entity_state_update_transform", scanner.TryParseEntityTransform(CreateEntityStateUpdatePdu(7), out FastDisEntityTransform dis7EntityStateUpdate) && dis7EntityStateUpdate.Version == 7 && !dis7EntityStateUpdate.HasField(FastDisNative.FastDisEsFieldForceId) && Math.Abs(dis7EntityStateUpdate.LinearVelocity.Z - 6.0f) < 0.0001f, ref total, ref failed, checks);
            Check("scanner_parses_dis6_create_entity", scanner.TryParseCreateEntity(CreateCreateEntityPdu(6), out FastDisSimulationManagementRequest dis6Create) && dis6Create.Header.Version == 6 && dis6Create.RequestId == 0xA0B0C0D0u && dis6Create.ReceivingEntityId.Entity == 0x6666, ref total, ref failed, checks);
            Check("scanner_parses_dis7_create_entity", scanner.TryParseCreateEntity(CreateCreateEntityPdu(7), out FastDisSimulationManagementRequest dis7Create) && dis7Create.Header.Version == 7 && dis7Create.OriginatingEntityId.Site == 0x1111 && dis7Create.Header.ProtocolFamily == 5, ref total, ref failed, checks);
            Check("scanner_parses_dis6_remove_entity", scanner.TryParseRemoveEntity(CreateRemoveEntityPdu(6), out FastDisSimulationManagementRequest dis6Remove) && dis6Remove.Header.Version == 6 && dis6Remove.RequestId == 0x0BADF00Du && dis6Remove.ReceivingEntityId.Site == 0x4444, ref total, ref failed, checks);
            Check("scanner_parses_dis7_remove_entity", scanner.TryParseRemoveEntity(CreateRemoveEntityPdu(7), out FastDisSimulationManagementRequest dis7Remove) && dis7Remove.Header.Version == 7 && dis7Remove.OriginatingEntityId.Application == 0x2222, ref total, ref failed, checks);
            Check("scanner_parses_dis6_start_resume", scanner.TryParseStartResume(CreateStartResumePdu(6), out FastDisStartResume dis6Start) && dis6Start.Header.Version == 6 && dis6Start.RealWorldTime.Hour == 7u && dis6Start.SimulationTime.TimePastHour == 654321u, ref total, ref failed, checks);
            Check("scanner_parses_dis7_start_resume", scanner.TryParseStartResume(CreateStartResumePdu(7), out FastDisStartResume dis7Start) && dis7Start.Header.Version == 7 && dis7Start.RequestId == 0x01020304u, ref total, ref failed, checks);
            Check("scanner_parses_dis6_stop_freeze", scanner.TryParseStopFreeze(CreateStopFreezePdu(6), out FastDisStopFreeze dis6Stop) && dis6Stop.Header.Version == 6 && dis6Stop.Reason == 3 && dis6Stop.Padding1 == 0xABCD, ref total, ref failed, checks);
            Check("scanner_parses_dis7_stop_freeze", scanner.TryParseStopFreeze(CreateStopFreezePdu(7), out FastDisStopFreeze dis7Stop) && dis7Stop.Header.Version == 7 && dis7Stop.RealWorldTime.TimePastHour == 7654321u && dis7Stop.RequestId == 0x0F1E2D3Cu, ref total, ref failed, checks);
            Check("scanner_parses_dis6_acknowledge", scanner.TryParseAcknowledge(CreateAcknowledgePdu(6), out FastDisAcknowledge dis6Ack) && dis6Ack.Header.ProtocolFamily == 5 && dis6Ack.AcknowledgeFlag == 0x1234 && dis6Ack.RequestId == 0xCAFEBABEu, ref total, ref failed, checks);
            Check("scanner_parses_dis7_acknowledge", scanner.TryParseAcknowledge(CreateAcknowledgePdu(7), out FastDisAcknowledge dis7Ack) && dis7Ack.Header.Version == 7 && dis7Ack.ResponseFlag == 0x5678, ref total, ref failed, checks);
            Check("scanner_parses_dis6_create_entity_r", scanner.TryParseCreateEntityReliable(CreateCreateEntityReliablePdu(6), out FastDisSimulationManagementReliableRequest dis6CreateR) && dis6CreateR.Header.ProtocolFamily == 10 && dis6CreateR.RequiredReliabilityService == 7 && dis6CreateR.RequestId == 0xA0B0C0D0u, ref total, ref failed, checks);
            Check("scanner_parses_dis7_remove_entity_r", scanner.TryParseRemoveEntityReliable(CreateRemoveEntityReliablePdu(7), out FastDisSimulationManagementReliableRequest dis7RemoveR) && dis7RemoveR.Header.Version == 7 && dis7RemoveR.Pad2 == 10, ref total, ref failed, checks);
            Check("scanner_parses_dis6_start_resume_r", scanner.TryParseStartResumeReliable(CreateStartResumeReliablePdu(6), out FastDisStartResumeReliable dis6StartR) && dis6StartR.RequiredReliabilityService == 11 && dis6StartR.RequestId == 0x01020304u, ref total, ref failed, checks);
            Check("scanner_parses_dis7_stop_freeze_r", scanner.TryParseStopFreezeReliable(CreateStopFreezeReliablePdu(7), out FastDisStopFreezeReliable dis7StopR) && dis7StopR.Header.Version == 7 && dis7StopR.RequiredReliablityService == 13 && dis7StopR.Pad1 == 14, ref total, ref failed, checks);
            Check("scanner_parses_dis6_acknowledge_r", scanner.TryParseAcknowledgeReliable(CreateAcknowledgeReliablePdu(6), out FastDisAcknowledge dis6AckR) && dis6AckR.Header.ProtocolFamily == 10 && dis6AckR.AcknowledgeFlag == 0x9ABC && dis6AckR.RequestId == 0xFACECAFEu, ref total, ref failed, checks);
            Check("scanner_parses_dis6_fire", scanner.TryParseFire(CreateFirePdu(6), out FastDisFire dis6Fire) && dis6Fire.Header.Version == 6 && dis6Fire.FireMissionIndex == 99u && Math.Abs(dis6Fire.RangeToTarget - 4444.5f) < 0.0001f, ref total, ref failed, checks);
            Check("scanner_parses_dis7_fire", scanner.TryParseFire(CreateFirePdu(7), out FastDisFire dis7Fire) && dis7Fire.Header.Version == 7 && dis7Fire.MunitionDescriptor.Rate == 600 && dis7Fire.EventId.EventNumber == 0x000C, ref total, ref failed, checks);
            Check("scanner_parses_dis6_detonation", scanner.TryParseDetonation(CreateDetonationPdu(6), out FastDisDetonation dis6Detonation) && dis6Detonation.Header.Version == 6 && dis6Detonation.DetonationResult == 17 && dis6Detonation.VariableParameterCount == 1, ref total, ref failed, checks);
            Check("scanner_parses_dis7_detonation", scanner.TryParseDetonation(CreateDetonationPdu(7), out FastDisDetonation dis7Detonation) && dis7Detonation.Header.Version == 7 && Math.Abs(dis7Detonation.WorldLocation.Z - 333.75) < 0.0001 && Math.Abs(dis7Detonation.LocationInEntityCoordinates.X + 4.0f) < 0.0001f, ref total, ref failed, checks);

            Vector3 unity = FastDisTransformMapper.EnuToUnity(new Vector3(1, 2, 3));
            Check("enu_maps_to_unity_east_up_north", Mathf.Approximately(unity.x, 1) && Mathf.Approximately(unity.y, 3) && Mathf.Approximately(unity.z, 2), ref total, ref failed, checks);

            Quaternion rotation = FastDisTransformMapper.BodyBasisToUnityRotation(Vector3.forward, Vector3.up);
            Check("body_basis_rotation_is_finite", IsFinite(rotation), ref total, ref failed, checks);
            Check("native_dead_reckoning_algorithm_known", FastDisNative.DeadReckoningAlgorithmKnown(4), ref total, ref failed, checks);
            Check("native_dead_reckoning_extrapolates_transform", FastDisNative.TryExtrapolateEntityTransformDeadReckoning(dis7EntityState, 2.0, out FastDisEntityTransform deadReckonedTransform) && Math.Abs(deadReckonedTransform.Location.X - 13.5) < 0.01 && Math.Abs(deadReckonedTransform.Location.Y - 16.2) < 0.01 && Math.Abs(deadReckonedTransform.Location.Z - 38.9) < 0.01, ref total, ref failed, checks);

            GameObject runtimeRoot = new GameObject("FastDIS Runtime Verification");
            BenchmarkRow[] benchmarkRows = Array.Empty<BenchmarkRow>();
            try
            {
                FastDisWorld world = runtimeRoot.AddComponent<FastDisWorld>();
                FastDisNetworkReceiver receiver = runtimeRoot.AddComponent<FastDisNetworkReceiver>();
                FastDisNetworkSender sender = runtimeRoot.AddComponent<FastDisNetworkSender>();
                FastDisReplayPlayer replayPlayer = runtimeRoot.AddComponent<FastDisReplayPlayer>();

                byte[] runtimeEntityState = CreateEntityStatePdu(7, 2);
                Check("world_processes_entity_state_packet", world.ProcessPacket(runtimeEntityState) && world.KnownEntityCount == 1 && world.BoundActorCount == 1 && world.PacketsProcessed == 1, ref total, ref failed, checks);

                FastDIS.Unity.FastDisEntityId runtimeEntity = new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x3333 };
                Check("world_exposes_last_entity_transform", world.TryGetEntityTransform(runtimeEntity, out FastDisEntityTransform worldTransform) && Math.Abs(worldTransform.Location.X - 10.0) < 0.0001 && Math.Abs(worldTransform.Location.Y - 20.0) < 0.0001, ref total, ref failed, checks);
                Check("world_auto_spawns_and_positions_actor", world.TryGetBoundActor(runtimeEntity, out Transform actor) && TryGetActorLocalPosition(actor, out Vector3 actorPosition) && Mathf.Approximately(actorPosition.x, 10.0f) && Mathf.Approximately(actorPosition.y, 30.0f) && Mathf.Approximately(actorPosition.z, 20.0f), ref total, ref failed, checks);

                byte[] replayBytes = BuildReplay(CreateEntityStatePdu(7, 2), CreateEntityStateUpdatePdu(7));
                replayPlayer.LoadReplay(replayBytes);
                replayPlayer.Play();
                Check("replay_player_parses_fastdispkt_stream", replayPlayer.PacketCount == 2, ref total, ref failed, checks);
                Check("replay_player_steps_world_state", replayPlayer.Step() >= 1 && world.KnownEntityCount == 1, ref total, ref failed, checks);

                GameObject exactPrefab = new GameObject("ExactPrefab");
                GameObject wildcardPrefab = new GameObject("WildcardPrefab");
                GameObject priorityWildcardPrefab = new GameObject("PriorityWildcardPrefab");
                GameObject defaultPrefab = new GameObject("DefaultPrefab");
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
                SetPrivateField(mapping, "defaultPrefab", defaultPrefab);
                SetPrivateField(world, "entityMapping", mapping);
                world.ClearRuntimeState();
                Check(
                    "world_resolves_exact_wildcard_priority_and_default_prefab_mapping",
                    world.ProcessPacket(CreateEntityStatePdu(7, 2), 1.0f)
                    && world.TryGetBoundActor(runtimeEntity, out Transform mappedActor)
                    && mappedActor.name.StartsWith("ExactPrefab", StringComparison.Ordinal)
                    && world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0x7777, 0x1234, 0x0001, 45.0, 46.0, 47.0), 1.0f)
                    && world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x7777, Application = 0x1234, Entity = 0x0001 }, out Transform wildcardActor)
                    && wildcardActor.name.StartsWith("WildcardPrefab", StringComparison.Ordinal)
                    && world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0x7777, 0x8888, 0x9999, 55.0, 66.0, 77.0), 1.0f)
                    && world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0x7777, Application = 0x8888, Entity = 0x9999 }, out Transform priorityWildcardActor)
                    && priorityWildcardActor.name.StartsWith("PriorityWildcardPrefab", StringComparison.Ordinal)
                    && world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0xAAAA, 0xBBBB, 0xCCCC, 85.0, 86.0, 87.0), 1.0f)
                    && world.TryGetBoundActor(new FastDIS.Unity.FastDisEntityId { Site = 0xAAAA, Application = 0xBBBB, Entity = 0xCCCC }, out Transform fallbackActor)
                    && fallbackActor.name.StartsWith("DefaultPrefab", StringComparison.Ordinal),
                    ref total,
                    ref failed,
                    checks
                );

                world.StaleTimeoutSeconds = 1.0f;
                Check(
                    "world_evicts_stale_entities",
                    world.RemoveExpiredEntities(1.25f) == 0
                    && world.KnownEntityCount == 4
                    && world.RemoveExpiredEntities(2.25f) == 4
                    && world.KnownEntityCount == 0
                    && world.StaleRemovals == 4,
                    ref total,
                    ref failed,
                    checks
                );

                world.ClearRuntimeState();
                world.StaleTimeoutSeconds = 0.0f;
                world.DeadReckoningEnabled = true;
                world.SmoothingDurationSeconds = 0.0f;
                Check(
                    "world_dead_reckons_entity_motion",
                    world.ProcessPacket(CreateEntityStatePdu(7, 2), 1.0f)
                    && world.AdvanceSimulation(3.0f) >= 1
                    && world.TryGetBoundActor(runtimeEntity, out Transform deadReckonedActor)
                    && TryGetActorLocalPosition(deadReckonedActor, out Vector3 deadReckonedPosition)
                    && Math.Abs(deadReckonedPosition.x - 13.5f) < 0.01f
                    && Math.Abs(deadReckonedPosition.y - 38.9f) < 0.01f
                    && Math.Abs(deadReckonedPosition.z - 16.2f) < 0.01f,
                    ref total,
                    ref failed,
                    checks
                );

                world.ClearRuntimeState();
                world.StaleTimeoutSeconds = 0.0f;
                world.DeadReckoningEnabled = false;
                world.SmoothingDurationSeconds = 1.0f;
                world.TeleportDistanceMeters = 1000.0f;
                Check(
                    "world_smooths_authoritative_correction",
                    world.ProcessPacket(CreateEntityStatePdu(7, 2), 1.0f)
                    && world.TryGetBoundActor(runtimeEntity, out Transform smoothingActor)
                    && SetActorLocalPosition(smoothingActor, Vector3.zero)
                    && world.ProcessPacket(CreateEntityStatePduForEntity(7, 2, 0x1111, 0x2222, 0x3333, 20.0, 40.0, 60.0), 2.0f)
                    && TryGetActorLocalPosition(smoothingActor, out Vector3 smoothingStartPosition)
                    && Mathf.Approximately(smoothingStartPosition.x, 0.0f)
                    && world.AdvanceSimulation(2.5f) >= 0
                    && TryGetActorLocalPosition(smoothingActor, out Vector3 smoothingMidPosition)
                    && smoothingMidPosition.x > 0.0f
                    && smoothingMidPosition.x < 20.0f
                    && world.AdvanceSimulation(3.5f) >= 0
                    && TryGetActorLocalPosition(smoothingActor, out Vector3 smoothingEndPosition)
                    && Math.Abs(smoothingEndPosition.x - 20.0f) < 0.01f,
                    ref total,
                    ref failed,
                    checks
                );

                FastDisFire worldFire = default;
                FastDisDetonation worldDetonation = default;
                FastDisStartResume worldStartResume = default;
                FastDisStopFreeze worldStopFreeze = default;
                int worldFireCalls = 0;
                int worldDetonationCalls = 0;
                int worldStartResumeCalls = 0;
                int worldStopFreezeCalls = 0;
                world.FireReceived += value =>
                {
                    worldFire = value;
                    worldFireCalls++;
                };
                world.DetonationReceived += value =>
                {
                    worldDetonation = value;
                    worldDetonationCalls++;
                };
                world.StartResumeReceived += value =>
                {
                    worldStartResume = value;
                    worldStartResumeCalls++;
                };
                world.StopFreezeReceived += value =>
                {
                    worldStopFreeze = value;
                    worldStopFreezeCalls++;
                };
                Check(
                    "world_surfaces_fire_event",
                    world.ProcessPacket(CreateFirePdu(7))
                    && worldFireCalls == 1
                    && world.FireEventsReceived == 1
                    && worldFire.EventId.EventNumber == 0x000C
                    && worldFire.MunitionDescriptor.Rate == 600,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_detonation_event",
                    world.ProcessPacket(CreateDetonationPdu(7))
                    && worldDetonationCalls == 1
                    && world.DetonationEventsReceived == 1
                    && worldDetonation.DetonationResult == 17
                    && worldDetonation.ExplodingEntityId.Entity == 0x0009,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_start_resume_event",
                    world.ProcessPacket(CreateStartResumePdu(7))
                    && worldStartResumeCalls == 1
                    && world.StartResumeEventsReceived == 1
                    && worldStartResume.RequestId == 0x01020304u
                    && worldStartResume.SimulationTime.TimePastHour == 654321u,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_stop_freeze_event",
                    world.ProcessPacket(CreateStopFreezePdu(7))
                    && worldStopFreezeCalls == 1
                    && world.StopFreezeEventsReceived == 1
                    && worldStopFreeze.Reason == 3
                    && worldStopFreeze.RequestId == 0x0F1E2D3Cu,
                    ref total,
                    ref failed,
                    checks
                );
                FastDisDesignator worldDesignator = default;
                FastDisSignal worldSignal = default;
                FastDisElectronicEmissions worldEmissions = default;
                int worldDesignatorCalls = 0;
                int worldSignalCalls = 0;
                int worldEmissionsCalls = 0;
                world.DesignatorReceived += value =>
                {
                    worldDesignator = value;
                    worldDesignatorCalls++;
                };
                world.SignalReceived += value =>
                {
                    worldSignal = value;
                    worldSignalCalls++;
                };
                world.ElectronicEmissionsReceived += value =>
                {
                    worldEmissions = value;
                    worldEmissionsCalls++;
                };
                Check(
                    "world_surfaces_designator_event",
                    world.ProcessPacket(CreateDesignatorPdu(7))
                    && worldDesignatorCalls == 1
                    && world.DesignatorEventsReceived == 1
                    && worldDesignator.DesignatedEntityId.Entity == 0x0006
                    && Math.Abs(worldDesignator.DesignatorPower - 12.5f) < 0.0001f,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_signal_event",
                    world.ProcessPacket(CreateSignalPdu(7))
                    && worldSignalCalls == 1
                    && world.SignalEventsReceived == 1
                    && worldSignal.EncodingScheme == 0x2222
                    && worldSignal.SampleRate == 48000u,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_electronic_emissions_event",
                    world.ProcessPacket(CreateElectronicEmissionsPdu(7))
                    && worldEmissionsCalls == 1
                    && world.ElectronicEmissionsEventsReceived == 1
                    && worldEmissions.EventId.EventNumber == 0x0006
                    && worldEmissions.NumberOfSystems == 0x02,
                    ref total,
                    ref failed,
                    checks
                );
                FastDisTransmitter worldTransmitter = default;
                FastDisReceiver worldReceiver = default;
                FastDisIff worldIff = default;
                FastDisAttribute worldAttribute = default;
                FastDisDirectedEnergyFire worldDirectedEnergyFire = default;
                FastDisEntityDamageStatus worldEntityDamageStatus = default;
                int worldTransmitterCalls = 0;
                int worldReceiverCalls = 0;
                int worldIffCalls = 0;
                int worldAttributeCalls = 0;
                int worldDirectedEnergyFireCalls = 0;
                int worldEntityDamageStatusCalls = 0;
                world.TransmitterReceived += value => { worldTransmitter = value; worldTransmitterCalls++; };
                world.ReceiverReceived += value => { worldReceiver = value; worldReceiverCalls++; };
                world.IffReceived += value => { worldIff = value; worldIffCalls++; };
                world.AttributeReceived += value => { worldAttribute = value; worldAttributeCalls++; };
                world.DirectedEnergyFireReceived += value => { worldDirectedEnergyFire = value; worldDirectedEnergyFireCalls++; };
                world.EntityDamageStatusReceived += value => { worldEntityDamageStatus = value; worldEntityDamageStatusCalls++; };
                Check(
                    "world_surfaces_transmitter_event",
                    world.ProcessPacket(CreateTransmitterPdu(7))
                    && worldTransmitterCalls == 1
                    && world.TransmitterEventsReceived == 1
                    && worldTransmitter.Frequency == 225000u
                    && worldTransmitter.VariableTransmitterParameterCount == 2u,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_receiver_event",
                    world.ProcessPacket(CreateReceiverPdu(7))
                    && worldReceiverCalls == 1
                    && world.ReceiverEventsReceived == 1
                    && Math.Abs(worldReceiver.ReceivedPower - 12.5f) < 0.0001f
                    && worldReceiver.TransmitterEntityId.Entity == 0x0006,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_iff_event",
                    world.ProcessPacket(CreateIffPdu(7))
                    && worldIffCalls == 1
                    && world.IffEventsReceived == 1
                    && worldIff.EventId.EventNumber == 0x0006
                    && worldIff.FundamentalParameters.Parameter6 == 10,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_attribute_event",
                    world.ProcessPacket(CreateAttributePdu(7))
                    && worldAttributeCalls == 1
                    && world.AttributeEventsReceived == 1
                    && worldAttribute.MasterAttributeRecordType == 0x778899AAu
                    && worldAttribute.NumberAttributeRecordSet == 1u,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_directed_energy_fire_event",
                    world.ProcessPacket(CreateDirectedEnergyFirePdu(7))
                    && worldDirectedEnergyFireCalls == 1
                    && world.DirectedEnergyFireEventsReceived == 1
                    && worldDirectedEnergyFire.PulseWidth == 9012
                    && worldDirectedEnergyFire.NumberOfDeRecords == 1u,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_entity_damage_status_event",
                    world.ProcessPacket(CreateEntityDamageStatusPdu(7))
                    && worldEntityDamageStatusCalls == 1
                    && world.EntityDamageStatusEventsReceived == 1
                    && worldEntityDamageStatus.DamagedEntityId.Entity == 0x0009
                    && worldEntityDamageStatus.NumberOfDamageDescription == 1u,
                    ref total,
                    ref failed,
                    checks
                );
                FastDisCollision worldCollision = default;
                FastDisCollisionElastic worldCollisionElastic = default;
                int worldCollisionCalls = 0;
                int worldCollisionElasticCalls = 0;
                world.CollisionReceived += value => { worldCollision = value; worldCollisionCalls++; };
                world.CollisionElasticReceived += value => { worldCollisionElastic = value; worldCollisionElasticCalls++; };
                Check(
                    "world_surfaces_collision_event",
                    world.ProcessPacket(CreateCollisionPdu(7))
                    && worldCollisionCalls == 1
                    && world.CollisionEventsReceived == 1
                    && worldCollision.CollidingEntityId.Entity == 0x0006
                    && Math.Abs(worldCollision.Mass - 123.5f) < 0.0001f,
                    ref total,
                    ref failed,
                    checks
                );
                Check(
                    "world_surfaces_collision_elastic_event",
                    world.ProcessPacket(CreateCollisionElasticPdu(7))
                    && worldCollisionElasticCalls == 1
                    && world.CollisionElasticEventsReceived == 1
                    && Math.Abs(worldCollisionElastic.ContactVelocity.Z - 6.5f) < 0.0001f
                    && Math.Abs(worldCollisionElastic.CoefficientOfRestitution - 0.75f) < 0.0001f,
                    ref total,
                    ref failed,
                    checks
                );

                world.ClearRuntimeState();
                ulong loopbackPacketsBefore = receiver.PacketsReceived;
                Check("receiver_socket_loopback_feeds_world", SendLoopbackPacket(receiver, CreateEntityStatePdu(6, 1)) && receiver.PacketsReceived - loopbackPacketsBefore == 1 && world.KnownEntityCount == 1, ref total, ref failed, checks);
                world.ClearRuntimeState();
                ulong multicastPacketsBefore = receiver.PacketsReceived;
                Check("receiver_multicast_loopback_feeds_world", SendMulticastPacket(receiver, CreateEntityStatePdu(6, 1)) && receiver.MulticastEnabled && receiver.PacketsReceived - multicastPacketsBefore == 1 && world.KnownEntityCount == 1, ref total, ref failed, checks);
                world.ClearRuntimeState();
                Check("sender_raw_unicast_feeds_receiver_world", SendRawPacket(sender, receiver, CreateEntityStatePdu(7, 2)) && sender.PacketsSent == 1 && world.KnownEntityCount == 1, ref total, ref failed, checks);
                world.ClearRuntimeState();
                Check("sender_typed_entity_state_feeds_receiver_world", SendTypedEntityState(sender, receiver) && sender.PacketsSent == 2 && world.TryGetEntityTransform(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x4444 }, out FastDisEntityTransform sentTransform) && Math.Abs(sentTransform.Location.X - 12.0) < 0.0001, ref total, ref failed, checks);
                world.ClearRuntimeState();
                Check("sender_supports_multicast_and_broadcast_destinations", VerifyMulticastAndBroadcastSend(), ref total, ref failed, checks);
                world.ClearRuntimeState();
                Check("publisher_heartbeat_and_threshold_send", VerifyPublisherSendsHeartbeatAndThreshold(world, receiver), ref total, ref failed, checks);
                world.ClearRuntimeState();
                world.StaleTimeoutSeconds = 0.0f;
                world.GroundClampPolicy = FastDisWorld.GroundClampPolicyKind.ClampToZeroY;
                Check(
                    "world_applies_ground_clamp_policy",
                    world.ProcessPacket(CreateEntityStatePdu(7, 2, 10.0, 20.0, -5.0), 1.0f)
                    && world.TryGetBoundActor(runtimeEntity, out Transform clampedActor)
                    && TryGetActorLocalPosition(clampedActor, out Vector3 clampedPosition)
                    && Math.Abs(clampedPosition.y - 0.0f) < 0.0001f
                    && world.GroundClampApplications == 1,
                    ref total,
                    ref failed,
                    checks
                );
                world.ClearRuntimeState();
                world.StaleTimeoutSeconds = 0.0f;
                world.GroundClampPolicy = FastDisWorld.GroundClampPolicyKind.None;
                world.CullingPolicy = FastDisWorld.CullingPolicyKind.Distance;
                world.CullingDistanceMeters = 25.0f;
                world.SmoothingDurationSeconds = 0.0f;
                Check(
                    "world_applies_distance_culling_policy",
                    world.ProcessPacket(CreateEntityStatePdu(7, 2, 100.0, 0.0, 0.0), 1.0f)
                    && world.TryGetBoundActor(runtimeEntity, out Transform culledActor)
                    && !culledActor.gameObject.activeSelf
                    && world.CullingSkips == 1
                    && world.ProcessPacket(CreateEntityStatePdu(7, 2, 5.0, 0.0, 0.0), 2.0f)
                    && culledActor.gameObject.activeSelf
                    && TryGetActorLocalPosition(culledActor, out Vector3 culledPosition)
                    && Math.Abs(culledPosition.x - 5.0f) < 0.0001f,
                    ref total,
                    ref failed,
                    checks
                );
                world.CullingPolicy = FastDisWorld.CullingPolicyKind.None;
                Check("remove_entity_request_clears_known_entity", world.ProcessPacket(CreateRemoveEntityPdu(6, 0x1111, 0x2222, 0x3333)) && world.KnownEntityCount == 0 && world.RemoveRequests == 1, ref total, ref failed, checks);

                benchmarkRows = new[]
                {
                    MeasureCanonicalEntityStateBenchmark(
                        world,
                        receiver,
                        new BenchmarkScenarioSpec
                        {
                            Scenario = "entity_state_1x10hz",
                            Iterations = 24,
                            EntityCount = 1,
                            UpdateHz = 10,
                            Notes = "Measured from the Unity editor-method runtime lane by injecting the canonical twenty-four-packet one-entity Entity State workload through FastDisNetworkReceiver into FastDisWorld on the main thread.",
                        }
                    ),
                    MeasureCanonicalEntityStateBenchmark(
                        world,
                        receiver,
                        new BenchmarkScenarioSpec
                        {
                            Scenario = "entity_state_100x30hz",
                            Iterations = 300,
                            EntityCount = 100,
                            UpdateHz = 30,
                            Notes = "Measured from the Unity editor-method runtime lane by injecting three hundred Entity State updates across one hundred entities through FastDisNetworkReceiver into FastDisWorld on the main thread.",
                        }
                    ),
                };

                UnityEngine.Object.DestroyImmediate(mapping);
                UnityEngine.Object.DestroyImmediate(exactPrefab);
                UnityEngine.Object.DestroyImmediate(wildcardPrefab);
                UnityEngine.Object.DestroyImmediate(priorityWildcardPrefab);
                UnityEngine.Object.DestroyImmediate(defaultPrefab);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(runtimeRoot);
            }

            string directory = Path.GetDirectoryName(reportPath);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }
            string status = failed == 0 ? "pass" : "fail";
            string benchmarkRowsJson = BuildBenchmarkRowsJson(benchmarkRows);
            string json =
                "{\n" +
                "  \"schema\": \"fastdis.unity_editor_method_verification.v1\",\n" +
                $"  \"status\": \"{status}\",\n" +
                $"  \"unity_version\": \"{Escape(Application.unityVersion)}\",\n" +
                $"  \"abi_version\": {abiVersion},\n" +
                $"  \"total\": {total},\n" +
                $"  \"passed\": {total - failed},\n" +
                $"  \"failed\": {failed},\n" +
                "  \"checks\": [\n" +
                checks.ToString() +
                "  ],\n" +
                "  \"benchmark_rows\": [\n" +
                benchmarkRowsJson +
                "  ]\n" +
                "}\n";
            File.WriteAllText(reportPath, json, Encoding.UTF8);
            UnityEngine.Debug.Log($"FastDIS runtime verification report: {reportPath}");
            EditorApplication.Exit(failed == 0 ? 0 : 1);
        }

        private static void Check(string name, bool ok, ref int total, ref int failed, StringBuilder checks)
        {
            if (total > 0)
            {
                checks.Append(",\n");
            }

            total++;
            if (!ok)
            {
                failed++;
            }

            checks.Append("    { \"name\": \"");
            checks.Append(Escape(name));
            checks.Append("\", \"status\": \"");
            checks.Append(ok ? "pass" : "fail");
            checks.Append("\" }");
        }

        private static bool IsFinite(Quaternion value)
        {
            return IsFinite(value.x) && IsFinite(value.y) && IsFinite(value.z) && IsFinite(value.w);
        }

        private static bool IsFinite(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value);
        }

        private static string ReportPathFromArguments()
        {
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "-fastdisReport")
                {
                    return args[i + 1];
                }
            }

            return null;
        }

        private static string Escape(string value)
        {
            return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        private static string BuildBenchmarkRowsJson(BenchmarkRow[] rows)
        {
            if (rows == null || rows.Length == 0)
            {
                return string.Empty;
            }
            StringBuilder builder = new StringBuilder();
            bool first = true;
            foreach (BenchmarkRow row in rows)
            {
                if (string.IsNullOrEmpty(row.Scenario))
                {
                    continue;
                }
                if (!first)
                {
                    builder.Append(",\n");
                }
                builder.Append(
                    "    {\n" +
                    $"      \"scenario\": \"{Escape(row.Scenario)}\",\n" +
                    $"      \"entity_count\": {row.EntityCount},\n" +
                    $"      \"update_hz\": {row.UpdateHz},\n" +
                    $"      \"packets_received\": {row.PacketsReceived},\n" +
                    $"      \"packets_parsed\": {row.PacketsParsed},\n" +
                    $"      \"packets_accepted\": {row.PacketsAccepted},\n" +
                    $"      \"packets_rejected\": {row.PacketsRejected},\n" +
                    $"      \"malformed\": {row.Malformed},\n" +
                    $"      \"main_thread_apply_ms\": {row.MainThreadApplyMs.ToString(System.Globalization.CultureInfo.InvariantCulture)},\n" +
                    $"      \"packets_per_sec\": {row.PacketsPerSec.ToString(System.Globalization.CultureInfo.InvariantCulture)},\n" +
                    $"      \"steady_state_gc_bytes\": {row.SteadyStateGcBytes},\n" +
                    $"      \"notes\": \"{Escape(row.Notes ?? string.Empty)}\"\n" +
                    "    }"
                );
                first = false;
            }
            if (!first)
            {
                builder.Append("\n");
            }
            return builder.ToString();
        }

        private static BenchmarkRow MeasureCanonicalEntityStateBenchmark(FastDisWorld world, FastDisNetworkReceiver receiver, BenchmarkScenarioSpec spec)
        {
            world.ClearRuntimeState();

            ulong receivedBefore = receiver.PacketsReceived;
            ulong processedBefore = world.PacketsProcessed;
            ulong malformedBefore = world.MalformedPackets;
            long gcBefore = GC.GetTotalMemory(true);
            Stopwatch stopwatch = Stopwatch.StartNew();
            int entityCount = Math.Max(spec.EntityCount, 1);
            for (int i = 0; i < spec.Iterations; i++)
            {
                ushort entity = (ushort)(0x3333 + (i % entityCount));
                double step = Math.Floor((double)i / entityCount);
                double x = 10.0 + step;
                double y = 20.0 + (i % entityCount);
                if (!receiver.InjectPacket(CreateEntityStatePduForEntity(7, 2, 0x1111, 0x2222, entity, x, y, 30.0)))
                {
                    break;
                }
            }
            stopwatch.Stop();
            long gcAfter = GC.GetTotalMemory(true);

            ulong packetsReceived = receiver.PacketsReceived - receivedBefore;
            ulong packetsAccepted = world.PacketsProcessed - processedBefore;
            ulong malformed = world.MalformedPackets - malformedBefore;
            ulong packetsRejected = packetsReceived >= packetsAccepted ? packetsReceived - packetsAccepted : 0;
            double elapsedMs = Math.Max(stopwatch.Elapsed.TotalMilliseconds, 0.0001);
            long gcDelta = Math.Max(0L, gcAfter - gcBefore);

            return new BenchmarkRow
            {
                Scenario = spec.Scenario,
                EntityCount = spec.EntityCount,
                UpdateHz = spec.UpdateHz,
                PacketsReceived = packetsReceived,
                PacketsParsed = packetsAccepted,
                PacketsAccepted = packetsAccepted,
                PacketsRejected = packetsRejected,
                Malformed = malformed,
                MainThreadApplyMs = packetsAccepted > 0 ? elapsedMs / packetsAccepted : 0.0,
                PacketsPerSec = packetsAccepted > 0 ? (packetsAccepted * 1000.0) / elapsedMs : 0.0,
                SteadyStateGcBytes = packetsAccepted > 0 ? gcDelta / (long)packetsAccepted : gcDelta,
                Notes = spec.Notes,
            };
        }

        private static void SetPrivateField(object target, string name, object value)
        {
            FieldInfo field = target.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic);
            if (field == null)
            {
                throw new InvalidOperationException($"missing field {name} on {target.GetType().FullName}");
            }
            field.SetValue(target, value);
        }

        private static bool SetActorLocalPosition(Transform actor, Vector3 position)
        {
            actor.localPosition = position;
            return true;
        }

        private static bool TryGetActorLocalPosition(Transform actor, out Vector3 position)
        {
            if (actor == null)
            {
                position = Vector3.zero;
                return false;
            }

            position = actor.localPosition;
            return true;
        }

        private static byte[] CreateEntityStatePdu(byte version, byte forceId)
        {
            return CreateEntityStatePduForEntity(version, forceId, 0x1111, 0x2222, 0x3333, 10.0, 20.0, 30.0);
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
            packet[body + 7] = 0;

            packet[body + 8] = 1;
            packet[body + 9] = 2;
            WriteU16(packet, body + 10, 840);
            packet[body + 12] = 3;
            packet[body + 13] = 4;
            packet[body + 14] = 5;
            packet[body + 15] = 6;

            packet[body + 16] = 9;
            packet[body + 17] = 8;
            WriteU16(packet, body + 18, 124);
            packet[body + 20] = 7;
            packet[body + 21] = 6;
            packet[body + 22] = 5;
            packet[body + 23] = 4;

            WriteVec3(packet, body + 24, 1.25f, -2.5f, 3.75f);
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
            packet[body + 116] = 1;
            byte[] marking = Encoding.ASCII.GetBytes("TANK001");
            Array.Copy(marking, 0, packet, body + 117, marking.Length);
            WriteU32(packet, body + 128, 0x01020304u);
            return packet;
        }

        private static bool SendLoopbackPacket(FastDisNetworkReceiver receiver, byte[] packet)
        {
            ushort loopbackPort = ReserveLoopbackPort();
            receiver.ConfigureEndpoint("127.0.0.1", loopbackPort);
            receiver.StartReceiver();
            try
            {
                using (UdpClient sender = new UdpClient())
                {
                    sender.Send(packet, packet.Length, new IPEndPoint(IPAddress.Loopback, loopbackPort));
                }

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
            finally
            {
                receiver.StopReceiver();
            }
        }

        private static bool SendMulticastPacket(FastDisNetworkReceiver receiver, byte[] packet)
        {
            ushort loopbackPort = ReserveLoopbackPort();
            receiver.ConfigureMulticast("239.255.42.99", loopbackPort, "127.0.0.1", true);
            receiver.StartReceiver();
            try
            {
                using (UdpClient sender = new UdpClient(AddressFamily.InterNetwork))
                {
                    sender.MulticastLoopback = true;
                    sender.Client.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.MulticastInterface, IPAddress.Loopback.GetAddressBytes());
                    sender.Send(packet, packet.Length, new IPEndPoint(IPAddress.Parse("239.255.42.99"), loopbackPort));
                }

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
            finally
            {
                receiver.StopReceiver();
            }
        }

        private static bool SendRawPacket(FastDisNetworkSender sender, FastDisNetworkReceiver receiver, byte[] packet)
        {
            ushort loopbackPort = ReserveLoopbackPort();
            receiver.ConfigureEndpoint("127.0.0.1", loopbackPort);
            receiver.StartReceiver();
            sender.ConfigureUnicast("127.0.0.1", loopbackPort);
            try
            {
                if (!sender.SendRaw(packet))
                {
                    return false;
                }

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
            finally
            {
                receiver.StopReceiver();
                sender.StopSender();
            }
        }

        private static bool SendTypedEntityState(FastDisNetworkSender sender, FastDisNetworkReceiver receiver)
        {
            ushort loopbackPort = ReserveLoopbackPort();
            receiver.ConfigureEndpoint("127.0.0.1", loopbackPort);
            receiver.StartReceiver();
            sender.ConfigureUnicast("127.0.0.1", loopbackPort);
            try
            {
                if (!sender.SendEntityState(
                        new FastDisNetworkSender.EntityStateSpec
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
                        }))
                {
                    return false;
                }

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
            finally
            {
                receiver.StopReceiver();
                sender.StopSender();
            }
        }

        private static bool VerifyPublisherSendsHeartbeatAndThreshold(FastDisWorld world, FastDisNetworkReceiver receiver)
        {
            GameObject publisherRoot = new GameObject("FastDIS Publisher Verification");
            try
            {
                FastDisNetworkSender sender = publisherRoot.AddComponent<FastDisNetworkSender>();
                FastDisEntityPublisher publisher = publisherRoot.AddComponent<FastDisEntityPublisher>();
                publisher.Sender = sender;
                publisher.EntityId = new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x5555 };
                publisher.HeartbeatSeconds = 1.0f;
                publisher.PositionThresholdMeters = 1.0f;
                publisher.OrientationThresholdDegrees = 5.0f;

                ushort loopbackPort = ReserveLoopbackPort();
                receiver.ConfigureEndpoint("127.0.0.1", loopbackPort);
                receiver.StartReceiver();
                sender.ConfigureUnicast("127.0.0.1", loopbackPort);
                publisherRoot.transform.localPosition = new Vector3(12.0f, 56.0f, 34.0f);
                ulong packetsBefore = receiver.PacketsReceived;

                if (!publisher.Tick(0.0f) || !PumpReceiver(receiver))
                {
                    return false;
                }
                if (!publisher.Tick(1.1f) || !PumpReceiver(receiver))
                {
                    return false;
                }

                publisherRoot.transform.localPosition = new Vector3(15.5f, 56.0f, 34.0f);
                if (!publisher.Tick(1.2f) || !PumpReceiver(receiver))
                {
                    return false;
                }

                return publisher.TotalPublishes == 3
                    && publisher.HeartbeatPublishes == 1
                    && publisher.ThresholdPublishes == 1
                    && sender.PacketsSent == 3
                    && receiver.PacketsReceived - packetsBefore == 3
                    && world.TryGetEntityTransform(new FastDIS.Unity.FastDisEntityId { Site = 0x1111, Application = 0x2222, Entity = 0x5555 }, out FastDisEntityTransform transform)
                    && Math.Abs(transform.Location.X - 15.5) < 0.0001
                    && Math.Abs(transform.Location.Y - 34.0) < 0.0001
                    && Math.Abs(transform.Location.Z - 56.0) < 0.0001;
            }
            finally
            {
                receiver.StopReceiver();
                UnityEngine.Object.DestroyImmediate(publisherRoot);
            }
        }

        private static bool VerifyMulticastAndBroadcastSend()
        {
            GameObject multicastRoot = new GameObject("FastDIS Multicast Send Verification");
            GameObject broadcastRoot = new GameObject("FastDIS Broadcast Send Verification");
            try
            {
                FastDisNetworkSender multicastSender = multicastRoot.AddComponent<FastDisNetworkSender>();

                ushort multicastPort = ReserveLoopbackPort();
                multicastSender.ConfigureMulticast("239.255.42.99", multicastPort, true);
                bool multicastOk = multicastSender.MulticastEnabled
                    && !multicastSender.BroadcastEnabled
                    && multicastSender.SendRaw(CreateEntityStatePdu(7, 2, 21.0, 22.0, 23.0))
                    && multicastSender.PacketsSent == 1;

                FastDisNetworkSender broadcastSender = broadcastRoot.AddComponent<FastDisNetworkSender>();

                ushort broadcastPort = ReserveLoopbackPort();
                broadcastSender.ConfigureBroadcast(broadcastPort);
                bool broadcastOk = broadcastSender.BroadcastEnabled
                    && !broadcastSender.MulticastEnabled
                    && broadcastSender.SendRaw(CreateEntityStatePdu(7, 2, 31.0, 32.0, 33.0))
                    && broadcastSender.PacketsSent == 1;

                return multicastOk && broadcastOk && multicastSender.PacketsSent == 1;
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(multicastRoot);
                UnityEngine.Object.DestroyImmediate(broadcastRoot);
            }
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

        private static byte[] CreateEntityStateUpdatePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 67, 72);
            packet[3] = 1;
            int body = 12;

            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0);
            WriteVec3(packet, body + 8, 4.0f, 5.0f, 6.0f);
            WriteWorld(packet, body + 20, 40.0, 50.0, 60.0);
            WriteVec3(packet, body + 44, 0.4f, 0.5f, 0.6f);
            WriteU32(packet, body + 56, 0x11223344u);
            return packet;
        }

        private static byte[] CreateCreateEntityPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 11, 28);
            packet[3] = 5;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            WriteU32(packet, body + 12, 0xA0B0C0D0u);
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

        private static byte[] BuildReplay(params byte[][] packets)
        {
            using MemoryStream stream = new MemoryStream();
            for (int i = 0; i < packets.Length; i++)
            {
                byte[] packet = packets[i];
                stream.WriteByte((byte)((packet.Length >> 24) & 0xFF));
                stream.WriteByte((byte)((packet.Length >> 16) & 0xFF));
                stream.WriteByte((byte)((packet.Length >> 8) & 0xFF));
                stream.WriteByte((byte)(packet.Length & 0xFF));
                stream.Write(packet, 0, packet.Length);
            }
            return stream.ToArray();
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

        private static byte[] CreateRemoveEntityPdu(byte version)
        {
            return CreateRemoveEntityPdu(version, 0x4444, 0x5555, 0x6666);
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
            ushort length = (ushort)(version >= 7 ? 28 : 40);
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
            byte[] packet = CreatePdu(version, 27, (ushort)(version >= 7 ? 28 : 36));
            packet[3] = 4;
            int body = 12;
            int offset = 0;
            if (version < 7)
            {
                WriteU16(packet, body + 0, 0x0000);
                WriteU16(packet, body + 2, 0x0000);
                WriteU16(packet, body + 4, 0x0000);
                WriteU16(packet, body + 6, 0x1111);
                offset = 8;
            }
            WriteU16(packet, body + offset + 0, 0x2222);
            WriteU16(packet, body + offset + 2, 0x3333);
            WriteFloat(packet, body + offset + 4, 12.5f);
            WriteU16(packet, body + offset + 8, 0x0004);
            WriteU16(packet, body + offset + 10, 0x0005);
            WriteU16(packet, body + offset + 12, 0x0006);
            WriteU16(packet, body + offset + 14, 0x4444);
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

        private static byte[] CreateAcknowledgePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 15, 30);
            packet[3] = 5;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            WriteU16(packet, body + 12, 0x1234);
            WriteU16(packet, body + 14, 0x5678);
            WriteU32(packet, body + 16, 0xCAFEBABEu);
            return packet;
        }

        private static byte[] CreateCreateEntityReliablePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 51, 32);
            packet[3] = 10;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            packet[body + 12] = 7;
            WriteU16(packet, body + 13, 0x1357);
            packet[body + 15] = 9;
            WriteU32(packet, body + 16, 0xA0B0C0D0u);
            return packet;
        }

        private static byte[] CreateRemoveEntityReliablePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 52, 32);
            packet[3] = 10;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            packet[body + 12] = 8;
            WriteU16(packet, body + 13, 0x2468);
            packet[body + 15] = 10;
            WriteU32(packet, body + 16, 0x0BADF00Du);
            return packet;
        }

        private static byte[] CreateStartResumeReliablePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 53, 48);
            packet[3] = 10;
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
            packet[body + 28] = 11;
            WriteU16(packet, body + 29, 0xAAAA);
            packet[body + 31] = 12;
            WriteU32(packet, body + 32, 0x01020304u);
            return packet;
        }

        private static byte[] CreateStopFreezeReliablePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 54, 36);
            packet[3] = 10;
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
            packet[body + 22] = 13;
            packet[body + 23] = 14;
            WriteU32(packet, body + 24, 0x0F1E2D3Cu);
            return packet;
        }

        private static byte[] CreateAcknowledgeReliablePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 55, 30);
            packet[3] = 10;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
            WriteU16(packet, body + 12, 0x9ABC);
            WriteU16(packet, body + 14, 0xDEF0);
            WriteU32(packet, body + 16, 0xFACECAFEu);
            return packet;
        }

        private static byte[] CreatePdu(byte version, byte pduType, ushort length)
        {
            byte[] packet = new byte[160];
            packet[0] = version;
            packet[1] = 3;
            packet[2] = pduType;
            packet[3] = 1;
            packet[4] = 0x01;
            packet[5] = 0x02;
            packet[6] = 0x03;
            packet[7] = 0x04;
            WriteU16(packet, 8, length);
            if (version >= 7)
            {
                packet[10] = 0x80;
                packet[11] = 0x00;
            }
            else
            {
                packet[10] = 0x12;
                packet[11] = 0x34;
            }
            return packet;
        }

        private static void WriteU16(byte[] packet, int offset, ushort value)
        {
            packet[offset + 0] = (byte)((value >> 8) & 0xff);
            packet[offset + 1] = (byte)(value & 0xff);
        }

        private static void WriteU32(byte[] packet, int offset, uint value)
        {
            packet[offset + 0] = (byte)((value >> 24) & 0xff);
            packet[offset + 1] = (byte)((value >> 16) & 0xff);
            packet[offset + 2] = (byte)((value >> 8) & 0xff);
            packet[offset + 3] = (byte)(value & 0xff);
        }

        private static void WriteU64(byte[] packet, int offset, ulong value)
        {
            packet[offset + 0] = (byte)((value >> 56) & 0xff);
            packet[offset + 1] = (byte)((value >> 48) & 0xff);
            packet[offset + 2] = (byte)((value >> 40) & 0xff);
            packet[offset + 3] = (byte)((value >> 32) & 0xff);
            packet[offset + 4] = (byte)((value >> 24) & 0xff);
            packet[offset + 5] = (byte)((value >> 16) & 0xff);
            packet[offset + 6] = (byte)((value >> 8) & 0xff);
            packet[offset + 7] = (byte)(value & 0xff);
        }

        private static void WriteFloat(byte[] packet, int offset, float value)
        {
            WriteU32(packet, offset, (uint)BitConverter.SingleToInt32Bits(value));
        }

        private static void WriteDouble(byte[] packet, int offset, double value)
        {
            WriteU64(packet, offset, (ulong)BitConverter.DoubleToInt64Bits(value));
        }

        private static void WriteVec3(byte[] packet, int offset, float x, float y, float z)
        {
            WriteFloat(packet, offset + 0, x);
            WriteFloat(packet, offset + 4, y);
            WriteFloat(packet, offset + 8, z);
        }

        private static void WriteWorld(byte[] packet, int offset, double x, double y, double z)
        {
            WriteDouble(packet, offset + 0, x);
            WriteDouble(packet, offset + 8, y);
            WriteDouble(packet, offset + 16, z);
        }
    }
}
