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
            Assert.That(Marshal.SizeOf<FastDisFire>(), Is.EqualTo(104));
            Assert.That(Marshal.SizeOf<FastDisDetonation>(), Is.EqualTo(112));
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
