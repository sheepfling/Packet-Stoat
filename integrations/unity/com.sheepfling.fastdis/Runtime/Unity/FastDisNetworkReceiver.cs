using System;
using System.Net;
using System.Net.Sockets;
using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisNetworkReceiver : MonoBehaviour
    {
        [SerializeField]
        private string bindAddress = "0.0.0.0";

        [SerializeField]
        private ushort port = 3001;

        [SerializeField]
        private bool multicastEnabled;

        [SerializeField]
        private string multicastAddress = "239.255.42.99";

        [SerializeField]
        private string multicastInterfaceAddress = "127.0.0.1";

        [SerializeField]
        private bool multicastLoopback = true;

        [SerializeField]
        private FastDisWorld world;

        [SerializeField]
        private bool autoStart = true;

        [SerializeField]
        private int maxPacketsPerTick = 32;

        private UdpClient client;
        private IPEndPoint remote;
        private ulong packetsReceived;

        public string BindAddress => bindAddress;
        public ushort Port => port;
        public bool MulticastEnabled => multicastEnabled;
        public string MulticastAddress => multicastAddress;
        public string MulticastInterfaceAddress => multicastInterfaceAddress;
        public bool MulticastLoopback => multicastLoopback;
        public bool IsRunning => client != null;
        public ulong PacketsReceived => packetsReceived;

        public void ConfigureEndpoint(string address, ushort listenPort)
        {
            if (client != null)
            {
                throw new InvalidOperationException("Cannot change the receiver endpoint while it is running.");
            }

            bindAddress = string.IsNullOrWhiteSpace(address) ? "0.0.0.0" : address;
            port = listenPort;
            multicastEnabled = false;
        }

        public void ConfigureMulticast(string groupAddress, ushort listenPort, string interfaceAddress = "127.0.0.1", bool loopback = true)
        {
            if (client != null)
            {
                throw new InvalidOperationException("Cannot change the receiver endpoint while it is running.");
            }

            bindAddress = "0.0.0.0";
            port = listenPort;
            multicastEnabled = true;
            multicastAddress = string.IsNullOrWhiteSpace(groupAddress) ? "239.255.42.99" : groupAddress;
            multicastInterfaceAddress = string.IsNullOrWhiteSpace(interfaceAddress) ? "127.0.0.1" : interfaceAddress;
            multicastLoopback = loopback;
        }

        private void OnEnable()
        {
            if (autoStart)
            {
                StartReceiver();
            }
        }

        private void Update()
        {
            PumpAvailable();
        }

        private void OnDisable()
        {
            StopReceiver();
        }

        public void StartReceiver()
        {
            if (client != null)
            {
                return;
            }

            IPAddress address = string.IsNullOrWhiteSpace(bindAddress) || bindAddress == "0.0.0.0"
                ? IPAddress.Any
                : IPAddress.Parse(bindAddress);
            remote = new IPEndPoint(IPAddress.Any, 0);
            if (multicastEnabled)
            {
                client = new UdpClient(AddressFamily.InterNetwork);
                client.ExclusiveAddressUse = false;
                client.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
                client.Client.Bind(new IPEndPoint(address, port));
                client.MulticastLoopback = multicastLoopback;

                IPAddress group = IPAddress.Parse(multicastAddress);
                IPAddress iface = IPAddress.Parse(multicastInterfaceAddress);
                client.JoinMulticastGroup(group, iface);
            }
            else
            {
                client = new UdpClient(new IPEndPoint(address, port));
            }
            client.Client.Blocking = false;
        }

        public void StopReceiver()
        {
            if (client == null)
            {
                return;
            }

            try
            {
                if (multicastEnabled)
                {
                    try
                    {
                        client.DropMulticastGroup(IPAddress.Parse(multicastAddress));
                    }
                    catch (SocketException)
                    {
                    }
                    catch (ObjectDisposedException)
                    {
                    }
                }
                client.Close();
            }
            finally
            {
                client = null;
                remote = null;
            }
        }

        public int PumpAvailable()
        {
            if (world == null)
            {
                world = GetComponent<FastDisWorld>();
            }
            if (client == null || world == null)
            {
                return 0;
            }

            int processed = 0;
            while (processed < Math.Max(1, maxPacketsPerTick) && client.Available > 0)
            {
                byte[] packet = client.Receive(ref remote);
                if (world.ProcessPacket(packet))
                {
                    packetsReceived++;
                    processed++;
                }
            }
            return processed;
        }

        public bool InjectPacket(byte[] packet)
        {
            if (world == null)
            {
                world = GetComponent<FastDisWorld>();
            }
            if (world == null)
            {
                return false;
            }

            bool ok = world.ProcessPacket(packet);
            if (ok)
            {
                packetsReceived++;
            }
            return ok;
        }
    }
}
