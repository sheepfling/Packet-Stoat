using UnityEditor;

namespace FastDIS.Editor
{
    public static class FastDisSettingsProvider
    {
        [SettingsProvider]
        public static SettingsProvider CreateProvider()
        {
            return new SettingsProvider("Project/FastDIS", SettingsScope.Project)
            {
                label = "FastDIS",
                guiHandler = _ => EditorGUILayout.LabelField(FastDisPackageDoctor.CheckNativeLibrary())
            };
        }
    }
}
