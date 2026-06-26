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

            FastDIS.Unity.FastDisWorld world = FindFirstObjectByType<FastDIS.Unity.FastDisWorld>();
            if (world == null)
            {
                EditorGUILayout.HelpBox("No active FastDisWorld found in the open scene.", MessageType.None);
                return;
            }

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Runtime", EditorStyles.boldLabel);
            EditorGUILayout.LabelField("Last PDU", world.LastPdu);
            EditorGUILayout.LabelField("Known Entities", world.KnownEntityCount.ToString());
            EditorGUILayout.LabelField("Bound Actors", world.BoundActorCount.ToString());
            EditorGUILayout.LabelField("Packets Processed", world.PacketsProcessed.ToString());
            EditorGUILayout.LabelField("Entities Spawned", world.EntitiesSpawned.ToString());
            EditorGUILayout.LabelField("Remove Requests", world.RemoveRequests.ToString());
            EditorGUILayout.LabelField("Malformed Packets", world.MalformedPackets.ToString());
        }
    }
}
