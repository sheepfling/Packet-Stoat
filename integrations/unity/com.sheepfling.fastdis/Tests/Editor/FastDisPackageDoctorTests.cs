using FastDIS.Editor;
using NUnit.Framework;

namespace FastDIS.Editor.Tests
{
    public sealed class FastDisPackageDoctorTests
    {
        [Test]
        public void DoctorReturnsActionableMessage()
        {
            string message = FastDisPackageDoctor.CheckNativeLibrary();

            Assert.That(message, Does.Contain("FastDIS native ABI"));
        }
    }
}
