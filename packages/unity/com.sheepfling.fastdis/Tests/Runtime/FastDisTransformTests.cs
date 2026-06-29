using FastDIS.Unity;
using NUnit.Framework;
using UnityEngine;

namespace FastDIS.Tests
{
    public sealed class FastDisTransformTests
    {
        [Test]
        public void EnuMapsToUnityEastUpNorth()
        {
            Vector3 unity = FastDisTransformMapper.EnuToUnity(new Vector3(1, 2, 3));

            Assert.That(unity.x, Is.EqualTo(1));
            Assert.That(unity.y, Is.EqualTo(3));
            Assert.That(unity.z, Is.EqualTo(2));
        }
    }
}
