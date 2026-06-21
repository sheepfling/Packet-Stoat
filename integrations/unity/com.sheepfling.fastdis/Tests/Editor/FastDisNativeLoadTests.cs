using FastDIS.Native;
using NUnit.Framework;

namespace FastDIS.Editor.Tests
{
    public sealed class FastDisNativeLoadTests
    {
        [Test]
        public void FastDisNativeLibraryLoadsAndReportsAbiVersion()
        {
            bool loaded = FastDisNative.TryGetAbiVersion(out uint abiVersion);

            Assert.That(loaded, Is.True, "FastDIS native library failed to load from Unity native plug-in paths.");
            Assert.That(abiVersion, Is.GreaterThan(0u));
        }
    }
}
