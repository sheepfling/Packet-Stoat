using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace FastDIS.Native
{
    public static class FastDisNative
    {
        private const string LibraryName = "fastdis";
        public const uint AbiVersion = 9;
        public const uint FastDisFlagAllowTruncated = 0x00000001u;
        public const ulong FastDisEsFieldForceId = 0x0000000000000004UL;
        public const ulong FastDisEsFieldLocation = 0x0000000000000080UL;
        public const ulong FastDisEsFieldLinearVelocity = 0x0000000000000040UL;
        public const int FastDisOk = 0;

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        internal static extern uint fastdis_abi_version();

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr fastdis_version_string();

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_entity_transform(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisEntityTransform outTransform);

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

        public static bool TryParseEntityTransform(
            byte[] packet,
            out FastDisEntityTransform transform,
            uint flags = 0,
            bool allowTruncated = false)
        {
            transform = default;
            if (packet == null || packet.Length == 0)
            {
                return false;
            }

            GCHandle handle = default;
            try
            {
                handle = GCHandle.Alloc(packet, GCHandleType.Pinned);
                uint combinedFlags = flags | (allowTruncated ? FastDisFlagAllowTruncated : 0u);
                int rc = fastdis_parse_entity_transform(
                    handle.AddrOfPinnedObject(),
                    (UIntPtr)(uint)packet.Length,
                    combinedFlags,
                    out transform);
                return rc == FastDisOk;
            }
            catch (DllNotFoundException)
            {
                transform = default;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                transform = default;
                return false;
            }
            finally
            {
                if (handle.IsAllocated)
                {
                    handle.Free();
                }
            }
        }
    }
}
