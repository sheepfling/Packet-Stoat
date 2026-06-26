using System;
using System.Collections.Generic;
using UnityEngine;

namespace FastDIS.Unity
{
    public sealed class FastDisReplayPlayer : MonoBehaviour
    {
        [SerializeField]
        private TextAsset replayBytes;

        [SerializeField]
        private bool loop;

        [SerializeField]
        private FastDisWorld world;

        [SerializeField]
        private bool autoPlay = true;

        [SerializeField]
        private int packetsPerTick = 8;

        private readonly List<byte[]> packets = new List<byte[]>();
        private int nextPacketIndex;
        private bool playing;

        public TextAsset ReplayBytes => replayBytes;
        public bool Loop => loop;
        public int PacketCount => packets.Count;
        public int NextPacketIndex => nextPacketIndex;
        public bool IsPlaying => playing;

        private void OnEnable()
        {
            if (replayBytes != null)
            {
                LoadReplay(replayBytes.bytes);
            }
            if (autoPlay)
            {
                Play();
            }
        }

        private void Update()
        {
            Step();
        }

        public void LoadReplay(byte[] bytes)
        {
            packets.Clear();
            nextPacketIndex = 0;
            if (bytes == null)
            {
                return;
            }

            foreach (byte[] packet in ParseReplay(bytes))
            {
                packets.Add(packet);
            }
        }

        public void Play()
        {
            playing = packets.Count > 0;
        }

        public void Stop()
        {
            playing = false;
        }

        public int Step()
        {
            if (world == null)
            {
                world = GetComponent<FastDisWorld>();
            }
            if (!playing || world == null || packets.Count == 0)
            {
                return 0;
            }

            int sent = 0;
            int budget = Math.Max(1, packetsPerTick);
            while (sent < budget && packets.Count > 0)
            {
                if (nextPacketIndex >= packets.Count)
                {
                    if (!loop)
                    {
                        playing = false;
                        break;
                    }
                    nextPacketIndex = 0;
                }

                if (world.ProcessPacket(packets[nextPacketIndex]))
                {
                    sent++;
                }
                nextPacketIndex++;
            }
            return sent;
        }

        public static IReadOnlyList<byte[]> ParseReplay(byte[] bytes)
        {
            List<byte[]> packets = new List<byte[]>();
            if (bytes == null)
            {
                return packets;
            }

            int offset = 0;
            if (bytes.Length >= 8 &&
                bytes[0] == (byte)'F' &&
                bytes[1] == (byte)'D' &&
                bytes[2] == (byte)'P' &&
                bytes[3] == (byte)'K' &&
                bytes[4] == (byte)'T' &&
                bytes[5] == (byte)'1')
            {
                offset = 6;
                if (offset + 2 > bytes.Length)
                {
                    return packets;
                }

                int packetCount = (bytes[offset] << 8) | bytes[offset + 1];
                offset += 2;
                for (int i = 0; i < packetCount && offset + 4 <= bytes.Length; i++)
                {
                    int length = (bytes[offset] << 24)
                        | (bytes[offset + 1] << 16)
                        | (bytes[offset + 2] << 8)
                        | bytes[offset + 3];
                    offset += 4;
                    if (length <= 0 || offset + length > bytes.Length)
                    {
                        break;
                    }

                    byte[] packet = new byte[length];
                    Buffer.BlockCopy(bytes, offset, packet, 0, length);
                    packets.Add(packet);
                    offset += length;
                }
                return packets;
            }

            while (offset + 4 <= bytes.Length)
            {
                int length = (bytes[offset] << 24)
                    | (bytes[offset + 1] << 16)
                    | (bytes[offset + 2] << 8)
                    | bytes[offset + 3];
                offset += 4;
                if (length <= 0 || offset + length > bytes.Length)
                {
                    break;
                }
                byte[] packet = new byte[length];
                Buffer.BlockCopy(bytes, offset, packet, 0, length);
                packets.Add(packet);
                offset += length;
            }
            return packets;
        }
    }
}
