using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Serializers
{
    public class ByteEnumSerializer<T> : FieldSerializer<T>
    {
        protected override T _Read(BinaryReader br)
        {
            return (T)(object)br.ReadByte();
        }

        protected override void _Write(BinaryWriter bw, T t)
        {
            bw.Write((byte)(object)t);
        }
    }
}
