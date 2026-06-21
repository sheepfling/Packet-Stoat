using FastDIS.Native;

namespace FastDIS.Editor
{
    public static class FastDisPackageDoctor
    {
        public static string CheckNativeLibrary()
        {
            return FastDisNative.TryGetAbiVersion(out uint version)
                ? $"FastDIS native ABI available: {version}"
                : "FastDIS native ABI not available. Stage the platform library under Runtime/Plugins.";
        }
    }
}
