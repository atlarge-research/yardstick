using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(ColorSerailizer))]
    public partial struct Color
    {
        public class ColorSerailizer : FieldSerializer<Color>
        {
            protected override Color _Read(BinaryReader bb)
            {
                return new Color(bb.ReadByte(), bb.ReadByte(), bb.ReadByte());
            }

            protected override void _Write(BinaryWriter bb, Color c)
            {
                bb.Write((byte)c.R);
                bb.Write((byte)c.G);
                bb.Write((byte)c.B);
            }
        }
    }
}
