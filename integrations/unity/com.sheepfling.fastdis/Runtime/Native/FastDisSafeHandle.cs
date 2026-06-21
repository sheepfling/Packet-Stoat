using System;
using Microsoft.Win32.SafeHandles;

namespace FastDIS.Native
{
    public sealed class FastDisSafeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public FastDisSafeHandle() : base(true)
        {
        }

        protected override bool ReleaseHandle()
        {
            // Placeholder until Unity runtime owns native scanner/table handles.
            return true;
        }
    }
}
