using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(PositionSerializer))]
    public partial struct Position
    {
        private class PositionSerializer : Serializer<Position>
        {
            protected override Position _Read(BinaryReader br)
            {
                return new Position
                {
                    X = br.ReadInt32(),
                    Y = br.ReadInt32()
                };
            }

            protected override void _Write(BinaryWriter bw, Position t)
            {
                bw.Write(t.X);
                bw.Write(t.Y);
            }
        }
    }
}
