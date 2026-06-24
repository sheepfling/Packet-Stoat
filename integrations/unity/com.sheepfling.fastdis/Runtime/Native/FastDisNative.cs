using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace FastDIS.Native
{
    public static class FastDisNative
    {
        private const string LibraryName = "fastdis";
        public const uint AbiVersion = 11;
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

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_fire(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisFire outFire);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_detonation(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisDetonation outDetonation);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_create_entity(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisSimulationManagementRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_remove_entity(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisSimulationManagementRequest outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_start_resume(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisStartResume outRequest);

        [DllImport(LibraryName, CallingConvention = CallingConvention.Cdecl)]
        private static extern int fastdis_parse_stop_freeze(
            IntPtr data,
            UIntPtr size,
            uint flags,
            out FastDisStopFreeze outRequest);

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

        public static bool TryParseCreateEntity(
            byte[] packet,
            out FastDisSimulationManagementRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_create_entity, out request);
        }

        public static bool TryParseRemoveEntity(
            byte[] packet,
            out FastDisSimulationManagementRequest request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_remove_entity, out request);
        }

        public static bool TryParseStartResume(
            byte[] packet,
            out FastDisStartResume request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_start_resume, out request);
        }

        public static bool TryParseStopFreeze(
            byte[] packet,
            out FastDisStopFreeze request,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_stop_freeze, out request);
        }

        public static bool TryParseFire(
            byte[] packet,
            out FastDisFire fire,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_fire, out fire);
        }

        public static bool TryParseDetonation(
            byte[] packet,
            out FastDisDetonation detonation,
            uint flags = 0,
            bool allowTruncated = false)
        {
            return TryParse(packet, flags, allowTruncated, fastdis_parse_detonation, out detonation);
        }

        private delegate int ParseDelegate<T>(IntPtr data, UIntPtr size, uint flags, out T parsed);

        private static bool TryParse<T>(
            byte[] packet,
            uint flags,
            bool allowTruncated,
            ParseDelegate<T> parser,
            out T parsed)
        {
            parsed = default;
            if (packet == null || packet.Length == 0)
            {
                return false;
            }

            GCHandle handle = default;
            try
            {
                handle = GCHandle.Alloc(packet, GCHandleType.Pinned);
                uint combinedFlags = flags | (allowTruncated ? FastDisFlagAllowTruncated : 0u);
                int rc = parser(
                    handle.AddrOfPinnedObject(),
                    (UIntPtr)(uint)packet.Length,
                    combinedFlags,
                    out parsed);
                return rc == FastDisOk;
            }
            catch (DllNotFoundException)
            {
                parsed = default;
                return false;
            }
            catch (EntryPointNotFoundException)
            {
                parsed = default;
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
