using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(ColorSerailizer))]
    public partial struct Color
    {
        public class ColorSerailizer : Serializer<Color>
        {
            protected override Color _Read(BinaryReader bb)
            {
                return new Color((int)bb.ReadByte(), (int)bb.ReadByte(), (int)bb.ReadByte());
            }

            protected override void _Write(BinaryWriter bb, Color c)
            {
                bb.Write(c.R);
                bb.Write(c.G);
                bb.Write(c.B);
            }
        }
    }
}
