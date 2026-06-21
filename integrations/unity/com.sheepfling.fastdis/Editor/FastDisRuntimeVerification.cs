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
    }
}
