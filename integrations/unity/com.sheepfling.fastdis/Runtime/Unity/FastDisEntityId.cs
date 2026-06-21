using System;

namespace FastDIS.Unity
{
    [Serializable]
    public struct FastDisEntityId
    {
        public ushort Site;
        public ushort Application;
        public ushort Entity;

        public override string ToString()
        {
            return $"{Site}:{Application}:{Entity}";
        }
    }
}
