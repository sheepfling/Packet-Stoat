using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisNetworkReceiver : MonoBehaviour
    {
        [SerializeField]
        private string bindAddress = "0.0.0.0";

        [SerializeField]
        private ushort port = 3001;

        public string BindAddress => bindAddress;
        public ushort Port => port;
    }
}
