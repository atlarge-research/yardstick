using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Serializers
{
    public class ByteEnumSerializer<T> : Serializer<T>
    {
        protected override T _Read(BinaryReader br)
        {
            return (T)Convert.ChangeType(br.ReadByte(), typeof(T));
        }

        protected override void _Write(BinaryWriter bw, T t)
        {
            bw.Write((byte)Convert.ChangeType(t, typeof(byte)));
        }
    }
}
