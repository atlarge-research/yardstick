using System.IO;

namespace TrProtocol.Models;

[Serializer(typeof(PositionSerializer))]
public partial struct Position
{
    private class PositionSerializer : FieldSerializer<Position>
    {
        protected override Position ReadOverride(BinaryReader br)
        {
            return new Position
            {
                X = br.ReadInt32(),
                Y = br.ReadInt32()
            };
        }

        protected override void WriteOverride(BinaryWriter bw, Position t)
        {
            bw.Write(t.X);
            bw.Write(t.Y);
        }
    }
}
