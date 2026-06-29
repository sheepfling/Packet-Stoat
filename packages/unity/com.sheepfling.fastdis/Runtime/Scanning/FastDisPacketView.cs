namespace FastDIS.Scanning
{
    public readonly struct FastDisHeaderView
    {
        public FastDisHeaderView(byte version, byte exerciseId, byte pduType, byte protocolFamily, ushort length)
        {
            Version = version;
            ExerciseId = exerciseId;
            PduType = pduType;
            ProtocolFamily = protocolFamily;
            Length = length;
        }

        public byte Version { get; }
        public byte ExerciseId { get; }
        public byte PduType { get; }
        public byte ProtocolFamily { get; }
        public ushort Length { get; }

        public static bool TryParse(byte[] packet, out FastDisHeaderView header)
        {
            if (packet == null || packet.Length < 12)
            {
                header = default;
                return false;
            }

            ushort length = (ushort)((packet[8] << 8) | packet[9]);
            header = new FastDisHeaderView(packet[0], packet[1], packet[2], packet[3], length);
            return length >= 12 && length <= packet.Length;
        }
    }
}
