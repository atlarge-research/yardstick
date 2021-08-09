using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(ShortPositionSerializer))]
    public partial struct ShortPosition
    {
        private class ShortPositionSerializer : Serializer<ShortPosition>
        {
            protected override ShortPosition _Read(BinaryReader br)
            {
                return new ShortPosition
                {
                    X = br.ReadInt16(),
                    Y = br.ReadInt16()
                };
            }

            protected override void _Write(BinaryWriter bw, ShortPosition t)
            {
                bw.Write(t.X);
                bw.Write(t.Y);
            }
        }
    }
}
