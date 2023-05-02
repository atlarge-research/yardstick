namespace TrProtocol.Models;


[Serializer(typeof(ColorSerailizer))]
public partial struct Color
{
    private class ColorSerailizer : FieldSerializer<Color>
    {
        protected override Color ReadOverride(BinaryReader br)
        {
            return new Color(br.ReadByte(), br.ReadByte(), br.ReadByte());
        }

        protected override void WriteOverride(BinaryWriter bw, Color t)
        {
            bw.Write((byte)t.R);
            bw.Write((byte)t.G);
            bw.Write((byte)t.B);
        }
    }
}