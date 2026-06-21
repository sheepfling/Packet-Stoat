using System;
using System.Runtime.InteropServices;

namespace FastDIS.Unity
{
    public static class FastDisNative
    {
        private const string LibraryName = "fastdis";

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        internal static extern uint fastdis_abi_version();

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr fastdis_version_string();

        public static bool TryGetAbiVersion(out uint abiVersion)
        {
            try
            {
                abiVersion = fastdis_abi_version();
                return true;
            }
            catch (DllNotFoundException)
            {
                abiVersion = 0;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                abiVersion = 0;
                return false;
            }
        }
    }
}
