using System;

namespace FastDIS.Unity
{
    [Serializable]
    public struct FastDisEntityId
    {
        public ushort site;
        public ushort application;
        public ushort entity;

        public override string ToString()
        {
            return $"{site}:{application}:{entity}";
        }
    }
}
