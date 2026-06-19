using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;

public sealed class FastDisOrientationVerifier : MonoBehaviour
{
    [SerializeField] private string selectedCaseName = "level_north";
    [SerializeField] private bool runAllCasesOnStart = true;
    [SerializeField] private float maxAxisAngleDegrees = 0.01f;
    [SerializeField] private float axisLength = 4.0f;

    private OrientationFixtureCase activeCase;
    private Quaternion activeRotation = Quaternion.identity;

    private void Start()
    {
        OrientationFixtureRoot fixture = LoadFixture();
        if (fixture == null || fixture.cases == null || fixture.cases.Count == 0)
        {
            Debug.LogError("FastDIS Unity verification could not load orientation_engine_cases.json");
            return;
        }

        if (runAllCasesOnStart)
        {
            RunAllCases(fixture);
        }

        activeCase = fixture.FindCase(selectedCaseName) ?? fixture.cases[0];
        ApplyCaseToTransform(activeCase, transform);
        activeRotation = transform.rotation;
    }

    private void OnDrawGizmos()
    {
        if (activeCase == null || activeCase.expected == null)
        {
            return;
        }

        DrawAxis(transform.position, activeRotation * Vector3.forward, Color.red, axisLength);
        DrawAxis(transform.position, activeRotation * Vector3.right, Color.green, axisLength);
        DrawAxis(transform.position, activeRotation * Vector3.up, Color.blue, axisLength);

        DrawAxis(transform.position, activeCase.expected.AsUnityForward(), Color.white, axisLength * 0.8f);
        DrawAxis(transform.position, activeCase.expected.AsUnityRight(), Color.yellow, axisLength * 0.8f);
        DrawAxis(transform.position, activeCase.expected.AsUnityUp(), Color.cyan, axisLength * 0.8f);
    }

    private void RunAllCases(OrientationFixtureRoot fixture)
    {
        int failures = 0;
        foreach (OrientationFixtureCase orientationCase in fixture.cases)
        {
            if (!VerifyCase(orientationCase))
            {
                failures += 1;
            }
        }

        if (failures == 0)
        {
            Debug.Log($"FastDIS Unity orientation verification passed {fixture.cases.Count} cases");
        }
        else
        {
            Debug.LogError($"FastDIS Unity orientation verification failed {failures} case checks");
        }
    }

    private bool VerifyCase(OrientationFixtureCase orientationCase)
    {
        GameObject probe = new GameObject($"FastDisProbe_{orientationCase.name}");
        try
        {
            ApplyCaseToTransform(orientationCase, probe.transform);

            bool forwardOk = AssertAxis(orientationCase.name, "forward", probe.transform.forward, orientationCase.expected.AsUnityForward());
            bool rightOk = AssertAxis(orientationCase.name, "right", probe.transform.right, orientationCase.expected.AsUnityRight());
            bool upOk = AssertAxis(orientationCase.name, "up", probe.transform.up, orientationCase.expected.AsUnityUp());
            return forwardOk && rightOk && upOk;
        }
        finally
        {
            Destroy(probe);
        }
    }

    private void ApplyCaseToTransform(OrientationFixtureCase orientationCase, Transform targetTransform)
    {
        Vector3 forward = orientationCase.expected.AsUnityForward();
        Vector3 up = orientationCase.expected.AsUnityUp();
        targetTransform.SetPositionAndRotation(Vector3.zero, Quaternion.LookRotation(forward, up));
    }

    private bool AssertAxis(string caseName, string axisName, Vector3 actual, Vector3 expected)
    {
        float angle = AngleBetweenDegrees(actual, expected);
        if (angle > maxAxisAngleDegrees)
        {
            Debug.LogError($"{caseName} {axisName} angle {angle:F8} > {maxAxisAngleDegrees:F8}");
            return false;
        }

        Debug.Log($"PASS {caseName} {axisName} angle {angle:F8}");
        return true;
    }

    private static void DrawAxis(Vector3 origin, Vector3 direction, Color color, float length)
    {
        Gizmos.color = color;
        Gizmos.DrawLine(origin, origin + direction.normalized * length);
        Gizmos.DrawSphere(origin + direction.normalized * length, length * 0.04f);
    }

    private static float AngleBetweenDegrees(Vector3 actual, Vector3 expected)
    {
        float dot = Mathf.Clamp(Vector3.Dot(actual.normalized, expected.normalized), -1.0f, 1.0f);
        return Mathf.Rad2Deg * Mathf.Acos(dot);
    }

    private static OrientationFixtureRoot LoadFixture()
    {
        string path = Path.Combine(Application.streamingAssetsPath, "orientation_engine_cases.json");
        if (!File.Exists(path))
        {
            return null;
        }

        string json = File.ReadAllText(path);
        return JsonConvert.DeserializeObject<OrientationFixtureRoot>(json);
    }

    [Serializable]
    private sealed class OrientationFixtureRoot
    {
        public string schema;
        public List<OrientationFixtureCase> cases;

        public OrientationFixtureCase FindCase(string caseName)
        {
            return cases?.Find(item => string.Equals(item.name, caseName, StringComparison.Ordinal));
        }
    }

    [Serializable]
    private sealed class OrientationFixtureCase
    {
        public string name;
        public OrientationFixtureExpected expected;
    }

    [Serializable]
    private sealed class OrientationFixtureExpected
    {
        [JsonProperty("unity_forward")]
        public float[] unityForward;

        [JsonProperty("unity_right")]
        public float[] unityRight;

        [JsonProperty("unity_up")]
        public float[] unityUp;

        public Vector3 AsUnityForward()
        {
            return ToVector3(unityForward);
        }

        public Vector3 AsUnityRight()
        {
            return ToVector3(unityRight);
        }

        public Vector3 AsUnityUp()
        {
            return ToVector3(unityUp);
        }

        private static Vector3 ToVector3(float[] values)
        {
            if (values == null || values.Length != 3)
            {
                return Vector3.zero;
            }

            return new Vector3(values[0], values[1], values[2]);
        }
    }
}
