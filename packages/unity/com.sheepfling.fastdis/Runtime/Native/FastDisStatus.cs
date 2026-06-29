namespace FastDIS.Native
{
    public enum FastDisStatus
    {
        Ok = 0,
        BadArgument = 1,
        ShortPacket = 2,
        LengthExceedsBuffer = 3,
        LengthTooSmall = 4,
        Unsupported = 5
    }
}
