using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(Vector2Serailizer))]
    public partial struct Vector2
    {
        public class Vector2Serailizer : Serializer<Vector2>
        {
            protected override Vector2 _Read(BinaryReader bb)
            {
                return new Vector2(bb.ReadSingle(), bb.ReadSingle());
            }

            protected override void _Write(BinaryWriter bb, Vector2 v)
            {
                bb.Write(v.X);
                bb.Write(v.Y);
            }
        }
    }
}
