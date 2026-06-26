using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class FastDisOrientationVerificationRunner
{
    public static void Run()
    {
        string reportPath = ReportPathFromArguments();
        if (string.IsNullOrEmpty(reportPath))
        {
            reportPath = Path.Combine(Environment.CurrentDirectory, "fastdis_unity_orientation_verification.json");
        }

        EditorSceneManager.OpenScene("Assets/Scenes/OrientationVerification.unity", OpenSceneMode.Single);
        FastDisOrientationVerifier verifier = UnityEngine.Object.FindAnyObjectByType<FastDisOrientationVerifier>();

        int total = 0;
        int failed = 1;
        string detail = "FastDisOrientationVerifier component was not found in the scene.";
        if (verifier != null)
        {
            FastDisOrientationVerifier.VerificationSummary summary = verifier.RunVerificationNow();
            total = summary.Total;
            failed = summary.Failed;
            detail = summary.Failed == 0
                ? $"passed {summary.Total} orientation checks"
                : $"failed {summary.Failed} of {summary.Total} orientation checks";
        }

        string directory = Path.GetDirectoryName(reportPath);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        string status = failed == 0 ? "pass" : "fail";
        string json =
            "{\n" +
            "  \"schema\": \"fastdis.unity_orientation_scene_verification.v1\",\n" +
            $"  \"status\": \"{status}\",\n" +
            $"  \"unity_version\": \"{Escape(Application.unityVersion)}\",\n" +
            "  \"scene\": \"Assets/Scenes/OrientationVerification.unity\",\n" +
            $"  \"total\": {total},\n" +
            $"  \"failed\": {failed},\n" +
            $"  \"detail\": \"{Escape(detail)}\"\n" +
            "}\n";
        File.WriteAllText(reportPath, json, Encoding.UTF8);
        Debug.Log($"FastDIS orientation verification report: {reportPath}");
        EditorApplication.Exit(failed == 0 ? 0 : 1);
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
