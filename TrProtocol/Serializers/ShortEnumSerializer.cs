using System;
using System.IO;

namespace TrProtocol.Serializers
{
    public class ShortEnumSerializer<T> : FieldSerializer<T> where T : Enum
    {
        protected override T _Read(BinaryReader br)
        {
            return (T)(object)br.ReadInt16();
        }

        protected override void _Write(BinaryWriter bw, T t)
        {
            bw.Write((short)(object)t);
        }
    }
}
