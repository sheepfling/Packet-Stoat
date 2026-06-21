using UnityEditor;
using UnityEngine;

namespace FastDIS.Unity.Editor
{
    public sealed class FastDisDiagnosticsWindow : EditorWindow
    {
        [MenuItem("Window/FastDIS/Diagnostics")]
        public static void Open()
        {
            GetWindow<FastDisDiagnosticsWindow>("FastDIS");
        }

        private void OnGUI()
        {
            EditorGUILayout.LabelField("FastDIS Unity", EditorStyles.boldLabel);

            bool loaded = FastDisNative.TryGetAbiVersion(out uint abiVersion);
            EditorGUILayout.LabelField("Native library", loaded ? "found" : "not found");
            EditorGUILayout.LabelField("ABI version", loaded ? abiVersion.ToString() : "unavailable");
        }
    }
}
