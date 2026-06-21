using UnityEditor;
using UnityEngine;

namespace FastDIS.Editor
{
    public sealed class FastDisMonitorWindow : EditorWindow
    {
        [MenuItem("Window/FastDIS/Monitor")]
        public static void Open()
        {
            GetWindow<FastDisMonitorWindow>("FastDIS");
        }

        private void OnGUI()
        {
            EditorGUILayout.LabelField("FastDIS for Unity", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(FastDisPackageDoctor.CheckNativeLibrary(), MessageType.Info);
        }
    }
}
