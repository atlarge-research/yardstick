using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(UShortPositionSerializer))]
    public partial struct UShortPosition
    {
        private class UShortPositionSerializer : FieldSerializer<UShortPosition>
        {
            protected override UShortPosition _Read(BinaryReader br)
            {
                return new UShortPosition
                {
                    X = br.ReadUInt16(),
                    Y = br.ReadUInt16()
                };
            }

            protected override void _Write(BinaryWriter bw, UShortPosition t)
            {
                bw.Write(t.X);
                bw.Write(t.Y);
            }
        }
    }
}
