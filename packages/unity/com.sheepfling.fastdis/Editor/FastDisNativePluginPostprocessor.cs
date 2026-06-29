using UnityEditor;

namespace FastDIS.Editor
{
    public sealed class FastDisNativePluginPostprocessor : AssetPostprocessor
    {
        private void OnPreprocessAsset()
        {
            // Unity import settings for staged native plug-ins will live here
            // once release artifacts include platform binaries.
        }
    }
}
