using System;
using System.IO;
using System.Text;
using FastDIS.Native;
using FastDIS.Scanning;
using FastDIS.Unity;
using UnityEditor;
using UnityEngine;

namespace FastDIS.Editor
{
    public static class FastDisRuntimeVerification
    {
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

            Vector3 unity = FastDisTransformMapper.EnuToUnity(new Vector3(1, 2, 3));
            Check("enu_maps_to_unity_east_up_north", Mathf.Approximately(unity.x, 1) && Mathf.Approximately(unity.y, 3) && Mathf.Approximately(unity.z, 2), ref total, ref failed, checks);

            Quaternion rotation = FastDisTransformMapper.BodyBasisToUnityRotation(Vector3.forward, Vector3.up);
            Check("body_basis_rotation_is_finite", IsFinite(rotation), ref total, ref failed, checks);

            string directory = Path.GetDirectoryName(reportPath);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }
            string status = failed == 0 ? "pass" : "fail";
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
            byte[] marking = Encoding.ASCII.GetBytes("TANK001");
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
