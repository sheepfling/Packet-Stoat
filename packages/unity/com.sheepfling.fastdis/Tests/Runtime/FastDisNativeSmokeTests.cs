using System;
using System.Runtime.InteropServices;
using FastDIS.Native;
using FastDIS.Scanning;
using NUnit.Framework;

namespace FastDIS.Tests
{
    public sealed class FastDisNativeSmokeTests
    {
        [Test]
        public void ScannerAcceptsMinimalHeaderSizedPacket()
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = { 7, 1, 1, 1, 0, 0, 0, 1, 0, 12, 0, 0 };

            Assert.That(scanner.Scan(new[] { packet }).Count, Is.EqualTo(1));
        }

        [Test]
        public void NativeEntityTransformLayoutMatchesCurrentAbi()
        {
            Assert.That(Marshal.SizeOf<FastDisHeader>(), Is.EqualTo(16));
            Assert.That(Marshal.SizeOf<FastDisEntityId>(), Is.EqualTo(6));
            Assert.That(Marshal.SizeOf<FastDisClockTime>(), Is.EqualTo(8));
            Assert.That(Marshal.SizeOf<FastDisEventId>(), Is.EqualTo(6));
            Assert.That(Marshal.SizeOf<FastDisEntityType>(), Is.EqualTo(8));
            Assert.That(Marshal.SizeOf<FastDisBurstDescriptor>(), Is.EqualTo(16));
            Assert.That(Marshal.SizeOf<FastDisWorldCoordinates>(), Is.EqualTo(24));
            Assert.That(Marshal.SizeOf<FastDisEulerAngles>(), Is.EqualTo(12));
            Assert.That(Marshal.SizeOf<FastDisVec3F>(), Is.EqualTo(12));
            Assert.That(Marshal.SizeOf<FastDisEntityTransform>(), Is.EqualTo(120));
            Assert.That(Marshal.SizeOf<FastDisSimulationManagementRequest>(), Is.EqualTo(32));
            Assert.That(Marshal.SizeOf<FastDisStartResume>(), Is.EqualTo(48));
            Assert.That(Marshal.SizeOf<FastDisStopFreeze>(), Is.EqualTo(44));
            Assert.That(Marshal.SizeOf<FastDisAcknowledge>(), Is.EqualTo(36));
            Assert.That(Marshal.SizeOf<FastDisSimulationManagementReliableRequest>(), Is.EqualTo(40));
            Assert.That(Marshal.SizeOf<FastDisStartResumeReliable>(), Is.EqualTo(56));
            Assert.That(Marshal.SizeOf<FastDisStopFreezeReliable>(), Is.EqualTo(44));
            Assert.That(Marshal.SizeOf<FastDisFire>(), Is.EqualTo(104));
            Assert.That(Marshal.SizeOf<FastDisDetonation>(), Is.EqualTo(112));
            Assert.That(Marshal.SizeOf<FastDisOtherPdu>(), Is.EqualTo(40));
            Assert.That(Marshal.SizeOf<FastDisAggregateState>(), Is.EqualTo(144));
            Assert.That(Marshal.SizeOf<FastDisIsGroupOf>(), Is.EqualTo(56));
            Assert.That(Marshal.SizeOf<FastDisTransferControlRequest>(), Is.EqualTo(56));
            Assert.That(Marshal.SizeOf<FastDisTransferOwnership>(), Is.EqualTo(56));
            Assert.That(Marshal.SizeOf<FastDisIsPartOf>(), Is.EqualTo(56));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesEntityStateTransform(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateEntityStatePdu(version, 2);

            Assert.That(scanner.TryParseEntityTransform(packet, out FastDisEntityTransform transform), Is.True);
            Assert.That(transform.EntityId.Site, Is.EqualTo(0x1111));
            Assert.That(transform.EntityId.Application, Is.EqualTo(0x2222));
            Assert.That(transform.EntityId.Entity, Is.EqualTo(0x3333));
            Assert.That(transform.ForceId, Is.EqualTo(2));
            Assert.That(transform.ExerciseId, Is.EqualTo(3));
            Assert.That(transform.Version, Is.EqualTo(version));
            Assert.That(transform.Timestamp, Is.EqualTo(0x01020304u));
            Assert.That(transform.Appearance, Is.EqualTo(0xAABBCCDDu));
            Assert.That(transform.Location.X, Is.EqualTo(10.0).Within(0.0001));
            Assert.That(transform.Location.Y, Is.EqualTo(20.0).Within(0.0001));
            Assert.That(transform.Location.Z, Is.EqualTo(30.0).Within(0.0001));
            Assert.That(transform.Orientation.Phi, Is.EqualTo(0.3f).Within(0.0001f));
            Assert.That(transform.LinearVelocity.X, Is.EqualTo(1.25f).Within(0.0001f));
            Assert.That(transform.DeadReckoningAlgorithm, Is.EqualTo(4));
            Assert.That(transform.DeadReckoningParameters[0], Is.EqualTo(1));
            Assert.That(transform.DeadReckoningLinearAcceleration.X, Is.EqualTo(0.5f).Within(0.0001f));
            Assert.That(transform.DeadReckoningAngularVelocity.Z, Is.EqualTo(1.7f).Within(0.0001f));
            Assert.That(transform.HasField(FastDisNative.FastDisEsFieldForceId), Is.True);
            Assert.That(transform.HasField(FastDisNative.FastDisEsFieldLocation), Is.True);
            Assert.That(transform.HasField(FastDisNative.FastDisEsFieldLinearVelocity), Is.True);
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesEntityStateUpdateTransform(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateEntityStateUpdatePdu(version);

            Assert.That(scanner.TryParseEntityTransform(packet, out FastDisEntityTransform transform), Is.True);
            Assert.That(transform.EntityId.Site, Is.EqualTo(0x1111));
            Assert.That(transform.EntityId.Application, Is.EqualTo(0x2222));
            Assert.That(transform.EntityId.Entity, Is.EqualTo(0x3333));
            Assert.That(transform.ForceId, Is.EqualTo(0));
            Assert.That(transform.ExerciseId, Is.EqualTo(3));
            Assert.That(transform.Version, Is.EqualTo(version));
            Assert.That(transform.Timestamp, Is.EqualTo(0x01020304u));
            Assert.That(transform.Appearance, Is.EqualTo(0x11223344u));
            Assert.That(transform.Location.X, Is.EqualTo(40.0).Within(0.0001));
            Assert.That(transform.Location.Y, Is.EqualTo(50.0).Within(0.0001));
            Assert.That(transform.Location.Z, Is.EqualTo(60.0).Within(0.0001));
            Assert.That(transform.LinearVelocity.Z, Is.EqualTo(6.0f).Within(0.0001f));
            Assert.That(transform.Orientation.Theta, Is.EqualTo(0.5f).Within(0.0001f));
            Assert.That(transform.HasField(FastDisNative.FastDisEsFieldForceId), Is.False);
            Assert.That(transform.HasField(FastDisNative.FastDisEsFieldLocation), Is.True);
            Assert.That(transform.HasField(FastDisNative.FastDisEsFieldLinearVelocity), Is.True);
        }

        [Test]
        public void ScannerEntityTransformBatchKeepsOnlySupportedRows()
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] headerOnly = { 7, 1, 2, 2, 0, 0, 0, 1, 0, 12, 0, 0 };
            var transforms = scanner.ScanEntityTransforms(
                new[]
                {
                    CreateEntityStatePdu(7, 2),
                    headerOnly,
                    CreateEntityStateUpdatePdu(7),
                });

            Assert.That(transforms.Count, Is.EqualTo(2));
            Assert.That(transforms[0].ForceId, Is.EqualTo(2));
            Assert.That(transforms[1].ForceId, Is.EqualTo(0));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesCreateEntity(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateCreateEntityPdu(version);

            Assert.That(scanner.TryParseCreateEntity(packet, out FastDisSimulationManagementRequest request), Is.True);
            Assert.That(request.Header.PduType, Is.EqualTo(11));
            Assert.That(request.Header.ProtocolFamily, Is.EqualTo(5));
            Assert.That(request.Header.Version, Is.EqualTo(version));
            Assert.That(request.OriginatingEntityId.Site, Is.EqualTo(0x1111));
            Assert.That(request.ReceivingEntityId.Entity, Is.EqualTo(0x6666));
            Assert.That(request.RequestId, Is.EqualTo(0xA0B0C0D0u));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesRemoveEntity(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateRemoveEntityPdu(version);

            Assert.That(scanner.TryParseRemoveEntity(packet, out FastDisSimulationManagementRequest request), Is.True);
            Assert.That(request.Header.PduType, Is.EqualTo(12));
            Assert.That(request.Header.ProtocolFamily, Is.EqualTo(5));
            Assert.That(request.Header.Version, Is.EqualTo(version));
            Assert.That(request.OriginatingEntityId.Application, Is.EqualTo(0x2222));
            Assert.That(request.ReceivingEntityId.Site, Is.EqualTo(0x4444));
            Assert.That(request.RequestId, Is.EqualTo(0x0BADF00Du));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesStartResume(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateStartResumePdu(version);

            Assert.That(scanner.TryParseStartResume(packet, out FastDisStartResume request), Is.True);
            Assert.That(request.Header.PduType, Is.EqualTo(13));
            Assert.That(request.Header.Version, Is.EqualTo(version));
            Assert.That(request.RealWorldTime.Hour, Is.EqualTo(7u));
            Assert.That(request.RealWorldTime.TimePastHour, Is.EqualTo(123456u));
            Assert.That(request.SimulationTime.Hour, Is.EqualTo(9u));
            Assert.That(request.SimulationTime.TimePastHour, Is.EqualTo(654321u));
            Assert.That(request.RequestId, Is.EqualTo(0x01020304u));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesStopFreeze(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateStopFreezePdu(version);

            Assert.That(scanner.TryParseStopFreeze(packet, out FastDisStopFreeze request), Is.True);
            Assert.That(request.Header.PduType, Is.EqualTo(14));
            Assert.That(request.Header.Version, Is.EqualTo(version));
            Assert.That(request.RealWorldTime.Hour, Is.EqualTo(5u));
            Assert.That(request.RealWorldTime.TimePastHour, Is.EqualTo(7654321u));
            Assert.That(request.Reason, Is.EqualTo(3));
            Assert.That(request.FrozenBehavior, Is.EqualTo(4));
            Assert.That(request.Padding1, Is.EqualTo(0xABCD));
            Assert.That(request.RequestId, Is.EqualTo(0x0F1E2D3Cu));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesReliableSimulationManagement(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();

            Assert.That(scanner.TryParseAcknowledge(CreateAcknowledgePdu(version), out FastDisAcknowledge acknowledge), Is.True);
            Assert.That(acknowledge.Header.PduType, Is.EqualTo(15));
            Assert.That(acknowledge.Header.ProtocolFamily, Is.EqualTo(5));
            Assert.That(acknowledge.AcknowledgeFlag, Is.EqualTo(0x1234));
            Assert.That(acknowledge.ResponseFlag, Is.EqualTo(0x5678));
            Assert.That(acknowledge.RequestId, Is.EqualTo(0xCAFEBABEu));

            Assert.That(scanner.TryParseCreateEntityReliable(CreateCreateEntityReliablePdu(version), out FastDisSimulationManagementReliableRequest createReliable), Is.True);
            Assert.That(createReliable.Header.PduType, Is.EqualTo(51));
            Assert.That(createReliable.Header.ProtocolFamily, Is.EqualTo(10));
            Assert.That(createReliable.RequiredReliabilityService, Is.EqualTo(7));
            Assert.That(createReliable.Pad1, Is.EqualTo(0x1357));
            Assert.That(createReliable.Pad2, Is.EqualTo(9));
            Assert.That(createReliable.RequestId, Is.EqualTo(0xA0B0C0D0u));

            Assert.That(scanner.TryParseRemoveEntityReliable(CreateRemoveEntityReliablePdu(version), out FastDisSimulationManagementReliableRequest removeReliable), Is.True);
            Assert.That(removeReliable.Header.PduType, Is.EqualTo(52));
            Assert.That(removeReliable.RequiredReliabilityService, Is.EqualTo(8));
            Assert.That(removeReliable.Pad1, Is.EqualTo(0x2468));
            Assert.That(removeReliable.Pad2, Is.EqualTo(10));
            Assert.That(removeReliable.RequestId, Is.EqualTo(0x0BADF00Du));

            Assert.That(scanner.TryParseStartResumeReliable(CreateStartResumeReliablePdu(version), out FastDisStartResumeReliable startReliable), Is.True);
            Assert.That(startReliable.Header.PduType, Is.EqualTo(53));
            Assert.That(startReliable.RealWorldTime.Hour, Is.EqualTo(7u));
            Assert.That(startReliable.SimulationTime.TimePastHour, Is.EqualTo(654321u));
            Assert.That(startReliable.RequiredReliabilityService, Is.EqualTo(11));
            Assert.That(startReliable.Pad1, Is.EqualTo(0xAAAA));
            Assert.That(startReliable.Pad2, Is.EqualTo(12));
            Assert.That(startReliable.RequestId, Is.EqualTo(0x01020304u));

            Assert.That(scanner.TryParseStopFreezeReliable(CreateStopFreezeReliablePdu(version), out FastDisStopFreezeReliable stopReliable), Is.True);
            Assert.That(stopReliable.Header.PduType, Is.EqualTo(54));
            Assert.That(stopReliable.Reason, Is.EqualTo(3));
            Assert.That(stopReliable.FrozenBehavior, Is.EqualTo(4));
            Assert.That(stopReliable.RequiredReliablityService, Is.EqualTo(13));
            Assert.That(stopReliable.Pad1, Is.EqualTo(14));
            Assert.That(stopReliable.RequestId, Is.EqualTo(0x0F1E2D3Cu));

            Assert.That(scanner.TryParseAcknowledgeReliable(CreateAcknowledgeReliablePdu(version), out FastDisAcknowledge acknowledgeReliable), Is.True);
            Assert.That(acknowledgeReliable.Header.PduType, Is.EqualTo(55));
            Assert.That(acknowledgeReliable.Header.ProtocolFamily, Is.EqualTo(10));
            Assert.That(acknowledgeReliable.AcknowledgeFlag, Is.EqualTo(0x9ABC));
            Assert.That(acknowledgeReliable.ResponseFlag, Is.EqualTo(0xDEF0));
            Assert.That(acknowledgeReliable.RequestId, Is.EqualTo(0xFACECAFEu));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesFire(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateFirePdu(version);

            Assert.That(scanner.TryParseFire(packet, out FastDisFire fire), Is.True);
            Assert.That(fire.Header.PduType, Is.EqualTo(2));
            Assert.That(fire.Header.ProtocolFamily, Is.EqualTo(2));
            Assert.That(fire.Header.Version, Is.EqualTo(version));
            Assert.That(fire.FiringEntityId.Entity, Is.EqualTo(0x0003));
            Assert.That(fire.TargetEntityId.Entity, Is.EqualTo(0x0006));
            Assert.That(fire.MunitionEntityId.Entity, Is.EqualTo(0x0009));
            Assert.That(fire.EventId.EventNumber, Is.EqualTo(0x000C));
            Assert.That(fire.FireMissionIndex, Is.EqualTo(99u));
            Assert.That(fire.WorldLocation.X, Is.EqualTo(1000.5).Within(0.0001));
            Assert.That(fire.MunitionDescriptor.Rate, Is.EqualTo(600));
            Assert.That(fire.Velocity.Z, Is.EqualTo(3.5f).Within(0.0001f));
            Assert.That(fire.RangeToTarget, Is.EqualTo(4444.5f).Within(0.0001f));
        }

        [TestCase((byte)6)]
        [TestCase((byte)7)]
        public void ScannerParsesDetonation(byte version)
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = CreateDetonationPdu(version);

            Assert.That(scanner.TryParseDetonation(packet, out FastDisDetonation detonation), Is.True);
            Assert.That(detonation.Header.PduType, Is.EqualTo(3));
            Assert.That(detonation.Header.ProtocolFamily, Is.EqualTo(2));
            Assert.That(detonation.Header.Version, Is.EqualTo(version));
            Assert.That(detonation.ExplodingEntityId.Entity, Is.EqualTo(0x0009));
            Assert.That(detonation.EventId.EventNumber, Is.EqualTo(0x000C));
            Assert.That(detonation.WorldLocation.Z, Is.EqualTo(333.75).Within(0.0001));
            Assert.That(detonation.MunitionDescriptor.Warhead, Is.EqualTo(101));
            Assert.That(detonation.LocationInEntityCoordinates.X, Is.EqualTo(-4.0f).Within(0.0001f));
            Assert.That(detonation.DetonationResult, Is.EqualTo(17));
            Assert.That(detonation.VariableParameterCount, Is.EqualTo(1));
            Assert.That(detonation.Padding1, Is.EqualTo(0));
        }

        [Test]
        public void ScannerParsesOtherAndEntityManagementRows()
        {
            FastDisScanner scanner = new FastDisScanner();

            Assert.That(scanner.TryParseOtherPdu(CreateOtherPdu(6), out FastDisOtherPdu other), Is.True);
            Assert.That(other.Header.Version, Is.EqualTo(6));
            Assert.That(other.Header.ProtocolFamily, Is.EqualTo(0));
            Assert.That(other.OpaquePayloadBytes, Is.EqualTo(new byte[] { 0x4f, 0x54, 0x48, 0x52 }));

            Assert.That(scanner.TryParseAggregateState(CreateAggregateStatePdu(7), out FastDisAggregateState aggregate), Is.True);
            Assert.That(aggregate.Header.Version, Is.EqualTo(7));
            Assert.That(aggregate.AggregateId.Entity, Is.EqualTo(3));
            Assert.That(aggregate.ForceId, Is.EqualTo(4));
            Assert.That(aggregate.AggregateStateValue, Is.EqualTo(5));
            Assert.That(aggregate.AggregateType.Country, Is.EqualTo(840));
            Assert.That(aggregate.Formation, Is.EqualTo(0x11223344u));
            Assert.That(aggregate.AggregateMarkingCharacterSet, Is.EqualTo(1));
            Assert.That(System.Text.Encoding.ASCII.GetString(aggregate.AggregateMarkingBytes).TrimEnd('\0'), Does.StartWith("AGGREGATE-ALPHA"));
            Assert.That(aggregate.Dimensions.Y, Is.EqualTo(2.0f).Within(0.0001f));
            Assert.That(aggregate.Orientation.Theta, Is.EqualTo(0.2f).Within(0.0001f));
            Assert.That(aggregate.CenterOfMass.Z, Is.EqualTo(30.0).Within(0.0001));
            Assert.That(aggregate.Velocity.X, Is.EqualTo(4.0f).Within(0.0001f));
            Assert.That(aggregate.NumberOfDisAggregates, Is.EqualTo(7));
            Assert.That(aggregate.NumberOfDisEntities, Is.EqualTo(8));
            Assert.That(aggregate.NumberOfSilentAggregateTypes, Is.EqualTo(9));
            Assert.That(aggregate.NumberOfSilentEntityTypes, Is.EqualTo(10));
            Assert.That(aggregate.AggregateRecordBytes, Is.EqualTo(new byte[] { 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6 }));

            Assert.That(scanner.TryParseIsGroupOf(CreateIsGroupOfPdu(6), out FastDisIsGroupOf group), Is.True);
            Assert.That(group.Header.Version, Is.EqualTo(6));
            Assert.That(group.GroupEntityId.Entity, Is.EqualTo(3));
            Assert.That(group.GroupedEntityCategory, Is.EqualTo(0x21));
            Assert.That(group.NumberOfGroupedEntities, Is.EqualTo(0x02));
            Assert.That(group.Pad2, Is.EqualTo(0x10203040u));
            Assert.That(group.Latitude, Is.EqualTo(41.25).Within(0.0001));
            Assert.That(group.Longitude, Is.EqualTo(-93.5).Within(0.0001));
            Assert.That(group.GroupedEntityDescriptionBytes, Is.EqualTo(new byte[] { 0xB1, 0xB2, 0xB3, 0xB4 }));

            Assert.That(scanner.TryParseTransferControlRequest(CreateTransferControlRequestPdu(6), out FastDisTransferControlRequest transferControl), Is.True);
            Assert.That(transferControl.Header.Version, Is.EqualTo(6));
            Assert.That(transferControl.OriginatingEntityId.Entity, Is.EqualTo(3));
            Assert.That(transferControl.ReceivingEntityId.Site, Is.EqualTo(4));
            Assert.That(transferControl.RequestId, Is.EqualTo(0x11223344u));
            Assert.That(transferControl.RequiredReliabilityService, Is.EqualTo(0x07));
            Assert.That(transferControl.TransferType, Is.EqualTo(0x08));
            Assert.That(transferControl.TransferEntityId.Entity, Is.EqualTo(9));
            Assert.That(transferControl.NumberOfRecordSets, Is.EqualTo(0x02));
            Assert.That(transferControl.RecordSetBytes, Is.EqualTo(new byte[] { 0xC1, 0xC2, 0xC3, 0xC4 }));

            Assert.That(scanner.TryParseTransferOwnership(CreateTransferOwnershipPdu(7), out FastDisTransferOwnership transferOwnership), Is.True);
            Assert.That(transferOwnership.Header.Version, Is.EqualTo(7));
            Assert.That(transferOwnership.OriginatingEntityId.Site, Is.EqualTo(10));
            Assert.That(transferOwnership.ReceivingEntityId.Entity, Is.EqualTo(15));
            Assert.That(transferOwnership.RequestId, Is.EqualTo(0x55667788u));
            Assert.That(transferOwnership.RequiredReliabilityService, Is.EqualTo(0x09));
            Assert.That(transferOwnership.TransferType, Is.EqualTo(0x0A));
            Assert.That(transferOwnership.TransferEntityId.Application, Is.EqualTo(17));
            Assert.That(transferOwnership.NumberOfRecordSets, Is.EqualTo(0x03));
            Assert.That(transferOwnership.RecordSetBytes, Is.EqualTo(new byte[] { 0xD1, 0xD2, 0xD3, 0xD4 }));

            Assert.That(scanner.TryParseIsPartOf(CreateIsPartOfPdu(7), out FastDisIsPartOf part), Is.True);
            Assert.That(part.Header.Version, Is.EqualTo(7));
            Assert.That(part.OriginatingEntityId.Entity, Is.EqualTo(3));
            Assert.That(part.ReceivingEntityId.Site, Is.EqualTo(4));
            Assert.That(part.RelationshipNature, Is.EqualTo(0x1112));
            Assert.That(part.RelationshipPosition, Is.EqualTo(0x1314));
            Assert.That(part.PartLocation.Y, Is.EqualTo(8.0f).Within(0.0001f));
            Assert.That(part.StationName, Is.EqualTo(0x2122));
            Assert.That(part.StationNumber, Is.EqualTo(0x2324));
            Assert.That(part.PartEntityType.Country, Is.EqualTo(225));
            Assert.That(part.PartEntityType.Extra, Is.EqualTo(7));
        }

        private static byte[] CreateEntityStatePdu(byte version, byte forceId)
        {
            byte[] packet = CreatePdu(version, 1, 144);
            packet[3] = 1;
            int body = 12;

            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
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
            WriteWorld(packet, body + 36, 10.0, 20.0, 30.0);
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
            byte[] marking = System.Text.Encoding.ASCII.GetBytes("TANK001");
            Array.Copy(marking, 0, packet, body + 117, marking.Length);
            WriteU32(packet, body + 128, 0x01020304u);
            return packet;
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
            byte[] packet = CreatePdu(version, 12, 28);
            packet[3] = 5;
            int body = 12;
            WriteU16(packet, body + 0, 0x1111);
            WriteU16(packet, body + 2, 0x2222);
            WriteU16(packet, body + 4, 0x3333);
            WriteU16(packet, body + 6, 0x4444);
            WriteU16(packet, body + 8, 0x5555);
            WriteU16(packet, body + 10, 0x6666);
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

        private static byte[] CreateOtherPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 0, 16);
            packet[3] = 0;
            packet[12] = 0x4f;
            packet[13] = 0x54;
            packet[14] = 0x48;
            packet[15] = 0x52;
            return packet;
        }

        private static byte[] CreateAggregateStatePdu(byte version)
        {
            byte[] packet = CreatePdu(version, 33, 138);
            packet[3] = 7;
            int body = 12;
            WriteU16(packet, body + 0, 1);
            WriteU16(packet, body + 2, 2);
            WriteU16(packet, body + 4, 3);
            packet[body + 6] = 4;
            packet[body + 7] = 5;
            packet[body + 8] = 1;
            packet[body + 9] = 2;
            WriteU16(packet, body + 10, 840);
            packet[body + 12] = 3;
            packet[body + 13] = 4;
            packet[body + 14] = 5;
            packet[body + 15] = 6;
            WriteU32(packet, body + 16, 0x11223344u);
            packet[body + 20] = 1;
            byte[] marking = System.Text.Encoding.ASCII.GetBytes("AGGREGATE-ALPHA");
            Array.Copy(marking, 0, packet, body + 21, marking.Length);
            WriteVec3(packet, body + 52, 1.0f, 2.0f, 3.0f);
            WriteVec3(packet, body + 64, 0.1f, 0.2f, 0.3f);
            WriteWorld(packet, body + 76, 10.0, 20.0, 30.0);
            WriteVec3(packet, body + 100, 4.0f, 5.0f, 6.0f);
            WriteU16(packet, body + 112, 7);
            WriteU16(packet, body + 114, 8);
            WriteU16(packet, body + 116, 9);
            WriteU16(packet, body + 118, 10);
            packet[132] = 0xA1;
            packet[133] = 0xA2;
            packet[134] = 0xA3;
            packet[135] = 0xA4;
            packet[136] = 0xA5;
            packet[137] = 0xA6;
            return packet;
        }

        private static byte[] CreateIsGroupOfPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 34, 44);
            packet[3] = 7;
            int body = 12;
            WriteU16(packet, body + 0, 1);
            WriteU16(packet, body + 2, 2);
            WriteU16(packet, body + 4, 3);
            packet[body + 6] = 0x21;
            packet[body + 7] = 0x02;
            WriteU32(packet, body + 8, 0x10203040u);
            WriteDouble(packet, body + 12, 41.25);
            WriteDouble(packet, body + 20, -93.5);
            packet[40] = 0xB1;
            packet[41] = 0xB2;
            packet[42] = 0xB3;
            packet[43] = 0xB4;
            return packet;
        }

        private static byte[] CreateTransferControlRequestPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 35, 41);
            packet[3] = 7;
            int body = 12;
            WriteU16(packet, body + 0, 1);
            WriteU16(packet, body + 2, 2);
            WriteU16(packet, body + 4, 3);
            WriteU16(packet, body + 6, 4);
            WriteU16(packet, body + 8, 5);
            WriteU16(packet, body + 10, 6);
            WriteU32(packet, body + 12, 0x11223344u);
            packet[body + 16] = 0x07;
            packet[body + 17] = 0x08;
            WriteU16(packet, body + 18, 7);
            WriteU16(packet, body + 20, 8);
            WriteU16(packet, body + 22, 9);
            packet[body + 24] = 0x02;
            packet[37] = 0xC1;
            packet[38] = 0xC2;
            packet[39] = 0xC3;
            packet[40] = 0xC4;
            return packet;
        }

        private static byte[] CreateTransferOwnershipPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 35, 41);
            packet[3] = 7;
            int body = 12;
            WriteU16(packet, body + 0, 10);
            WriteU16(packet, body + 2, 11);
            WriteU16(packet, body + 4, 12);
            WriteU16(packet, body + 6, 13);
            WriteU16(packet, body + 8, 14);
            WriteU16(packet, body + 10, 15);
            WriteU32(packet, body + 12, 0x55667788u);
            packet[body + 16] = 0x09;
            packet[body + 17] = 0x0A;
            WriteU16(packet, body + 18, 16);
            WriteU16(packet, body + 20, 17);
            WriteU16(packet, body + 22, 18);
            packet[body + 24] = 0x03;
            packet[37] = 0xD1;
            packet[38] = 0xD2;
            packet[39] = 0xD3;
            packet[40] = 0xD4;
            return packet;
        }

        private static byte[] CreateIsPartOfPdu(byte version)
        {
            byte[] packet = CreatePdu(version, 36, 52);
            packet[3] = 7;
            int body = 12;
            WriteU16(packet, body + 0, 1);
            WriteU16(packet, body + 2, 2);
            WriteU16(packet, body + 4, 3);
            WriteU16(packet, body + 6, 4);
            WriteU16(packet, body + 8, 5);
            WriteU16(packet, body + 10, 6);
            WriteU16(packet, body + 12, 0x1112);
            WriteU16(packet, body + 14, 0x1314);
            WriteVec3(packet, body + 16, 7.0f, 8.0f, 9.0f);
            WriteU16(packet, body + 28, 0x2122);
            WriteU16(packet, body + 30, 0x2324);
            packet[body + 32] = 2;
            packet[body + 33] = 3;
            WriteU16(packet, body + 34, 225);
            packet[body + 36] = 4;
            packet[body + 37] = 5;
            packet[body + 38] = 6;
            packet[body + 39] = 7;
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
