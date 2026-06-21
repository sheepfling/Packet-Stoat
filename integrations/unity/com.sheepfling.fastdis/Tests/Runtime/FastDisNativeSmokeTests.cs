using FastDIS.Scanning;
using NUnit.Framework;

namespace FastDIS.Tests
{
    public sealed class FastDisNativeSmokeTests
    {
        [Test]
        public void ScannerAcceptsMinimalHeaderSizedPacket()
        {
            FastDisScanner scanner = new FastDisScanner();
            byte[] packet = { 7, 1, 1, 1, 0, 0, 0, 1, 0, 12, 0, 0 };

            Assert.That(scanner.Scan(new[] { packet }).Count, Is.EqualTo(1));
        }
    }
}
