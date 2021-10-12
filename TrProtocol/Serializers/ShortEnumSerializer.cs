using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol.Packets;

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
