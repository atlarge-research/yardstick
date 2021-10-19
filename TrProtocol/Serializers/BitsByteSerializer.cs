using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(BitsByteSerializer))]
    public partial struct BitsByte
    {
        private class BitsByteSerializer : FieldSerializer<BitsByte>
        {
            protected override BitsByte _Read(BinaryReader br)
            {
                return br.ReadByte();
            }

            protected override void _Write(BinaryWriter bw, BitsByte t)
            {
                bw.Write(t);
            }
        }
    }
}
